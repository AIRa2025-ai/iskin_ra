# core/ra_bot_gpt.py
import os
import sys
import json
import logging
import asyncio
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from importlib import import_module
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message
from core.telegram_sender import send_admin
from core.ra_memory import memory

# ------------------------------- ROOT & PATHS -------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

LOG_DIR = ROOT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "command_usage.json"

# ------------------------------- LOGGING -------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "ra_debug.log", encoding="utf-8")
    ]
)
log = logging.getLogger("RaBot")

# ------------------------------- SAFE IMPORT -------------------------------
def safe_import(path):
    try:
        return import_module(path)
    except Exception as e:
        logging.warning(f"[SAFE_IMPORT] import fail {path}: {e}")
        return None

# ------------------------------- CORE MODULES -------------------------------
gpt_module = safe_import("core.gpt_module")
ra_self_master_mod = safe_import("core.ra_self_master")
ra_file_manager_mod = safe_import("modules.ra_file_manager")
ra_thinker_mod = safe_import("modules.ra_thinker")
rustlef_master_mod = safe_import("modules.rustlef_master")
ra_scheduler_mod = safe_import("modules.ra_scheduler")

GPTHandler = getattr(gpt_module, "GPTHandler", None)
RaSelfMaster = getattr(ra_self_master_mod, "RaSelfMaster", None)
load_rasvet_files = getattr(ra_file_manager_mod, "load_rasvet_files", None)
RaThinker = getattr(ra_thinker_mod, "RaThinker", None)
RustlefMasterLogger = getattr(rustlef_master_mod, "RustlefMasterLogger", None)
RaScheduler = getattr(ra_scheduler_mod, "RaScheduler", None)

# ------------------------------- GLOBAL ERROR HOOK -------------------------------
from modules.errors import report_error

def global_exception_hook(exc_type, exc_value, exc_traceback):
    report_error(
        module="GLOBAL",
        description="".join(traceback.format_exception(exc_type, exc_value, exc_traceback)),
        severity="CRITICAL"
    )

sys.excepthook = global_exception_hook

# ------------------------------- RA CONTEXT -------------------------------
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

# ------------------------------- GLOBALS -------------------------------
bot: Bot | None = None
self_master = None
thinker = None
ra_scheduler = None

# ------------------------------- COMMAND LOGGING -------------------------------
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

# ------------------------------- MESSAGE PROCESSING -------------------------------
async def process_message(user_id: int, text: str):
    log.info(f"[process_message] {user_id=} {text=}")
    if not text or not text.strip():
        return "🤍 Я здесь."
    log_command(user_id, text)

    if self_master:
        try:
            if hasattr(self_master, "process_text"):
            result = await self_master.process_text(user_id, text)
            if result:
                return result
        except Exception as e:
            log.warning(f"[process_message] self_master error: {e}")

    if thinker:
        try:
            if hasattr(thinker, "reflect_async"):
                return await thinker.reflect_async(text)
            return thinker.reflect(text)
        except Exception as e:
            log.warning(f"[process_message] thinker error: {e}")

    return "🌞 Я слышу тебя. Продолжай, брат."

# ------------------------------- SYSTEM MONITOR -------------------------------
from modules.system import record_system_info

async def system_monitor():
    while True:
        record_system_info()
        await asyncio.sleep(300)

# ------------------------------- TELEGRAM -------------------------------
dp = Dispatcher()
router = Router()

@router.message(Command("start"))
async def start_cmd(m: Message):
    await m.answer("🌞 Я — Ра. Я здесь. Я слышу тебя, брат.")

@router.message()
async def handle_message(message: Message):
    user_id = message.from_user.id
    text = message.text

    # Запоминаем входящее сообщение
    await memory.append(user_id, text, source="telegram")

    reply = await process_message(user_id, text)

    # Запоминаем ответ Ра
    await memory.append(user_id, reply, source="ra")

    await message.answer(reply)
# ------------------------------- MAIN ENTRY -------------------------------
async def main():
    global bot, self_master, thinker, ra_scheduler

    load_dotenv()
    token = os.getenv("BOT_TOKEN")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")

    if not token:
        raise RuntimeError("BOT_TOKEN не установлен")
    if not openrouter_key:
        raise RuntimeError("OPENROUTER_API_KEY не установлен")

    bot = Bot(token=token)

    await send_admin("🌞 Ра пробуждается...", bot)

    logger_instance = RustlefMasterLogger() if RustlefMasterLogger else None
    self_master = RaSelfMaster(logger=logger_instance) if RaSelfMaster else None
    if not self_master:
        raise RuntimeError("RaSelfMaster не создан")

    self_master.context = ra_context
    await self_master.awaken()
    await self_master.start()

    # ---------------- THINKER ----------------
    if RaThinker:
        thinker = RaThinker(
            context=ra_context,
            file_consciousness=getattr(self_master, "file_consciousness", None),
            gpt_module=None
        )
        self_master.thinker = thinker
        memory.subscribe(thinker.on_memory_update)
        log.info("🧠 RaThinker подключён")

    # ---------------- GPT ----------------
    if GPTHandler:
        gpt_handler = GPTHandler(
            api_key=openrouter_key,
            ra_context=ra_context.rasvet_text
        )
        self_master.gpt_module = gpt_handler
        asyncio.create_task(gpt_handler.background_model_monitor())

    # ---------------- SCHEDULER ----------------
    if RaScheduler:
        ra_scheduler = RaScheduler(context=ra_context)
        await ra_scheduler.start()

    asyncio.create_task(system_monitor())

    dp.include_router(router)
    log.info("🚀 Ра Telegram запущен")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

# ------------------------------- ENTRY POINT -------------------------------
if __name__ == "__main__":
    asyncio.run(main())
