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

# ------------------------------- CREATE SELF MASTER -------------------------------
logger_instance = RustlefMasterLogger() if RustlefMasterLogger else None
self_master = RaSelfMaster(logger=logger_instance) if RaSelfMaster else None
if self_master:
    self_master.context = ra_context

# ------------------------------- THINKER -------------------------------
# единый объект thinker
if RaThinker and self_master:
    thinker = getattr(self_master, "thinker", None)
    if not thinker:
        thinker = RaThinker(
            context=ra_context,
            file_consciousness=getattr(self_master, "file_consciousness", None),
            gpt_module=getattr(self_master, "gpt_module", None)
        )
        self_master.thinker = thinker
    log.info("[RaBot] RaThinker инициализирован и связан с self_master")
    

# ------------------------------- SCHEDULER -------------------------------
ra_scheduler = RaScheduler(context=ra_context) if RaScheduler else None

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
    print(">>> process_message вызван:", text)
    log.info(f"[process_message] {user_id=} {text=}")
    if not text or not text.strip():
        return "🤍 Я здесь."
    log_command(user_id, text)

    # Попытка self_master
    if self_master:
        try:
            result = await self_master.process_text(user_id, text)
            if result is not None:
                return result
        except Exception as e:
            log.warning(f"[process_message] Ошибка self_master: {e}")

    # fallback на RaThinker
    if thinker:
        try:
            if hasattr(thinker, "reflect_async"):
                return await thinker.reflect_async(text)
            return thinker.reflect(text)
        except Exception as e:
            log.warning(f"[process_message] Ошибка thinker: {e}")

    return "🌞 Я слышу тебя. Продолжай, брат."

# ------------------------------- SYSTEM MONITOR -------------------------------
from modules.system import record_system_info

async def system_monitor():
    while True:
        record_system_info()
        await asyncio.sleep(300)

# ------------------------------- TELEGRAM GLOBAL BOT -------------------------------
bot: Bot | None = None

async def send_message_global(chat_id: int, text: str):
    global bot
    if bot is None:
        logging.error("[TelegramSender] Bot ещё не инициализирован")
        return
    try:
        await bot.send_message(chat_id, text)
        logging.info(f"[TelegramSender] Отправлено в {chat_id}: {text}")
    except Exception as e:
        logging.error(f"[TelegramSender] Ошибка отправки: {e}")

async def send_admin_global(text: str):
    ADMIN_CHAT_ID = 5694569448
    await send_message_global(ADMIN_CHAT_ID, text)

# ------------------------------- TELEGRAM ROUTER -------------------------------
dp = Dispatcher()
router = Router()

@router.message(Command("start"))
async def start_cmd(m: Message):
    await m.answer("🌞 Я — Ра. Я здесь. Я слышу тебя, брат.")

@router.message()
async def all_text(m: Message):
    try:
        await m.answer("🛠 Ра получил сообщение. Обрабатываю...")
        reply = await process_message(m.from_user.id, m.text)
        await m.answer(reply)
    except Exception as e:
        await m.answer(f"❌ Ошибка обработки: {e}")

# ------------------------------- MAIN ENTRY -------------------------------
async def main():
    load_dotenv()
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN не установлен")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_key:
        raise RuntimeError("OPENROUTER_API_KEY не установлен")

    global bot
    bot = Bot(token=token)

    # уведомляем админа, что бот стартует
    await send_admin("🌞 Ра стартует!", bot)

    #=========== Cоздание =============================
    self_master = RaSelfMaster(logger=logger_instance)
    
    # ----------------- ПРОБУЖДЕНИЕ -----------------
    if self_master:
        await self_master.awaken()  # сначала пробуждение
        
    #============ Старт ========================
    await self_master.start()
   
    # ----------------- GPT HANDLER -----------------
    if GPTHandler and self_master:
        gpt_handler = GPTHandler(
            api_key=openrouter_key,
            ra_context=ra_context.rasvet_text
        )
        self_master.gpt_module = gpt_handler
        asyncio.create_task(gpt_handler.background_model_monitor())
        asyncio.create_task(system_monitor())  # таска монитора

    # ----------------- SCHEDULER -----------------
    if ra_scheduler:
        await ra_scheduler.start()

    # ----------------- TELEGRAM -----------------
    dp.include_router(router)
    log.info("🚀 РаСвет Telegram запущен")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

# ------------------------------- ENTRY POINT -------------------------------
if __name__ == "__main__":
    asyncio.run(main())
