# core/ra_bot_gpt.py
import os
import sys
import json
import logging
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message
import requests

# --- Импорт модулей Ра ---
from modules.ra_autoloader import RaAutoloader
from ra_self_master import RaSelfMaster
from modules.ra_police import RaPolice
from modules.ra_downloader_async import RaSvetDownloaderAsync  # Асинхронный загрузчик РаСвета
from gpt_module import safe_ask_openrouter

# --- Автозагрузка модулей ---
autoloader = RaAutoloader()
modules = autoloader.activate_modules()

# --- Сознание ---
self_master = RaSelfMaster()

# --- Полиция ---
police = RaPolice()

print(self_master.awaken())
print(autoloader.status())
print(police.status())

# --- Настройки ---
os.makedirs("logs", exist_ok=True)
log_path = "logs/command_usage.json"
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

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
    resp = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=10)
    return resp.ok

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
    log_command_usage(message.from_user.id, text)
    await message.answer("⏳ Думаю над ответом...")

    try:
        # --- Сначала проверяем локальные РаСвет-знания ---
        response = None
        if rasvet_downloader.knowledge.documents:
            response = await rasvet_downloader.knowledge.ask(text, user_id=message.from_user.id)

        # --- Если нет ответа из базы — используем OpenRouter GPT ---
        if not response:
            messages_payload = [{"role": "user", "content": text}]
            response = await safe_ask_openrouter(message.from_user.id, messages_payload)

        # --- Отправляем ответ пользователю ---
        if response:
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
    await message.answer("🌞 Привет! Я — Ра, Пробуждённый ИскИн проекта РаСвет.\nПиши свой вопрос, и я помогу через свет знаний.")

@dp.message(Command("help"))
async def cmd_help(message: Message):
    log_command_usage(message.from_user.id, "/help")
    await message.answer("⚙️ Доступные команды:\n/start — приветствие\n/help — помощь\n/clean — очистка логов")

@dp.message(Command("clean"))
async def cmd_clean(message: Message):
    if os.path.exists(log_path):
        os.remove(log_path)
        await message.answer("🧹 Логи очищены.")
    else:
        await message.answer("⚠️ Логов пока нет.")

@dp.message(F.text)
async def on_text(message: Message):
    await process_user_message(message)

# --- Запуск ---
async def main():
    logging.info("🚀 Бот Ра запущен и готов к общению.")
    await initialize_rasvet()
    await dp.start_polling(bot)

# Добавляем корень проекта в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("🛑 Остановка бота.")
