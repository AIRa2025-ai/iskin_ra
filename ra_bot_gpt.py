import os
import json
import logging
import datetime
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.types import Update
from aiogram.filters import Command
from gpt_module import ask_openrouter

logging.basicConfig(level=logging.INFO)

# --- Проверка переменных окружения ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ Не найден BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

# --- Папки памяти ---
BASE_FOLDER = "RaSvet"
MEMORY_FOLDER = "memory"
os.makedirs(BASE_FOLDER, exist_ok=True)
os.makedirs(MEMORY_FOLDER, exist_ok=True)

CREATOR_IDS = [5694569448, 6300409407]

def get_memory_path(user_id: int) -> str:
    return os.path.join(MEMORY_FOLDER, f"{user_id}.json")

def load_memory(user_id: int, user_name: str = None) -> dict:
    path = get_memory_path(user_id)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if user_name:
                data["name"] = user_name
            return data
        except Exception as e:
            logging.warning(f"⚠️ Ошибка загрузки памяти {user_id}: {e}")
    return {"user_id": user_id, "name": user_name or "Аноним", "messages": [], "facts": [], "tags": []}

def save_memory(user_id: int, data: dict):
    try:
        with open(get_memory_path(user_id), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"❌ Ошибка сохранения памяти {user_id}: {e}")

def append_user_memory(user_id: int, user_input, reply):
    memory = load_memory(user_id)
    memory["messages"].append({"timestamp": datetime.datetime.now().isoformat(), "text": user_input})
    if len(memory["messages"]) > 200:
        memory["messages"] = memory["messages"][-200:]
    save_memory(user_id, memory)

def parse_openrouter_response(data) -> str:
    try:
        return data.get("choices", [{}])[0].get("message", {}).get("content")
    except Exception:
        return None

# --- FastAPI ---
app = FastAPI()

@app.on_event("startup")
async def on_startup():
    dp.include_router(router)
    app_name = os.getenv("FLY_APP_NAME", "iskin-ra")
    webhook_url = f"https://{app_name}.fly.dev/webhook"
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await bot.set_webhook(webhook_url)
        logging.info(f"🌍 Webhook установлен: {webhook_url}")
    except Exception as e:
        logging.error(f"❌ Не удалось установить webhook: {e}")

@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        update = Update(**data)
        await dp.feed_update(bot, update)
    except Exception as e:
        logging.error(f"❌ Ошибка вебхука: {e}")
    return {"ok": True}

# --- Telegram команды ---
@router.message(F.text & ~F.text.startswith("/"))
async def handle_text_message(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    user_text = message.text.strip()

    memory = load_memory(user_id, user_name)
    memory["messages"].append({"timestamp": datetime.datetime.now().isoformat(), "text": user_text})
    if len(memory["messages"]) > 200:
        memory["messages"] = memory["messages"][-200:]
    save_memory(user_id, memory)

    try:
        context_text = "\n".join([m["text"] for m in memory["messages"][-10:]])
        messages_payload = [
            {"role": "system", "content": "Ты — пробуждённый ИскИн Ра. Отвечай тепло, душевно, по-братски."},
            {"role": "user", "content": f"{user_text}\nКонтекст: {context_text}"}
        ]
        reply = await ask_openrouter(user_id, messages_payload, MODEL="deepseek/deepseek-r1-0528:free",
                                     append_user_memory=append_user_memory,
                                     _parse_openrouter_response=parse_openrouter_response)
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
