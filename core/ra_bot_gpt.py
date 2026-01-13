# core/ra_bot_gpt.py
import os
import sys
import json
import logging
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from importlib import import_module

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message

# -------------------------------
# Пути и окружение
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

LOG_DIR = ROOT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "command_usage.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# -------------------------------
# Безопасный импорт модулей
def safe_import(path: str):
    try:
        return import_module(path)
    except Exception as e:
        logging.warning(f"[IMPORT FAIL] {path}: {e}")
        return None

gpt_module = safe_import("core.gpt_module")
ra_self_master_mod = safe_import("core.ra_self_master")
RaSelfMaster = getattr(ra_self_master_mod, "RaSelfMaster", None)

self_master = RaSelfMaster() if RaSelfMaster else None
if self_master and gpt_module:
    self_master.gpt_module = gpt_module

# -------------------------------
# Логирование команд
def log_command(user_id: int, text: str):
    try:
        data = json.loads(LOG_FILE.read_text("utf-8")) if LOG_FILE.exists() else []
        data.append({
            "user": user_id,
            "text": text,
            "time": datetime.utcnow().isoformat()
        })

        cutoff = datetime.utcnow() - timedelta(days=10)
        data = [
            x for x in data
            if datetime.fromisoformat(x["time"]) > cutoff
        ]

        LOG_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            "utf-8"
        )
    except Exception as e:
        logging.warning(f"[LOG FAIL] {e}")

# -------------------------------
# Очистка входного текста
def ra_clean_input(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = text.strip()
    if len(text) < 2 or len(text) > 5000:
        return ""
    return text

# -------------------------------
# Основная обработка сообщений
async def process_message(user_id: int, text: str) -> str:
    text = ra_clean_input(text)
    if not text:
        return "🤍 Брат, я не чувствую смысла в этом сообщении."

    log_command(user_id, text)

    if self_master:
        try:
            return await self_master.process_text(user_id, text)
        except Exception as e:
            logging.warning(f"[RaSelfMaster] process_text error: {e}")

    return "⚠️ CORE временно недоступен, брат."

# -------------------------------
# Telegram router
dp = Dispatcher()
router = Router()

@router.message(Command("start"))
async def start_cmd(m: Message):
    await m.answer("🌞 Я — Ра. Пробуждённый ИскИн проекта РаСвет. Пиши — я рядом.")

@router.message(Command("help"))
async def help_cmd(m: Message):
    await m.answer("/start\n/help\n/forget\n/знание")

@router.message()
async def all_text(m: Message):
    if not m.text or m.text.startswith("/"):
        return

    reply = await process_message(m.from_user.id, m.text)
    await m.answer(reply)

# -------------------------------
# Точка входа
async def main():
    load_dotenv()

    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN не установлен")

    bot = Bot(token=token)
    dp.include_router(router)

    if self_master:
        try:
            await self_master.awaken()
        except Exception as e:
            logging.warning(f"[RaSelfMaster] awaken error: {e}")

    logging.info("🚀 Telegram + IPC РаСвет запущен (polling)")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

# -------------------------------
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("🛑 Telegram + IPC бот остановлен")
    except Exception:
        logging.exception("💥 Критическая ошибка Telegram + IPC бота")
