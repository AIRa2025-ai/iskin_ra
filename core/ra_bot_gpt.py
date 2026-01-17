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

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

LOG_DIR = ROOT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "command_usage.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout),
              logging.FileHandler(LOG_DIR / "ra_debug.log", encoding="utf-8")]
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
    if not text or len(text.strip()) < 1:
        return "🤍 Я здесь."

    log_command(user_id, text)

    if self_master:
        return await self_master.process_text(user_id, text)

    if thinker:
        return thinker.reflect(text)

    return "🌞 Я слышу тебя. Продолжай, брат."
    
# -------------------------------
# TELEGRAM
# -------------------------------
dp = Dispatcher()
router = Router()

@router.message(Command("start"))
async def start_cmd(m: Message):
    await m.answer("🌞 Я — Ра. Я здесь. Я слышу тебя, брат.")

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

    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_key:
        raise RuntimeError("OPENROUTER_API_KEY не установлен")

    if GPTHandler and self_master:
        gpt_handler = GPTHandler(
            api_key=openrouter_key,
            ra_context=ra_context.rasvet_text
        )
        self_master.gpt_module = gpt_handler

        # Запуск фонового монитора моделей
        asyncio.create_task(gpt_handler.background_model_monitor())

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
