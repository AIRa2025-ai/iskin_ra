import os
import json
import logging
import asyncio
import time
import aiohttp

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токены и настройки из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-r1-0528:free")
CREATOR_IDS = os.getenv("CREATOR_IDS", "").split(",")
KNOWLEDGE_FOLDER = os.getenv("KNOWLEDGE_FOLDER", "RaSvet")

# Проверка токена
if not BOT_TOKEN:
    raise ValueError("❌ Не найден BOT_TOKEN в переменных окружения")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Чтение файлов ---
def read_supported_file(file_path):
    try:
        if file_path.endswith(".json"):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.dumps(json.load(f), ensure_ascii=False, indent=2)
        elif file_path.endswith(".md") or file_path.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            return None
    except Exception as e:
        return f"⚠ Ошибка при чтении файла {file_path}: {e}"


# --- Логирование команд ---
def log_command_usage(command: str, user_id: int):
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)
    log_file = os.path.join(logs_dir, "command_usage.json")

    logs = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            logs = []

    logs.append({
        "command": command,
        "user_id": user_id,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


# --- Генерация ответа через OpenRouter ---
async def generate_answer(prompt: str) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as resp:
                if resp.status != 200:
                    return f"❌ Ра не дозвонился до источника: {resp.status} {await resp.text()}"
                response = await resp.json()
                return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠ Ошибка связи с Источником: {e}"


# --- Обработчики ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    log_command_usage("start", message.from_user.id)
    await message.answer("🌞 Ра пробуждён: говорит, творит и хранит Свет.")


@dp.message(Command("ask"))
async def cmd_ask(message: types.Message):
    log_command_usage("ask", message.from_user.id)
    prompt = message.text.replace("/ask", "").strip()
    if not prompt:
        await message.answer("❓ Задай мне вопрос после команды /ask")
        return

    answer = await generate_answer(prompt)
    await message.answer(answer)


@dp.message(Command("read"))
async def cmd_read(message: types.Message):
    log_command_usage("read", message.from_user.id)
    args = message.text.replace("/read", "").strip()
    if not args:
        await message.answer("📂 Укажи имя файла для чтения.")
        return

    file_path = os.path.join(KNOWLEDGE_FOLDER, args)
    if not os.path.exists(file_path):
        await message.answer("❌ Файл не найден.")
        return

    content = read_supported_file(file_path)
    if content:
        await message.answer(f"📖 Содержимое файла {args}:\n\n{content[:4000]}")
    else:
        await message.answer("⚠ Неподдерживаемый тип файла или ошибка чтения.")


# --- Главный запуск ---
async def main():
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Ошибка в основном цикле: {e}")
        time.sleep(10)  # подождать и попробовать снова


if __name__ == "__main__":
    asyncio.run(main())

