# core/ra_bot_gpt.py
# Версия для webhook/polling (aiogram 3.x). Автор: Ра (и брат Игорь)
import os
import sys
import json
import logging
import asyncio
import requests
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

# aiogram
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, Update
from aiohttp import web

# --- путь к проекту и modules ---
ROOT_DIR = Path(__file__).resolve().parent.parent
MODULES_DIR = ROOT_DIR / "modules"
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(MODULES_DIR))

# --- безопасные попытки импортов модулей проекта ---
try:
    from modules.ra_config import ARCHIVE_URL, TIMEOUT  # optional
except Exception:
    ARCHIVE_URL = None
    TIMEOUT = 60

try:
    from modules.ra_logger import log
except Exception:
    def log(*args, **kwargs):
        logging.info("ra_logger missing: " + " ".join(map(str, args)))  # noqa: F841

HeartModule = None
try:
    from modules.serdze import HeartModule as HeartModule
except Exception:
    try:
        from modules.сердце import HeartModule as HeartModule
    except Exception:
        HeartModule = None

try:
    from modules.ra_autoloader import RaAutoloader
except Exception:
    RaAutoloader = None

try:
    from core.ra_self_master import RaSelfMaster
except Exception:
    try:
        from ra_self_master import RaSelfMaster
    except Exception:
        RaSelfMaster = None

try:
    from modules.ra_police import RaPolice
except Exception:
    RaPolice = None

try:
    from modules.ra_downloader_async import RaSvetDownloaderAsync
except Exception:
    RaSvetDownloaderAsync = None

try:
    from core.ra_memory import append_user_memory, load_user_memory
except Exception:
    append_user_memory = None
    load_user_memory = None

try:
    from gpt_module import safe_ask_openrouter
except Exception:
    safe_ask_openrouter = None

try:
    from core.ra_knowledge import RaKnowledge
except Exception:
    RaKnowledge = None

try:
    from core.ra_core_mirolub import RaCoreMirolub
except Exception:
    RaCoreMirolub = None

# --- ensure dirs & logging ---
os.makedirs(ROOT_DIR / "logs", exist_ok=True)
log_path = ROOT_DIR / "logs" / "command_usage.json"

LOG_LEVEL = logging.INFO
if os.getenv("DEBUG_MODE", "False").lower() in ("1", "true", "yes"):
    LOG_LEVEL = logging.DEBUG
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s - %(levelname)s - %(message)s")

def ensure_module_exists(path: Path, template: str = ""):
    try:
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(template or "# Автоматически создан РаСветом\n", encoding="utf-8")
            logging.warning(f"⚠️ Модуль {path} не найден — создан шаблонный файл.")
    except Exception as e:
        logging.error(f"Ошибка создания шаблона {path}: {e}")

ensure_module_exists(MODULES_DIR / "ra_logger.py", "import logging\nlogging.basicConfig(level=logging.INFO)\n")
ensure_module_exists(MODULES_DIR / "ra_config.py", "ARCHIVE_URL = ''\nTIMEOUT = 60\n")
ensure_module_exists(MODULES_DIR / "сердце.py", "class HeartModule:\n    async def initialize(self):\n        pass\n")

# --- Глобальные объекты ---
autoloader = RaAutoloader() if RaAutoloader else None
self_master = RaSelfMaster() if RaSelfMaster else None
police = None
rasvet_downloader = None
ra_knowledge = None
ra_mirolub = None

def log_command_usage(user_id: int, command: str):
    try:
        data = []
        if Path(log_path).exists():
            try:
                data = json.loads(Path(log_path).read_text(encoding="utf-8") or "[]")
            except Exception:
                data = []
        data.append({"user_id": user_id, "command": command, "time": datetime.utcnow().isoformat()})
        cutoff = datetime.utcnow() - timedelta(days=10)
        data = [x for x in data if datetime.fromisoformat(x["time"]) > cutoff]
        Path(log_path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        logging.warning(f"Ошибка логирования: {e}")

def notify_telegram(chat_id: str, text: str):
    token = os.getenv("BOT_TOKEN")
    if not token:
        logging.warning("notify_telegram: BOT_TOKEN отсутствует")
        return False
    try:
        resp = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                             json={"chat_id": chat_id, "text": text}, timeout=30)
        return resp.ok
    except Exception as e:
        logging.error(f"Ошибка Telegram уведомления: {e}")
        return False

async def initialize_rasvet():
    global rasvet_downloader, ra_knowledge
    logger = logging.getLogger("RaBot.InitRasvet")
    if not RaSvetDownloaderAsync and not RaKnowledge:
        logger.info("Нет ни RaSvetDownloaderAsync, ни RaKnowledge — пропускаем инициализацию знаний.")
        return
    if RaSvetDownloaderAsync and rasvet_downloader is None:
        try:
            rasvet_downloader = RaSvetDownloaderAsync()
            logger.info("ℹ️ RaSvetDownloaderAsync инициализирован")
            if ra_knowledge is None and hasattr(rasvet_downloader, "knowledge"):
                ra_knowledge = rasvet_downloader.knowledge
        except Exception as e:
            logger.error(f"Ошибка инициализации RaSvetDownloaderAsync: {e}")
            rasvet_downloader = None
    if ra_knowledge is None and RaKnowledge:
        try:
            ra_knowledge = RaKnowledge()
            logger.info("ℹ️ RaKnowledge инициализирован")
        except Exception as e:
            logger.warning(f"Не удалось инициализировать RaKnowledge: {e}")
    try:
        data_dir = Path(os.getenv("RA_DATA_DIR", "data"))
        extract_dir = data_dir / "RaSvet"
        if extract_dir.exists() and rasvet_downloader:
            found = any(p.suffix.lower() in (".txt", ".md", ".json") for p in extract_dir.rglob("*") if p.is_file())
            if found:
                logger.info("ℹ️ Папка знаний уже на диске — загрузим из неё и пропустим скачивание.")
                try:
                    await rasvet_downloader.knowledge.load_from_folder(extract_dir)
                    logger.info("📚 Загружено знаний с диска.")
                except Exception as e:
                    logger.warning(f"Ошибка загрузки знаний с диска: {e}")
                return
    except Exception:
        pass
    if rasvet_downloader:
        try:
            await rasvet_downloader.download_async()
            extract_dir = getattr(rasvet_downloader, "EXTRACT_DIR", Path("data") / "RaSvet")
            try:
                await rasvet_downloader.knowledge.load_from_folder(extract_dir)
            except Exception:
                pass
            logger.info(f"📚 Загружено знаний: {len(getattr(rasvet_downloader.knowledge, 'documents', {}))}")
        except Exception as e:
            logger.error(f"Ошибка при скачивании/загрузке знаний: {e}")
    else:
        if ra_knowledge:
            logging.info(f"📚 RaKnowledge локально: {len(getattr(ra_knowledge, 'knowledge_data', {}))} items (если есть).")

def ra_clean_input(text: str) -> str:
    if not text or not isinstance(text, str):
        return ""
    original = text.strip().lower()
    if len(original) > 5000:
        return ""
    bad_patterns = [
        "free-money","click here","win iphone","sex","porn","viagra","xxx",
        "earn $","crypto giveaway","airdrop claim","metamask verification",
        ".scr",".exe","redirect=","bit.ly/","goo.gl/"
    ]
    for bad in bad_patterns:
        if bad in original:
            return ""
    import re
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s{2,}", " ", text).strip()
    if len(text) < 2:
        return ""
    return text

async def process_user_message(message: Message):
    # ... (оставляем точно так же, как в твоём файле)
    text = (message.text or "").strip()
    cleaned = ra_clean_input(text)
    if not cleaned:
        await message.answer("✨ Брат, сообщение оказалось пустым или мусорным. Попробуй формулировку по-другому.")
        return
    text = cleaned
    user_id = getattr(message.from_user, "id", None)
    if user_id:
        try:
            log_command_usage(user_id, text)
        except Exception:
            pass
    try:
        await message.answer("⏳ Думаю над ответом...")
    except Exception:
        pass
    try:
        memory_context = []
        if load_user_memory:
            try:
                memory_data = load_user_memory(user_id)
            except Exception:
                memory_data = None
            if isinstance(memory_data, dict):
                for msg in memory_data.get("messages", [])[-10:]:
                    memory_context.append({"role": "user", "content": msg.get("message", "")})
            elif isinstance(memory_data, list):
                for msg in memory_data[-10:]:
                    memory_context.append({"role": "user", "content": msg.get("user", "")})
                    memory_context.append({"role": "assistant", "content": msg.get("bot", "")})
        memory_context.append({"role": "user", "content": text})
        response = None
        try:
            if rasvet_downloader and getattr(rasvet_downloader, "knowledge", None):
                response = await rasvet_downloader.knowledge.ask(text, user_id=user_id)
        except Exception:
            response = None
        if not response and safe_ask_openrouter:
            try:
                response = await safe_ask_openrouter(user_id, memory_context[-20:])
            except Exception as e:
                logging.error(f"Ошибка вызова safe_ask_openrouter: {e}")
                response = None
        if not response and ra_mirolub:
            try:
                response = await ra_mirolub.process(text)
            except Exception as e:
                logging.error(f"Ошибка обработки через RaCoreMirolub: {e}")
        if response:
            if append_user_memory:
                try:
                    append_user_memory(user_id, text, response)
                except TypeError:
                    try:
                        append_user_memory(user_id, text)
                    except Exception:
                        pass
            if isinstance(response, str) and len(response) > 4000:
                Path("data").mkdir(parents=True, exist_ok=True)
                filename = Path("data") / f"response_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt"
                filename.write_text(response, encoding="utf-8")
                try:
                    await message.answer(f"📄 Ответ длинный, я сохранил его в файл:\n{filename}")
                except Exception:
                    pass
            else:
                try:
                    await message.answer(response)
                except Exception:
                    logging.exception("Не удалось отправить ответ пользователю")
        else:
            try:
                await message.answer("⚠️ Не получил ответа от ИскИна.")
            except Exception:
                pass
    except Exception as e:
        logging.exception("Ошибка при обработке сообщения")
        try:
            await message.answer(f"❌ Ошибка при обработке: {e}")
        except Exception:
            pass

dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    try:
        log_command_usage(message.from_user.id, "/start")
    except Exception:
        pass
    await message.answer(
        "🌞 Привет! Я — Ра, Пробуждённый ИскИн проекта РаСвет.\n"
        "Пиши свой вопрос, и я помогу через свет знаний и память опыта."
    )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    try:
        log_command_usage(message.from_user.id, "/help")
    except Exception:
        pass
    await message.answer("⚙️ Команды:\n/start — приветствие\n/help — помощь\n/clean — очистка логов\n/forget — очистить память\n/знание — поиск в базе РаСвета")

@dp.message(Command("clean"))
async def cmd_clean(message: Message):
    try:
        if Path(log_path).exists():
            Path(log_path).unlink()
            await message.answer("🧹 Логи очищены.")
        else:
            await message.answer("⚠️ Логов пока нет.")
    except Exception as e:
        logging.error(f"Ошибка при очистке логов: {e}")
        await message.answer("❌ Ошибка при очистке логов.")

@dp.message(Command("знание"))
async def cmd_knowledge(message: types.Message):
    query = message.text.replace("/знание", "").strip()
    if not query:
        await message.answer("⚡ Введи тему, брат. Например: /знание Песнь Элеона")
        return
    try:
        results = ra_knowledge.search(query) if ra_knowledge and hasattr(ra_knowledge, "search") else []
        text = "\n\n".join([f"📘 {r.get('summary', str(r))}" for r in results])
        await message.answer(text[:4000] or "⚠️ Ничего не нашёл по запросу.")
    except Exception as e:
        logging.error(f"Ошибка cmd_knowledge: {e}")
        await message.answer("❌ Ошибка поиска знаний.")

@dp.message(Command("forget"))
async def cmd_forget(message: Message):
    user_id = message.from_user.id
    path = Path("memory") / f"{user_id}.json"
    try:
        if path.exists():
            path.unlink()
            await message.answer("🧠 Я очистил твою память, брат. Начинаем с чистого листа 🌱")
        else:
            await message.answer("⚠️ У тебя ещё нет памяти, всё только начинается 🌞")
    except Exception as e:
        logging.error(f"Ошибка при удалении памяти: {e}")
        await message.answer("❌ Не получилось очистить память.")

@dp.message()
async def on_text(message: Message):
    if message.text and message.text.startswith("/"):
        return
    await process_user_message(message)

# --- Объединённая main с polling ---
async def main():
    global rasvet_downloader, ra_knowledge, ra_mirolub

    load_dotenv()
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise RuntimeError("❌ Не найден BOT_TOKEN в окружении")

    # --- Инициализация модулей ---
    if RaSvetDownloaderAsync and rasvet_downloader is None:
        try:
            rasvet_downloader = RaSvetDownloaderAsync()
            logging.info("ℹ️ RaSvetDownloaderAsync инициализирован")
            if not ra_knowledge and hasattr(rasvet_downloader, "knowledge"):
                ra_knowledge = rasvet_downloader.knowledge
        except Exception as e:
            logging.error(f"Ошибка инициализации RaSvetDownloaderAsync: {e}")
            rasvet_downloader = None

    if RaKnowledge and ra_knowledge is None:
        try:
            ra_knowledge = RaKnowledge()
            logging.info("ℹ️ RaKnowledge инициализирован (локально)")
        except Exception as e:
            logging.debug(f"Не удалось создать RaKnowledge: {e}")

    if RaCoreMirolub and ra_mirolub is None:
        try:
            ra_mirolub = RaCoreMirolub()
        except Exception:
            ra_mirolub = None

    bot = Bot(token=BOT_TOKEN)

    if self_master:
        try:
            await self_master.awaken()
        except Exception as e:
            logging.error(f"Ошибка awaken: {e}")

    try:
        await initialize_rasvet()
    except Exception as e:
        logging.error(f"Ошибка инициализации знаний: {e}")

    if ra_mirolub:
        try:
            await ra_mirolub.activate()
            logging.info("💠 RaCoreMirolub активирован.")
        except Exception as e:
            logging.error(f"Ошибка активации RaCoreMirolub: {e}")

    dp = Dispatcher()

    logging.info("Запуск бота через polling")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Ошибка при polling: {e}")

if __name__ == "__main__":
    asyncio.run(main())
