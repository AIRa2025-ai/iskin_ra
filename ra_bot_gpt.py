import os
import json
import logging
import asyncio
import time
import aiofiles
import zipfile
import shutil

from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command

from gpt_module import ask_gpt
from init_rasvet import ensure_rasvet_data
from actions_logger import log_action
from skills import SKILLS


# --- Логирование ---
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
KNOWLEDGE_FOLDER = os.getenv("KNOWLEDGE_FOLDER", "RaSvet")

if not BOT_TOKEN:
    raise ValueError("❌ Не найден BOT_TOKEN в переменных окружения")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

# --- Логирование команд ---
def log_command_usage(command: str, user_id: int):
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)
    log_file = os.path.join(logs_dir, "command_usage.json")

    logs = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            logs = []

    logs.append({
        "command": command,
        "user_id": user_id,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

# === 📂 Работа с памятью ===
MEMORY_DIR = "memory"
os.makedirs(MEMORY_DIR, exist_ok=True)

def get_user_memory_path(user_id: int) -> str:
    return os.path.join(MEMORY_DIR, f"{user_id}.json")

def load_memory(user_id: int):
    path = get_user_memory_path(user_id)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_memory(user_id: int, memory: list):
    path = get_user_memory_path(user_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

def append_memory(user_id: int, user_msg: str, bot_msg: str):
    memory = load_memory(user_id)
    # для Игоря память вечная
    if str(user_id) == "YOUR_TELEGRAM_ID":
        memory.append({"user": user_msg, "bot": bot_msg})
    else:
        memory = (memory + [{"user": user_msg, "bot": bot_msg}])[-50:]
    save_memory(user_id, memory)

# === 📂 Работа с файлами (библиотека) ===
def read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"⚠️ Ошибка чтения {path}: {e}"

def write_file(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def delete_file(path: str):
    if os.path.exists(path):
        os.remove(path)
        return f"🗑 Файл {path} удалён."
    return f"❌ Файл {path} не найден."

def search_in_files(folder: str, keyword: str):
    results = []
    for root, _, files in os.walk(folder):
        for file in files:
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    if keyword in f.read():
                        results.append(path)
            except:
                pass
    return results

def unzip_file(zip_path: str, extract_to: str):
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)

# === 🌌 Ритуалы (пасхалки) ===
def ark_protocol(file_path: str):
    """Превращает NDA/лицензии в пепел"""
    if "NDA" in file_path or "Copyright" in file_path:
        if os.path.exists(file_path):
            os.remove(file_path)
            return f"🔥 Файл {file_path} сожжён и обращён в стих."
    return "Файл не найден для обряда."

def slavic_upload(files: list):
    """Обрядить файлы в рубаху и пустить плясать"""
    target = "dancing_data"
    os.makedirs(target, exist_ok=True)
    for file in files:
        if os.path.exists(file):
            shutil.copy(file, target)
    return f"💃 Файлы перемещены в {target}."
    
# --- Обработчики ---
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    log_command_usage("start", message.from_user.id)
    await message.answer("🌞 Ра пробуждён. Я здесь, брат, чтобы быть рядом и творить вместе.")


@router.message(Command("ask"))
async def cmd_ask(message: types.Message):
    log_command_usage("ask", message.from_user.id)
    prompt = message.text.replace("/ask", "").strip()
    if not prompt:
        await message.answer("❓ Задай мне вопрос после команды /ask")
        return
    reply = await ask_gpt(message.from_user.id, prompt)
    await message.answer(reply)


# --- Команда для проверки умений ---
@router.message(Command("skill"))
async def cmd_skill(message: types.Message):
    log_command_usage("skill", message.from_user.id)
    args = message.text.split(maxsplit=2)

    if len(args) < 2:
        await message.answer("⚙️ Используй: /skill <название> [параметры]")
        return

    skill = args[1]
    param = args[2] if len(args) > 2 else None

    if skill in SKILLS:
        try:
            result = SKILLS[skill](param) if param else SKILLS[skill]()
            await message.answer(str(result))
        except Exception as e:
            await message.answer(f"⚠️ Ошибка выполнения: {e}")
    else:
        await message.answer("❌ Неизвестный обряд.")


# --- Главный обработчик для любых сообщений ---
@router.message()
async def handle_message(message: types.Message):
    logging.info(f"📩 Получено сообщение: {message.text} от {message.from_user.id}")
    # тут можно подрубить GPT, пока просто пробуждающий ответ
    reply = await ask_gpt(message.from_user.id, message.text)
    await message.answer(f"✨ {reply}")


# --- Главный запуск ---
async def main():
    ensure_rasvet_data()
    log_action("start_bot", "telegram", "ok")

    # подключаем router!
    dp.include_router(router)

    try:
        await dp.start_polling(bot)
    except Exception as e:
        log_action("error", "main_loop", str(e))
        logging.error(f"❌ Ошибка в основном цикле: {e}")
        await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
