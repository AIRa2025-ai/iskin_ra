# core/ra_bot_gpt.py
import os
import sys
import json
import logging
import asyncio
import requests
import subprocess
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv

# === 🔧 Пути для Python и контейнера ===
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MODULES_DIR = os.path.join(ROOT_DIR, "modules")
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, MODULES_DIR)

# --- 🔄 Автообновление модулей с GitHub с дебагом ---
GITHUB_REPO = "https://github.com/YourUsername/RaSvetModules.git"

def update_modules():
    try:
        if os.path.exists(MODULES_DIR) and os.path.exists(os.path.join(MODULES_DIR, ".git")):
            result = subprocess.run(
                ["git", "-C", MODULES_DIR, "pull"], capture_output=True, text=True
            )
            if result.returncode == 0:
                logging.info(f"✅ Модули обновлены через git pull:\n{result.stdout}")
            else:
                logging.warning(f"⚠️ Ошибка git pull:\n{result.stderr}")
        else:
            result = subprocess.run(
                ["git", "clone", GITHUB_REPO, MODULES_DIR], capture_output=True, text=True
            )
            if result.returncode == 0:
                logging.info(f"✅ Модули клонированы с GitHub:\n{result.stdout}")
            else:
                logging.error(f"❌ Ошибка git clone:\n{result.stderr}")
    except Exception as e:
        logging.error(f"❌ Исключение при обновлении модулей: {e}")

update_modules()

# === 🧩 Создание недостающих модулей ===
def ensure_module_exists(path: str, template: str = ""):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(template or "# Автоматически создан РаСветом\n")
        logging.warning(f"⚠️ Модуль {path} не найден — создан шаблонный файл.")

ensure_module_exists(os.path.join(MODULES_DIR, "ra_logger.py"), "import logging\nlogging.basicConfig(level=logging.INFO)\n")
ensure_module_exists(os.path.join(MODULES_DIR, "ra_config.py"), "import os\nBOT_NAME = 'RaSvet'\n")

# --- Импорты Ра ---
from modules.ra_autoloader import RaAutoloader
from ra_self_master import RaSelfMaster
from modules.ra_police import RaPolice
from modules.ra_downloader_async import RaSvetDownloaderAsync
from core.ra_memory import append_user_memory, load_user_memory
from gpt_module import safe_ask_openrouter
from core.ra_knowledge import RaKnowledge

# --- Инициализация ---
ra_knowledge = RaKnowledge()
autoloader = RaAutoloader()
modules = autoloader.activate_modules()
self_master = RaSelfMaster()
police = RaPolice()

print(self_master.awaken())
print(autoloader.status())
print(police.status())

# --- Настройки ---
os.makedirs("logs", exist_ok=True)
log_path = "logs/command_usage.json"
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ Не найден BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Логирование команд ---
def log_command_usage(user_id: int, command: str):
    try:
        data = []
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        data.append({"user_id": user_id, "command": command, "time": datetime.now().isoformat()})
        cutoff = datetime.now() - timedelta(days=10)
        data = [x for x in data if datetime.fromisoformat(x["time"]) > cutoff]
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.warning(f"Ошибка логирования: {e}")

# --- Telegram уведомления ---
def notify_telegram(chat_id: str, text: str):
    token = os.getenv("BOT_TOKEN")
    if not token:
        return False
    try:
        resp = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                             json={"chat_id": chat_id, "text": text}, timeout=10)
        return resp.ok
    except Exception as e:
        logging.error(f"Ошибка Telegram уведомления: {e}")
        return False

# --- РаСвет база знаний ---
rasvet_downloader = RaSvetDownloaderAsync()

async def initialize_rasvet():
    logging.info("🌞 Инициализация РаСвет-знаний...")
    await rasvet_downloader.download_async()
    await rasvet_downloader.knowledge.load_all_texts()
    logging.info(f"📚 Загружено знаний: {len(rasvet_downloader.knowledge.documents)} файлов")
    logging.info("🌞 РаСвет готов к ответам!")

# --- Основной обработчик сообщений ---
async def process_user_message(message: Message):
    text = message.text.strip()
    user_id = message.from_user.id
    log_command_usage(user_id, text)
    await message.answer("⏳ Думаю над ответом...")

    try:
        memory_data = load_user_memory(user_id)
        memory_context = []

        if isinstance(memory_data, dict):
            for msg in memory_data.get("messages", [])[-10:]:
                memory_context.append({"role": "user", "content": msg.get("message", "")})
        elif isinstance(memory_data, list):
            for msg in memory_data[-10:]:
                memory_context.append({"role": "user", "content": msg.get("user", "")})
                memory_context.append({"role": "assistant", "content": msg.get("bot", "")})

        memory_context.append({"role": "user", "content": text})

        response = None
        if rasvet_downloader.knowledge.documents:
            response = await rasvet_downloader.knowledge.ask(text, user_id=user_id)

        if not response:
            response = await safe_ask_openrouter(user_id, memory_context[-20:])

        if response:
            append_user_memory(user_id, text, response)
            if len(response) > 4000:
                os.makedirs("data", exist_ok=True)
                filename = f"data/response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(response)
                await message.answer(f"📄 Ответ длинный, я сохранил его в файл:\n{filename}")
            else:
                await message.answer(response)
        else:
            await message.answer("⚠️ Не получил ответа от ИскИна.")
    except Exception as e:
        await message.answer(f"❌ Ошибка при обработке: {e}")

# --- Команды ---
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
    if os.path.exists(log_path):
        os.remove(log_path)
        await message.answer("🧹 Логи очищены.")
    else:
        await message.answer("⚠️ Логов пока нет.")

@dp.message(Command("знание"))
async def cmd_knowledge(message: types.Message):
    query = message.text.replace("/знание", "").strip()
    if not query:
        await message.answer("⚡ Введи тему, брат. Например: /знание Песнь Элеона")
        return
    results = ra_knowledge.search(query)
    text = "\n\n".join([f"📘 {r['summary']}" for r in results])
    await message.answer(text[:4000])

@dp.message(Command("forget"))
async def cmd_forget(message: Message):
    user_id = message.from_user.id
    path = os.path.join("memory", f"{user_id}.json")
    if os.path.exists(path):
        os.remove(path)
        await message.answer("🧠 Я очистил твою память, брат. Начинаем с чистого листа 🌱")
    else:
        await message.answer("⚠️ У тебя ещё нет памяти, всё только начинается 🌞")

@dp.message(F.text)
async def on_text(message: Message):
    await process_user_message(message)

# --- Запуск ---
async def main():
    logging.info("🚀 Бот Ра запущен и готов к общению.")
    await initialize_rasvet()
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("🛑 Остановка бота.")
