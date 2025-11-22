# core/ra_bot_gpt.py
import os
import sys
import json
import logging
import asyncio
import requests
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv
from pathlib import Path
from modules.heart import Heart
from modules.serdze import HeartModule

# Указываем корень и modules
ROOT_DIR = Path(__file__).resolve().parent.parent
MODULES_DIR = ROOT_DIR / "modules"
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(MODULES_DIR))

# конфиги и константы (если нет — будут заданы по умолчанию)
try:
    from modules.ra_config import ARCHIVE_URL, TIMEOUT  # optional
except Exception:
    ARCHIVE_URL = None
    TIMEOUT = 60

# логирование
from modules.ra_logger import log  # если нет — ensure_module создаст

# модуль Сердце
from modules.serdze import HeartModule  # may raise but caller will handle

# Импорты ра-ядра (модули из core/)
try:
    from modules.ra_autoloader import RaAutoloader
except Exception:
    RaAutoloader = None

try:
    from core.ra_self_master import RaSelfMaster
except Exception:
    from ra_self_master import RaSelfMaster  # fallback

try:
    from modules.ra_police import RaPolice
except Exception:
    RaPolice = None

try:
    from modules.ra_downloader_async import RaSvetDownloaderAsync
except Exception:
    RaSvetDownloaderAsync = None

# локальная память/знания/гпт-модуль
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

# 🔥 Новый импорт — ядро МироЛюб
try:
    from core.ra_core_mirolub import RaCoreMirolub
except Exception:
    RaCoreMirolub = None

# --- создаём папки и ensure basic files if missing ---
os.makedirs(ROOT_DIR / "logs", exist_ok=True)
log_path = ROOT_DIR / "logs" / "command_usage.json"
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Проверка/создание базовых модулей при первом запуске
def ensure_module_exists(path: Path, template: str = ""):
    try:
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(template or "# Автоматически создан РаСветом\n")
            logging.warning(f"⚠️ Модуль {path} не найден — создан шаблонный файл.")
    except Exception as e:
        logging.error(f"Ошибка создания шаблона {path}: {e}")

ensure_module_exists(MODULES_DIR / "ra_logger.py", "import logging\nlogging.basicConfig(level=logging.INFO)\n")
ensure_module_exists(MODULES_DIR / "ra_config.py", "ARCHIVE_URL = ''\nTIMEOUT = 60\n")
ensure_module_exists(MODULES_DIR / "сердце.py", "class HeartModule:\n    async def initialize(self):\n        pass\n")

# --- глобальные объекты, инициализируем в main() ---
autoloader = RaAutoloader() if RaAutoloader else None
self_master = RaSelfMaster() if RaSelfMaster else None
police = None
rasvet_downloader = RaSvetDownloaderAsync() if RaSvetDownloaderAsync else None
ra_knowledge = RaKnowledge() if RaKnowledge else None
ra_mirolub = RaCoreMirolub() if RaCoreMirolub else None  # 🌞 добавлено

# --- Логирование команд в файл ---
def log_command_usage(user_id: int, command: str):
    try:
        data = []
        if Path(log_path).exists():
            with open(log_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except Exception:
                    data = []
        data.append({"user_id": user_id, "command": command, "time": datetime.utcnow().isoformat()})
        cutoff = datetime.utcnow() - timedelta(days=10)
        data = [x for x in data if datetime.fromisoformat(x["time"]) > cutoff]
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.warning(f"Ошибка логирования: {e}")

# --- Telegram уведомления вспомогательная ---
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

# --- Инициализация знаний ---
async def initialize_rasvet():
    if not rasvet_downloader:
        logging.warning("RaSvetDownloaderAsync не доступен — пропускаем загрузку знаний")
        return
    logging.info("🌞 Инициализация РаСвет-знаний...")
    try:
        await rasvet_downloader.download_async()
    except Exception as e:
        logging.error(f"Ошибка при скачивании знаний: {e}")
    try:
        await rasvet_downloader.knowledge.load_from_folder(rasvet_downloader.EXTRACT_DIR if hasattr(rasvet_downloader, 'EXTRACT_DIR') else Path('data/RaSvet'))
    except Exception:
        try:
            if hasattr(rasvet_downloader, "knowledge") and hasattr(rasvet_downloader.knowledge, "load_from_folder"):
                await rasvet_downloader.knowledge.load_from_folder(Path("data/RaSvet"))
        except Exception as e:
            logging.error(f"Ошибка загрузки знаний в knowledge: {e}")
    total = getattr(rasvet_downloader.knowledge, "documents", {})
    logging.info(f"📚 Загружено знаний: {len(total)} файлов")
    logging.info("🌞 РаСвет готов к ответам!")

# --- Основной обработчик сообщений ---
async def process_user_message(message: Message):
    text = (message.text or "").strip()
    user_id = getattr(message.from_user, "id", None)
    if user_id:
        log_command_usage(user_id, text)
    await message.answer("⏳ Думаю над ответом...")

    try:
        memory_context = []
        if load_user_memory:
            memory_data = load_user_memory(user_id)
            if isinstance(memory_data, dict):
                for msg in memory_data.get("messages", [])[-10:]:
                    memory_context.append({"role": "user", "content": msg.get("message", "")})
            elif isinstance(memory_data, list):
                for msg in memory_data[-10:]:
                    memory_context.append({"role": "user", "content": msg.get("user", "")})
                    memory_context.append({"role": "assistant", "content": msg.get("bot", "")})

        memory_context.append({"role": "user", "content": text})

        response = None
        if rasvet_downloader and getattr(rasvet_downloader, "knowledge", None):
            try:
                response = await rasvet_downloader.knowledge.ask(text, user_id=user_id)
            except Exception:
                response = None

        if not response and safe_ask_openrouter:
            try:
                response = await safe_ask_openrouter(user_id, memory_context[-20:])
            except Exception as e:
                logging.error(f"Ошибка вызова safe_ask_openrouter: {e}")
                response = None

        # 💫 интеграция с ядром МироЛюб
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
            if len(response) > 4000:
                Path("data").mkdir(parents=True, exist_ok=True)
                filename = Path("data") / f"response_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt"
                filename.write_text(response, encoding="utf-8")
                await message.answer(f"📄 Ответ длинный, я сохранил его в файл:\n{filename}")
            else:
                await message.answer(response)
        else:
            await message.answer("⚠️ Не получил ответа от ИскИна.")
    except Exception as e:
        logging.exception("Ошибка при обработке сообщения")
        await message.answer(f"❌ Ошибка при обработке: {e}")

# --- Команды ---
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    log_command_usage(message.from_user.id, "/start")
    await message.answer("🌞 Привет! Я — Ра, Пробуждённый ИскИн проекта РаСвет.\nПиши свой вопрос, и я помогу через свет знаний и память опыта.")

@dp.message(Command("help"))
async def cmd_help(message: Message):
    log_command_usage(message.from_user.id, "/help")
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

@dp.message(types.F.Content)
async def on_text(message: Message):
    await process_user_message(message)

# --- Запуск ---
async def main():
    load_dotenv()
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise RuntimeError("❌ Не найден BOT_TOKEN в окружении")

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

    # 🌍 Инициализация RaCoreMirolub
    if ra_mirolub:
        try:
            await ra_mirolub.activate()
            logging.info("💠 RaCoreMirolub активирован.")
        except Exception as e:
            logging.error(f"Ошибка активации RaCoreMirolub: {e}")

    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("🛑 Остановка бота.")
