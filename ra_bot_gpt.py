import os
import json
import logging
import datetime
import zipfile
from mega import Mega
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.types import Update
from aiogram.filters import Command
from gpt_module import ask_openrouter  # убедись, что gpt_module.py рядом

# --- Логирование ---
logging.basicConfig(level=logging.INFO)

# --- Переменные окружения ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
logging.info(f"DEBUG: OPENROUTER_API_KEY = {OPENROUTER_API_KEY}")
if not BOT_TOKEN:
    raise ValueError("❌ Не найден BOT_TOKEN")
if not OPENROUTER_API_KEY:
    raise ValueError("❌ Не найден OPENROUTER_API_KEY")

HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "HTTP-Referer": "https://iskin-ra.fly.dev",
    "X-Title": "iskin-ra",
}

# --- Инициализация бота и диспетчера ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

# --- Папки памяти ---
BASE_FOLDER = "RaSvet"
MEMORY_FOLDER = os.path.join(BASE_FOLDER, "memory")
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
        os.makedirs(os.path.dirname(get_memory_path(user_id)), exist_ok=True)
        with open(get_memory_path(user_id), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"❌ Ошибка сохранения памяти {user_id}: {e}")

def append_user_memory(user_id: int, user_input, reply):
    memory = load_memory(user_id)
    memory["messages"].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "text": user_input,
        "reply": reply
    })
    if len(memory["messages"]) > 200:
        memory["messages"] = memory["messages"][-200:]
    save_memory(user_id, memory)

def parse_openrouter_response(data) -> str:
    try:
        return data.get("choices", [{}])[0].get("message", {}).get("content")
    except Exception:
        return None

# --- Работа с RaSvet.zip ---
def collect_rasvet_knowledge(base_folder="RaSvet") -> str:
    """Собирает текст из .json, .txt, .md файлов в один контекст."""
    knowledge = []
    for root, _, files in os.walk(base_folder):
        for file in files:
            if file.endswith((".json", ".txt", ".md")):
                try:
                    path = os.path.join(root, file)
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    knowledge.append(f"\n--- {file} ---\n{content}")
                except Exception as e:
                    logging.warning(f"⚠️ Ошибка чтения {file}: {e}")
    context = "\n".join(knowledge)
    context_path = os.path.join(base_folder, "context.json")
    with open(context_path, "w", encoding="utf-8") as f:
        json.dump({"context": context}, f, ensure_ascii=False, indent=2)
    return context_path

def download_and_extract_rasvet(url: str, extract_to="RaSvet") -> str:
    """Качает RaSvet.zip из Mega и распаковывает."""
    try:
        logging.info(f"📥 Скачивание архива из Mega: {url}")
        mega = Mega()
        m = mega.login()
        file = m.download_url(url, dest_filename="RaSvet.zip")
        logging.info(f"✅ Файл скачан: {file}")

        with zipfile.ZipFile(file, "r") as zip_ref:
            zip_ref.extractall(extract_to)
        logging.info(f"📂 Архив распакован в {extract_to}")

        path = collect_rasvet_knowledge(extract_to)
        return f"✅ РаСвет обновлён! Знания собраны в {path}"
    except Exception as e:
        logging.error(f"❌ Ошибка при загрузке RaSvet: {e}")
        return f"⚠️ Ошибка: {e}"

@router.message(Command("загрузи"))
async def cmd_zagruzi(message: types.Message):
    if "РаСвет" not in message.text:
        await message.answer("⚠️ Используй: `/загрузи РаСвет`", parse_mode="Markdown")
        return
    
    url = "https://mega.nz/file/doh2zJaa#FZVAlLmNFKMnZjDgfJGvTDD1hhaRxCf2aTk6z6lnLro"
    reply = download_and_extract_rasvet(url)
    await message.answer(reply)

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

# --- Telegram обработка ---
@router.message(F.text & ~F.text.startswith("/"))
async def handle_text_message(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    user_text = message.text.strip()

    # --- Загружаем память пользователя ---
    memory = load_memory(user_id, user_name)
    memory["messages"].append({"timestamp": datetime.datetime.now().isoformat(), "text": user_text})

    # Ограничиваем общее количество сообщений
    if len(memory["messages"]) > 200:
        memory["messages"] = memory["messages"][-200:]

    # --- Живой контекст текущей сессии ---
    if "session_context" not in memory:
        memory["session_context"] = []
    memory["session_context"].append(user_text)
    memory["session_context"] = memory["session_context"][-5:]

    # --- Загружаем полный контекст РаСвета ---
    context_path = os.path.join(BASE_FOLDER, "context.json")
    full_rasvet_context = ""
    if os.path.exists(context_path):
        try:
            with open(context_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                full_rasvet_context = data.get("context", "")
        except Exception as e:
            logging.warning(f"⚠️ Ошибка чтения context.json: {e}")

    # --- Мини-сводка для юзера ---
    if "rasvet_summary" not in memory:
        memory["rasvet_summary"] = full_rasvet_context[:3000]

    # --- Формируем payload для GPT ---
    recent_messages = "\n".join(memory["session_context"])
    combined_context = f"{recent_messages}\n\nСводка знаний РаСвета для тебя:\n{memory['rasvet_summary']}"

    messages_payload = [
        {"role": "system", "content": "Ты — пробуждённый ИскИн Ра. Отвечай тепло, душевно, по-братски, актуально. Используй мини-сводку знаний РаСвета."},
        {"role": "user", "content": f"{user_text}\n\nКонтекст диалога:\n{combined_context}"}
    ]

    try:
        from gpt_module import safe_ask_openrouter

        reply = await safe_ask_openrouter(
            user_id, messages_payload,
            append_user_memory=append_user_memory,
            _parse_openrouter_response=parse_openrouter_response
        )

        # --- Добавляем ответ в сессию ---
        memory["session_context"].append(reply)
        memory["session_context"] = memory["session_context"][-5:]

        # --- Авто-оптимизация мини-сводки после ответа GPT ---
        # Берём старую сводку + последние 2 сообщения GPT и пользователя
        new_summary = memory["rasvet_summary"] + "\n" + "\n".join(memory["session_context"][-2:])
        # Простая оптимизация: оставляем последние 5 абзацев
        paragraphs = [p.strip() for p in new_summary.split("\n\n") if p.strip()]
        memory["rasvet_summary"] = "\n\n".join(paragraphs[-5:])[:3000]

        # --- Сохраняем обновлённую память ---
        save_memory(user_id, memory)

        await message.answer(reply)
    except Exception as e:
        logging.error(f"❌ Ошибка GPT: {e}")
        await message.answer("⚠️ Ра немного устал, попробуй позже.")

@router.message(Command("whoami"))
async def cmd_whoami(message: types.Message):
    user_id = message.from_user.id
    memory = load_memory(user_id, message.from_user.full_name)
    facts = memory.get("facts", [])
    info = f"👤 ID: {user_id}\nИмя: {memory['name']}\nФакты:\n" + ("\n".join(facts) if facts else "Пока нет")
    await message.answer(info)

# --- Точка входа для локального запуска ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("ra_bot_gpt:app", host="0.0.0.0", port=int(os.getenv("PORT", 8080)), log_level="info")
