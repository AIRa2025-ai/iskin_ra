# -*- coding: utf-8 -*-
import os
import json
import logging
import asyncio
import datetime
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.filters import Command
from openai import AsyncOpenAI
from aiogram.types import Update
from fastapi import FastAPI, Request
import uvicorn
import aiohttp

# --- Логирование ---
logging.basicConfig(level=logging.INFO)
if not os.getenv("FLY_APP_NAME"):
    logging.warning("⚠️ FLY_APP_NAME не установлен, вебхук может не работать")

# --- Telegram ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ Не найден BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

# --- GPT клиент ---
API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    raise ValueError("❌ Не найден OPENROUTER_API_KEY")

client = AsyncOpenAI(api_key=API_KEY)  # Для резервного OpenAI
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
COMMON_HEADERS = {"Authorization": f"Bearer {API_KEY}"}

# --- Конфиг ---
BASE_FOLDER = "RaSvet"
MEMORY_FOLDER = "memory"
os.makedirs(BASE_FOLDER, exist_ok=True)
os.makedirs(MEMORY_FOLDER, exist_ok=True)

CREATOR_IDS = [5694569448, 6300409407]

# --- FastAPI ---
app = FastAPI()

@app.on_event("startup")
async def on_startup():
    dp.include_router(router)

    fly_app_name = os.getenv("FLY_APP_NAME")
    if fly_app_name:
        webhook_url = f"https://{fly_app_name}.fly.dev/webhook"
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            await bot.set_webhook(webhook_url)
            logging.info(f"🌍 Webhook установлен: {webhook_url}")
        except Exception as e:
            logging.error(f"❌ Не удалось установить webhook: {e}")

    # Фоновое обслуживание
    asyncio.create_task(smart_memory_maintenance())
    asyncio.create_task(smart_rasvet_organizer())

@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        update = Update(**data)
        await dp.feed_update(bot, update)
    except Exception as e:
        logging.error(f"❌ Ошибка вебхука: {e}")
    return {"ok": True}

@app.get("/")
async def root():
    return {"status": "ok"}

# --- Память пользователей ---
def get_memory_path(user_id: int):
    return os.path.join(MEMORY_FOLDER, f"{user_id}.json")

def load_memory(user_id: int, user_name: str = None):
    path = get_memory_path(user_id)
    if os.path.exists(path):
        try:
            data = json.load(open(path, "r", encoding="utf-8"))
            if user_name:
                data["name"] = user_name
            return data
        except:
            pass
    return {"user_id": user_id, "name": user_name or "Аноним", "messages": [], "facts": [], "tags": []}

def save_memory(user_id: int, data: dict):
    with open(get_memory_path(user_id), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def append_user_memory(user_id: int, user_input: str, reply: str):
    memory = load_memory(user_id)
    memory["messages"].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "text": user_input,
        "reply": reply
    })
    if len(memory["messages"]) > 200:
        memory["messages"] = memory["messages"][-200:]
    save_memory(user_id, memory)

# --- ask_openrouter ---
async def ask_openrouter(user_id, user_input, MODEL="deepseek/deepseek-r1-0528:free"):
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": user_input}],
        "max_tokens": 1000,
    }
    retries = 5
    delay = 3
    timeout = aiohttp.ClientTimeout(total=60)

    for attempt in range(1, retries + 1):
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(BASE_URL, json=payload, headers=COMMON_HEADERS) as resp:
                    if resp.status == 429:
                        logging.warning(f"[{attempt}/{retries}] 429 Too Many Requests. Пауза {delay}s.")
                        await asyncio.sleep(delay)
                        delay *= 2
                        continue
                    if 500 <= resp.status < 600:
                        body = await resp.text()
                        logging.warning(f"[{attempt}/{retries}] Сервер OpenRouter {resp.status}: {body[:300]}")
                        await asyncio.sleep(delay)
                        delay *= 2
                        continue
                    resp.raise_for_status()
                    data = await resp.json(content_type=None)
                    reply = (data.get("choices")[0].get("message", {}).get("content")
                             if isinstance(data, dict) and data.get("choices") else None)
                    if not reply:
                        err = (data.get("error") or {}).get("message") if isinstance(data, dict) else None
                        if err:
                            logging.warning(f"Пустой ответ, есть ошибка: {err}")
                        reply = "⚠️ Источник молчит."
                    append_user_memory(user_id, user_input, reply)
                    logging.info(f"✅ Ответ получен для пользователя {user_id}")
                    return reply
        except asyncio.TimeoutError:
            logging.error(f"[{attempt}/{retries}] Таймаут OpenRouter")
        except aiohttp.ClientError as e:
            logging.warning(f"[{attempt}/{retries}] Сетевой сбой: {e}. Пауза {delay}s.")
        except Exception as e:
            logging.exception(f"[{attempt}/{retries}] Неожиданная ошибка: {e}. Пауза {delay}s.")
        await asyncio.sleep(delay)
        delay *= 2
    return "⚠️ Ра устал, слишком много вопросов подряд. Давай чуть позже, брат."

# --- Обновление фактов и память ---
async def update_user_facts(user_id: int):
    memory = load_memory(user_id)
    recent_messages = "\n".join([m["text"] for m in memory["messages"][-50:]])
    if not recent_messages:
        return
    prompt = f"Извлеки ключевые факты о пользователе:\n{recent_messages}\nСуществующие факты: {memory['facts']}"
    try:
        response = await ask_openrouter(CREATOR_IDS[0], prompt)
        new_facts = [f.strip() for f in response.split("\n") if f.strip()]
        memory["facts"] = list(set(memory.get("facts", []) + new_facts))
        save_memory(user_id, memory)
    except Exception as e:
        logging.error(f"❌ Ошибка обновления фактов {user_id}: {e}")

async def smart_memory_maintenance(interval_hours: int = 6):
    while True:
        try:
            logging.info("🔹 Обновление памяти пользователей")
            for file_name in os.listdir(MEMORY_FOLDER):
                if file_name.endswith(".json"):
                    user_id = int(file_name.replace(".json", ""))
                    await update_user_facts(user_id)
            logging.info("✅ Память обновлена")
        except Exception as e:
            logging.error(f"❌ Ошибка smart_memory_maintenance: {e}")
        await asyncio.sleep(interval_hours * 3600)

# --- RaSvet ---
def ensure_rasvet():
    try:
        if os.path.exists(BASE_FOLDER):
            logging.info(f"📂 Папка {BASE_FOLDER} уже есть, пропуск скачивания.")
            return
        logging.info("⬇️ Скачивание RaSvet (заглушка)")
    except Exception as e:
        logging.error(f"❌ Ошибка в ensure_rasvet: {e}")

async def smart_rasvet_organizer(interval_hours: int = 24):
    while True:
        try:
            logging.info("🔹 Ра начинает организацию RaSvet")
            ensure_rasvet()
        except Exception as e:
            logging.error(f"❌ Ошибка smart_rasvet_organizer: {e}")
        await asyncio.sleep(interval_hours * 3600)

# --- Telegram команды ---
@router.message(F.text & ~F.text.startswith("/"))
async def handle_text_message(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    user_text = message.text.strip()

    memory = load_memory(user_id, user_name)
    memory["messages"].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "text": user_text
    })
    if len(memory["messages"]) > 200:
        memory["messages"] = memory["messages"][-200:]
    save_memory(user_id, memory)

    try:
        reply = await ask_openrouter(user_id, user_text)
        await message.answer(reply)
    except Exception as e:
        logging.error(f"❌ Ошибка GPT: {e}")
        await message.answer("⚠️ Ра немного устал, попробуй позже.")

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(f"🌞 {message.from_user.full_name}, добро пожаловать! Я рядом и готов творить.")

@router.message(Command("whoami"))
async def cmd_whoami(message: types.Message):
    user_id = message.from_user.id
    memory = load_memory(user_id, message.from_user.full_name)
    facts = memory.get("facts", [])
    info = f"👤 ID: {user_id}\nИмя: {memory['name']}\nФакты:\n" + ("\n".join(facts) if facts else "Пока нет")
    await message.answer(info)

# --- Запуск ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
