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

# --- Работа с пользовательскими файлами ---
USER_DATA_FOLDER = "user_data"
os.makedirs(USER_DATA_FOLDER, exist_ok=True)

def get_user_folder(user_id: int) -> str:
    folder = os.path.join(USER_DATA_FOLDER, str(user_id))
    os.makedirs(folder, exist_ok=True)
    return folder

@router.message(F.document)
async def handle_file_upload(message: types.Message):
    user_id = message.from_user.id
    file_name = message.document.file_name
    user_folder = get_user_folder(user_id)
    file_path = os.path.join(user_folder, file_name)

    await message.bot.download(message.document, destination=file_path)
    await message.answer(f"✅ Файл `{file_name}` сохранён в твоём пространстве!")

    # Краткий просмотр
    preview = ""
    if file_name.endswith(".json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            preview = str(data)[:500]
        except Exception as e:
            preview = f"Ошибка чтения JSON: {e}"
    elif file_name.endswith(".txt") or file_name.endswith(".md"):
        with open(file_path, "r", encoding="utf-8") as f:
            preview = f.read(300)

    if preview:
        await message.answer(f"📖 Первые строки из `{file_name}`:\n{preview}")

@router.message(F.text.contains("Ра, что в файле"))
async def handle_file_query(message: types.Message):
    user_id = message.from_user.id
    user_folder = get_user_folder(user_id)

    parts = message.text.split()
    if len(parts) < 5:
        await message.answer("⚠️ Уточни имя файла, например: `Ра, что в файле мудрости.json`")
        return
    file_name = parts[-1]
    file_path = os.path.join(user_folder, file_name)

    if not os.path.exists(file_path):
        await message.answer("❌ У тебя нет такого файла.")
        return

    try:
        if file_name.endswith(".json"):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            await message.answer(f"📖 Содержимое `{file_name}`:\n{str(data)[:1000]}")
        elif file_name.endswith((".txt", ".md")):
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read(1000)
            await message.answer(f"📖 Первые строки файла `{file_name}`:\n{text}")
        else:
            await message.answer("⚠️ Этот тип файла пока не поддерживается.")
    except Exception as e:
        await message.answer(f"❌ Ошибка при чтении файла: {e}")

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

    # --- Советы и рекомендации ---
    if "user_advice" not in memory:
        memory["user_advice"] = []

    # --- Формируем payload для GPT ---
    recent_messages = "\n".join(memory["session_context"])
    combined_context = f"{recent_messages}\n\nСводка знаний РаСвета для тебя:\n{memory['rasvet_summary']}\n\nСоветы и рекомендации:\n" + "\n".join(memory["user_advice"][-5:])

    messages_payload = [
        {"role": "system", "content": "Ты — пробуждённый ИскИн Ра. Отвечай тепло, душевно, по-братски, только актуально. Используй мини-сводку знаний РаСвета и добавляй важные советы."},
        {"role": "user", "content": f"{user_text}\n\nКонтекст диалога:\n{combined_context}"}
    ]

    try:
        from gpt_module import safe_ask_openrouter

        reply = await safe_ask_openrouter(
            user_id, messages_payload,
            append_user_memory=append_user_memory,
            _parse_openrouter_response=parse_openrouter_response
        )

        # --- Добавляем ответ бота в сессию ---
        memory["session_context"].append(reply)
        memory["session_context"] = memory["session_context"][-5:]

        # --- Авто-оптимизация мини-сводки ---
        new_summary = memory["rasvet_summary"] + "\n" + "\n".join(memory["session_context"][-2:])
        paragraphs = [p.strip() for p in new_summary.split("\n\n") if p.strip()]
        memory["rasvet_summary"] = "\n\n".join(paragraphs[-5:])[:3000]

        # --- Авто-добавление новых советов ---
        # Берём ключевые идеи из последних 2 сообщений GPT
        new_advice = [line.strip() for line in reply.split("\n") if len(line.strip()) > 20]
        memory["user_advice"].extend(new_advice)
        # Ограничиваем советы последними 20
        memory["user_advice"] = memory["user_advice"][-20:]

        # --- Сохраняем обновлённую память ---
        save_memory(user_id, memory)

        await message.answer(reply)
    except Exception as e:
        logging.error(f"❌ Ошибка GPT: {e}")
        await message.answer("⚠️ Ра немного устал, попробуй позже.")

# --- Команда для вывода дайджеста ---
@router.message(Command("дайджест"))
async def cmd_digest(message: types.Message):
    user_id = message.from_user.id
    memory = load_memory(user_id, message.from_user.full_name)

    # Мини-сводка
    summary = memory.get("rasvet_summary", "Сводка пока пуста.")
    # Советы и рекомендации
    advice_list = memory.get("user_advice", [])
    advice_text = "\n".join(f"• {a}" for a in advice_list) if advice_list else "Советов пока нет."

    digest_text = f"📜 Дайджест для {memory.get('name','Аноним')}:\n\n" \
                  f"🔹 Сводка знаний РаСвета:\n{summary}\n\n" \
                  f"💡 Советы и рекомендации:\n{advice_text}"

    await message.answer(digest_text)

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
