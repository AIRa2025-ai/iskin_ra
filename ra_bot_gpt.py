# ra_bot_gpt.py — переписанный под чистый aiogram 3.x

import os
import json
import asyncio
import logging
import datetime
import shutil
import re
import difflib

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from gtts import gTTS
from aiogram.types import FSInputFile

from gpt_module import ask_gpt
from rasvet_context import load_rasvet_context
from memory import append_user_memory

# === Настройки ===
load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
KNOWLEDGE_FOLDER = json.load(open("bot_config.json", encoding="utf-8"))["knowledge_folder"]
CREATOR_ID = [5694569448, 6300409447]

# === Инициализация ===
bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

# === Логирование ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Утилиты ===
def clean_text(text):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>|[*_~^=#>\[\](){}]", "", text)).strip()

def get_folder_path(phrase):
    norm = lambda s: s.lower().replace("_", " ").replace("-", " ").strip()
    target = norm(phrase)
    best, score = None, 0
    for root, dirs, _ in os.walk(KNOWLEDGE_FOLDER):
        for d in dirs:
            ratio = difflib.SequenceMatcher(None, norm(d), target).ratio()
            if ratio > score:
                best, score = os.path.join(root, d), ratio
    return best if score > 0.7 else None

# === Голосовой отклик ===
async def send_voice(message: types.Message, text: str):
    try:
        tts = gTTS(text=clean_text(text), lang="ru")
        filename = f"response_{message.message_id}.ogg"
        tts.save(filename)
        await message.answer_voice(voice=FSInputFile(filename))
        os.remove(filename)
    except Exception as e:
        await message.answer(f"⚠️ Ошибка озвучки: {e}")

# === Роутер сообщений ===
@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("🌞 Ра приветствует тебя, брат!")

@router.message()
async def on_message(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()
    text_l = text.lower()

    logger.info(f"Ра услышал: {text}")

    # === Запрос к GPT ===
    try:
        response = await ask_gpt(str(user_id), text)
        await message.answer(response)
        await send_voice(message, response)
        await asyncio.sleep(1)
        await append_user_memory(user_id, text, response)
    except Exception as e:
        await message.answer(f"⚠️ Ошибка ИскИна: {e}")
        return

    # === Создание папки ===
    if "создай папку" in text_l:
        name = text_l.replace("создай папку", "").strip()
        path = os.path.join(KNOWLEDGE_FOLDER, name.replace(" ", "_"))
        try:
            os.makedirs(path, exist_ok=True)
            await message.answer(f"📁 Папка создана: {name}")
        except Exception as e:
            await message.answer(f"⚠️ Ошибка: {e}")

    # === Удаление папки ===
    elif "удали папку" in text_l:
        path = get_folder_path(text_l.replace("удали папку", "").strip())
        if path:
            shutil.rmtree(path)
            await message.answer("🗑 Папка удалена.")
        else:
            await message.answer("⚠️ Папка не найдена.")

    # === Прочитай файл ===
    elif "прочитай" in text_l:
        phrase = text_l.replace("прочитай", "").strip()
        folder = get_folder_path(phrase)
        if folder:
            for f in os.listdir(folder):
                if f.endswith(".txt"):
                    with open(os.path.join(folder, f), encoding="utf-8") as file:
                        content = file.read(4000)
                        await message.answer(f"📖 {f}:
{content}")
                        return
        await message.answer("⚠️ Файл не найден.")

# === Точка входа ===
async def main():
    print("🚀 Ра запускается...")
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
