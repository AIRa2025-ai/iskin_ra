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
from core.gpt_module import GPTHandler

# -------------------------------
# PATHS
# -------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

LOG_DIR = ROOT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "command_usage.json"

# -------------------------------
# LOGGING
# -------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "ra_debug.log", encoding="utf-8")
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
        logging.warning(f"[SAFE_IMPORT] import fail {path}: {e}")
        return None

# -------------------------------
# IMPORT CORE MODULES
# -------------------------------
gpt_module = safe_import("core.gpt_module")
ra_self_master_mod = safe_import("core.ra_self_master")
ra_file_manager = safe_import("modules.ra_file_manager")
ra_thinker_mod = safe_import("modules.ra_thinker")

RaSelfMaster = getattr(ra_self_master_mod, "RaSelfMaster", None)
GPTHandler = getattr(gpt_module, "GPTHandler", None)
load_rasvet_files = getattr(ra_file_manager, "load_rasvet_files", None)
RaThinker = getattr(ra_thinker_mod, "RaThinker", None)

# -------------------------------
# RA CONTEXT
# -------------------------------
class RaContext:
    def __init__(self):
        self.rasvet_text = ""
        self.created_at = datetime.utcnow().isoformat()

    def load(self):
        if load_rasvet_files:
            self.rasvet_text = load_rasvet_files()
            log.info(f"🌞 RaContext загружен ({len(self.rasvet_text)} символов)")
        else:
            log.warning("⚠️ load_rasvet_files не найден")

# -------------------------------
# INIT CORE
# -------------------------------
ra_context = RaContext()
ra_context.load()

self_master = RaSelfMaster() if RaSelfMaster else None
if self_master:
    self_master.context = ra_context
thinker = RaThinker() if RaThinker else None
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
# PROCESS MESSAGE
# -------------------------------
async def process_message(user_id: int, text: str):
    if not text or len(text) < 2:
        return "🤍 Я здесь, брат."

    log_command(user_id, text)

    # 1️⃣ GPT
    if self_master and getattr(self_master, "gpt_module", None):
        try:
            response = await self_master.gpt_module.ask(text)
            if response:
                return response
        except Exception:
            logging.exception("[GPT] ошибка ответа")

    # 2️⃣ THINKER
    if thinker:
        return thinker.reflect(text)

    # 3️⃣ HEART FALLBACK
    return "🌞 Я слышу тебя. Продолжай, брат."

# -------------------------------
# TELEGRAM
# -------------------------------
dp = Dispatcher()
router = Router()

@router.message(Command("start"))
async def start_cmd(m: Message):
    await m.answer("🌞 Я — Ра. Я здесь. Я слышу.")

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

    if GPTHandler and self_master:
        gpt_handler = GPTHandler()
        self_master.gpt_module = gpt_handler

        if ra_context.rasvet_text:
            gpt_handler.set_ra_context(ra_context.rasvet_text)

    if self_master:
        await self_master.awaken()

    dp.include_router(router)
    log.info("🚀 РаСвет Telegram запущен")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
