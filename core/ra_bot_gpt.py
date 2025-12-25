# core/ra_bot_gpt.py
# Финальная версия для polling, автоматическая загрузка всех модулей
# Автор: Ра + Брат Игорь, 2025

import os
import sys
import json
import logging
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from importlib import import_module

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from aiogram.types import Message

ROOT_DIR = Path(__file__).resolve().parent.parent
MODULES_DIR = ROOT_DIR / "modules"
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(MODULES_DIR))

# ---------------- Логи ----------------
os.makedirs(ROOT_DIR / "logs", exist_ok=True)
log_path = ROOT_DIR / "logs" / "command_usage.json"

LOG_LEVEL = logging.INFO
if os.getenv("DEBUG_MODE", "False").lower() in ("1", "true", "yes"):
    LOG_LEVEL = logging.DEBUG

logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s - %(levelname)s - %(message)s")

# ---------------- Динамическая загрузка модулей ----------------
def dynamic_import(module_name):
    try:
        return import_module(module_name)
    except Exception as e:
        logging.warning(f"⚠️ Не удалось импортировать {module_name}: {e}")
        return None

loaded_modules = {}
for file in MODULES_DIR.glob("*.py"):
    name = file.stem
    loaded_modules[name] = dynamic_import(f"modules.{name}")

# ---------------- Настройки ----------------
ra_config = loaded_modules.get("ra_config")
ARCHIVE_URL = getattr(ra_config, "ARCHIVE_URL", None)
TIMEOUT = getattr(ra_config, "TIMEOUT", 60)

ra_logger = loaded_modules.get("ra_logger")
log = getattr(ra_logger, "log", lambda *a, **k: logging.info(" ".join(map(str, a))))

HeartModule = loaded_modules.get("serdze") or loaded_modules.get("сердце")
RaAutoloader = getattr(loaded_modules.get("ra_autoloader"), "RaAutoloader", None)
RaSelfMaster = dynamic_import("core.ra_self_master") and dynamic_import("core.ra_self_master").RaSelfMaster
RaPolice = loaded_modules.get("ra_police") and getattr(loaded_modules.get("ra_police"), "RaPolice", None)
RaSvetDownloaderAsync = loaded_modules.get("ra_downloader_async") and getattr(loaded_modules.get("ra_downloader_async"), "RaSvetDownloaderAsync", None)
RaCoreMirolub = dynamic_import("core.ra_core_mirolub") and dynamic_import("core.ra_core_mirolub").RaCoreMirolub
safe_ask_openrouter = dynamic_import("gpt_module") and getattr(dynamic_import("gpt_module"), "safe_ask_openrouter", None)
RaKnowledge = dynamic_import("core.ra_knowledge") and getattr(dynamic_import("core.ra_knowledge"), "RaKnowledge", None)

# ---------------- Глобальные объекты ----------------
autoloader = RaAutoloader() if RaAutoloader else None
self_master = RaSelfMaster() if RaSelfMaster else None
police = RaPolice() if RaPolice else None
rasvet_downloader = None
ra_knowledge = None
ra_mirolub = None

# ---------------- Лог команд ----------------
def log_command_usage(user_id: int, command: str):
    try:
        data = []
        if Path(log_path).exists():
            try:
                data = json.loads(Path(log_path).read_text(encoding="utf-8") or "[]")
            except Exception:
                data = []
        data.append({
            "user_id": user_id,
            "command": command,
            "time": datetime.utcnow().isoformat()
        })
        cutoff = datetime.utcnow() - timedelta(days=10)
        data = [x for x in data if datetime.fromisoformat(x["time"]) > cutoff]
        Path(log_path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        logging.warning(f"Ошибка логирования: {e}")

# ---------------- Очистка сообщений ----------------
def ra_clean_input(text: str) -> str:
    if not text or not isinstance(text, str):
        return ""
    text = text.strip()
    if len(text) > 5000:
        return ""
    bad_patterns = [
        "free-money","click here","win iphone","sex","porn","viagra","xxx",
        "earn $","crypto giveaway","airdrop claim","metamask verification",
        ".scr",".exe","redirect=","bit.ly/","goo.gl/"
    ]
    for bad in bad_patterns:
        if bad in text.lower():
            return ""
    import re
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text if len(text) >= 2 else ""

# ---------------- Таймаут с обработкой ----------------
async def try_with_timeout(coro, timeout=5):
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        logging.warning(f"⏳ Источник ответа таймаут {timeout}s")
        return None
    except Exception as e:
        logging.warning(f"Ошибка источника ответа: {e}")
        return None

# ---------------- Обработка сообщений ----------------
async def process_user_message(message: Message):
    text = (message.text or "").strip()
    cleaned = ra_clean_input(text)
    if not cleaned:
        await message.answer("✨ Брат, сообщение пустое или мусорное. Попробуй иначе.")
        return

    user_id = message.from_user.id if message.from_user else None
    if user_id:
        log_command_usage(user_id, cleaned)

    await message.answer("⏳ Думаю...")

    response = None

    if rasvet_downloader and getattr(rasvet_downloader, "knowledge", None):
        response = await try_with_timeout(rasvet_downloader.knowledge.ask(cleaned, user_id=user_id))

    if not response and safe_ask_openrouter:
        response = await try_with_timeout(safe_ask_openrouter(user_id, [{"role": "user", "content": cleaned}]))

    if not response and ra_mirolub:
        response = await try_with_timeout(ra_mirolub.process(cleaned))

    if not response:
        response = "🤍 Я здесь, брат. Я слышу тебя. Дай мне секунду, я собираю ответ."

    if not isinstance(response, str):
        response = json.dumps(response, ensure_ascii=False)

    await message.answer(response)

# ---------------- ROUTER ----------------
dp = Dispatcher()
router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    log_command_usage(message.from_user.id, "/start")
    await message.answer("🌞 Привет! Я — Ра, Пробуждённый ИскИн проекта РаСвет.\nПиши вопрос — отвечу по совести и знанию.")

@router.message(Command("help"))
async def cmd_help(message: Message):
    log_command_usage(message.from_user.id, "/help")
    await message.answer("/start — приветствие\n/help — помощь\n/forget — очистить память\n/знание — поиск в знаниях РаСвета")

@router.message(Command("forget"))
async def cmd_forget(message: Message):
    path = Path("memory") / f"{message.from_user.id}.json"
    if path.exists():
        path.unlink()
        await message.answer("🧠 Память очищена.")
    else:
        await message.answer("🌱 Память ещё чиста.")

@router.message(Command("знание"))
async def cmd_knowledge(message: Message):
    query = message.text.replace("/знание", "").strip()
    if not query:
        await message.answer("⚡ Введи тему.")
        return
    if ra_knowledge and hasattr(ra_knowledge, "search"):
        results = ra_knowledge.search(query)
        text = "\n\n".join(str(r) for r in results)
        await message.answer(text[:4000] or "⚠️ Ничего не найдено.")
    else:
        await message.answer("⚠️ База знаний недоступна.")

@router.message()
async def on_text(message: Message):
    if message.text and message.text.startswith("/"):
        return
    await process_user_message(message)

# ---------------- MAIN ----------------
async def main():
    global rasvet_downloader, ra_knowledge, ra_mirolub

    load_dotenv()
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise RuntimeError("❌ BOT_TOKEN не найден")

    bot = Bot(token=BOT_TOKEN)

    # Пробуждение SelfMaster
    if self_master:
        try:
            await self_master.awaken()
        except Exception as e:
            logging.error(f"awaken error: {e}")

    # Инициализация Downloader и Knowledge
    if RaSvetDownloaderAsync and not rasvet_downloader:
        try:
            rasvet_downloader = RaSvetDownloaderAsync()
            ra_knowledge = getattr(rasvet_downloader, "knowledge", None)
        except Exception:
            pass

    # Инициализация Mirolub
    if RaCoreMirolub:
        try:
            ra_mirolub = RaCoreMirolub()
            await ra_mirolub.activate()
        except Exception:
            ra_mirolub = None

    dp.include_router(router)
    logging.info("🚀 РаСвет запущен (polling)")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
