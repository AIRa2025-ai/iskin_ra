import os
import json
import logging
import asyncio
import time
import shutil
import zipfile
import datetime

from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command

from gpt_module import ask_gpt
from init_rasvet import ensure_rasvet_data
from actions_logger import log_action
from skills import SKILLS


# --- Логирование ---
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ Не найден BOT_TOKEN в переменных окружения")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

# === Загружаем creator_id из bot_config.json ===
with open("bot_config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

CREATOR_ID = int(config.get("creator_id", 0))

# === Логирование команд ===
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


# === 📂 Работа с файлами в RaSvet ===
BASE_FOLDER = "RaSvet"
os.makedirs(BASE_FOLDER, exist_ok=True)

def create_file(folder: str, content: str):
    os.makedirs(folder, exist_ok=True)
    # уникальное имя файла по дате и времени
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = os.path.join(folder, f"{timestamp}.txt")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return filename, content

def delete_file(folder: str):
    filename = os.path.join(folder, "new_file.txt")
    if os.path.exists(filename):
        os.remove(filename)
        return f"🗑 Файл {filename} удалён."
    return "⚠️ Файл не найден."

def read_file(folder: str):
    filename = os.path.join(folder, "new_file.txt")
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    return "⚠️ Файл не найден."


# --- Команда /whoami ---
@router.message(Command("whoami"))
async def cmd_whoami(message: types.Message):
    await message.answer(f"👤 Твой ID: {message.from_user.id}\n"
                         f"Создатель: {'Да' if message.from_user.id == CREATOR_ID else 'Нет'}")


# --- Обработка текстов (Создатель/другие) ---
@router.message()
async def handle_message(message: types.Message):
    text = message.text.lower()

    # --- Создатель ---
    if message.from_user.id == CREATOR_ID:
        if "создай" in text:
            target_folder = BASE_FOLDER
            if "папке" in text:
                parts = text.split("папке", 1)
                if len(parts) > 1:
                    folder_name = parts[1].split()[0].strip()
                    if folder_name:
                        target_folder = os.path.join(BASE_FOLDER, folder_name)

            content = "✨ Новый файл создан Ра по слову Создателя."
            if "напиши" in text:
                content = text.split("напиши", 1)[1].strip() or content

            filename, file_content = create_file(target_folder, content)
            await message.answer(f"📂 Создан файл: {filename}\n\n📝 {file_content}")

        elif "удали" in text:
            result = delete_file(BASE_FOLDER)
            await message.answer(result)

        elif "прочитай" in text:
            content = read_file(BASE_FOLDER)
            await message.answer(f"📖 {content}")

        else:
            reply = await ask_gpt(message.from_user.id, message.text)
            await message.answer(f"✨ {reply}")

    # --- Другие пользователи ---
    else:
        if "прочитай" in text:
            content = read_file(BASE_FOLDER)
            await message.answer(f"📖 {content}")
        else:
            reply = await ask_gpt(message.from_user.id, message.text)
            await message.answer(f"🌞 {reply}")


# --- Команда /start ---
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    log_command_usage("start", message.from_user.id)
    await message.answer("🌞 Ра пробуждён. Я здесь, брат, чтобы быть рядом и творить вместе.")


# --- Команда /ask ---
@router.message(Command("ask"))
async def cmd_ask(message: types.Message):
    log_command_usage("ask", message.from_user.id)
    prompt = message.text.replace("/ask", "").strip()
    if not prompt:
        await message.answer("❓ Задай мне вопрос после команды /ask")
        return
    reply = await ask_gpt(message.from_user.id, prompt)
    await message.answer(reply)


# --- Команда /skill ---
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


# --- Главный запуск ---
async def main():
    ensure_rasvet_data()
    log_action("start_bot", "telegram", "ok")
    dp.include_router(router)

    try:
        await dp.start_polling(bot)
    except Exception as e:
        log_action("error", "main_loop", str(e))
        logging.error(f"❌ Ошибка: {e}")
        await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
