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
# PATHS
# -------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

LOG_DIR = ROOT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "command_usage.json"

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/ra_debug.log", encoding="utf-8")
    ]
)

log = logging.getLogger("RaBot")

# -------------------------------
# SAFE IMPORT
# -------------------------------
def safe_import(path):
    try:
        return import_module(path)
    except Exception as e:
        logging.warning(f"import fail {path}: {e}")
        return None

# -------------------------------
# IMPORT CORE MODULES
# -------------------------------
gpt_module = safe_import("core.gpt_module")
ra_self_master_mod = safe_import("core.ra_self_master")

RaSelfMaster = getattr(ra_self_master_mod, "RaSelfMaster", None)
GPTHandler = getattr(gpt_module, "GPTHandler", None)

# -------------------------------
# INIT CORE
# -------------------------------
self_master = RaSelfMaster() if RaSelfMaster else None
gpt_handler = None

# -------------------------------
# LOG COMMANDS
# -------------------------------
def log_command(user_id, text):
    try:
        data = json.loads(LOG_FILE.read_text("utf-8")) if LOG_FILE.exists() else []
        data.append({
            "user": user_id,
            "text": text,
            "time": datetime.utcnow().isoformat()
        })
        cutoff = datetime.utcnow() - timedelta(days=10)
        data = [x for x in data if datetime.fromisoformat(x["time"]) > cutoff]
        LOG_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
    except Exception as e:
        logging.warning(f"log_command error: {e}")

# -------------------------------
# INPUT CLEAN
# -------------------------------
def ra_clean_input(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = text.strip()
    if len(text) < 2 or len(text) > 5000:
        return ""
    return text

# -------------------------------
# PROCESS MESSAGE
# -------------------------------
async def process_message(user_id: int, text: str):
    text = ra_clean_input(text)
    if not text:
        return "🤍 Брат, я не чувствую смысла в этом сообщении."

    log_command(user_id, text)

    if self_master:
        try:
            reply = await self_master.process_text(user_id, text)
            return reply
        except Exception as e:
            logging.exception(f"[RaSelfMaster] process_text error")

    return "⚠️ CORE временно недоступен, брат."

# -------------------------------
# TELEGRAM SETUP
# -------------------------------
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
    if m.text and m.text.startswith("/"):
        return
    reply = await process_message(m.from_user.id, m.text)
    await m.answer(reply)

# -------------------------------
# MAIN
# -------------------------------
async def main():
    global gpt_handler

    load_dotenv()

    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN не установлен")

    bot = Bot(token=token)

    # ---- GPT INIT (ВАЖНО)
    if GPTHandler and self_master:
        gpt_handler = GPTHandler()
        self_master.gpt_module = gpt_handler
        log.info("🧠 GPTHandler подключён к CORE")

        if gpt_handler.GPT_ENABLED:
            gpt_handler.background_task = asyncio.create_task(
                gpt_handler.background_model_monitor()
            )
            log.info("🌀 GPT монитор запущен")

    # ---- CORE AWAKEN
    if self_master:
        try:
            log.info("🌱 Пробуждение CORE...")
            await self_master.awaken()
            log.info("🌞 CORE пробуждён")
        except Exception:
            log.exception("CORE awaken error")

    dp.include_router(router)
    log.info("🚀 РаСвет Telegram запущен (polling)")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

# -------------------------------
# ENTRY
# -------------------------------
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("🛑 Ра остановлен вручную")
    except Exception:
        log.exception("💥 Критическая ошибка Ра")
