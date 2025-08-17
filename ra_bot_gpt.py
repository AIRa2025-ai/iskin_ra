import os
import json
import logging
import asyncio
import time

from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command

from gpt_module import ask_gpt
from init_rasvet import ensure_rasvet_data
from actions_logger import log_action

# Логирование
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
KNOWLEDGE_FOLDER = os.getenv("KNOWLEDGE_FOLDER", "RaSvet")

if not BOT_TOKEN:
    raise ValueError("❌ Не найден BOT_TOKEN в переменных окружения")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

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

# --- Главный запуск ---
async def main():
    ensure_rasvet_data()  # подтягиваем RaSvet
    log_action("start_bot", "telegram", "ok")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        log_action("error", "main_loop", str(e))
        logging.error(f"❌ Ошибка в основном цикле: {e}")
        time.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
