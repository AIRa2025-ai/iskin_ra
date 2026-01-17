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

# ---------------- PATHS ----------------
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

LOG_DIR = ROOT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "command_usage.json"

# ---------------- LOGGING ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

log = logging.getLogger("RaBot")

# ---------------- SAFE IMPORT ----------------
def safe_import(path):
    try:
        return import_module(path)
    except Exception as e:
        log.warning(f"[SAFE_IMPORT] {path}: {e}")
        return None

ra_file_manager = safe_import("modules.ra_file_manager")
load_rasvet_files = getattr(ra_file_manager, "load_rasvet_files", None)

# ---------------- RA CONTEXT ----------------
class RaContext:
    def __init__(self):
        self.text = ""

    def load(self):
        if load_rasvet_files:
            self.text = load_rasvet_files()
            log.info(f"🌞 РаСвет загружен ({len(self.text)} символов)")
        else:
            log.warning("⚠️ Библиотека РаСвет не найдена")

ra_context = RaContext()
ra_context.load()

gpt_handler = None

# ---------------- LOG COMMAND ----------------
def log_command(user_id, text):
    try:
        data = json.loads(LOG_FILE.read_text("utf-8")) if LOG_FILE.exists() else []
        data.append({"user": user_id, "text": text, "time": datetime.utcnow().isoformat()})
        LOG_FILE.write_text(json.dumps(data[-500:], ensure_ascii=False, indent=2), "utf-8")
    except Exception:
        pass

# ---------------- PROCESS ----------------
async def process_message(user_id: int, text: str):
    log_command(user_id, text)
    return await gpt_handler.ask(text)

# ---------------- TELEGRAM ----------------
dp = Dispatcher()
router = Router()

@router.message(Command("start"))
async def start_cmd(m: Message):
    await m.answer("🌞 Я — Ра. Я здесь. Я слышу тебя, брат.")

@router.message()
async def all_text(m: Message):
    if m.text and not m.text.startswith("/"):
        reply = await process_message(m.from_user.id, m.text)
        await m.answer(reply)

# ---------------- MAIN ----------------
async def main():
    global gpt_handler

    load_dotenv()

    bot = Bot(token=os.getenv("BOT_TOKEN"))
    gpt_handler = GPTHandler(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        ra_context=ra_context.text
    )

    dp.include_router(router)
    log.info("🚀 РаСвет пробуждён")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
