import os
import zipfile
import asyncio
import sys
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message
from mega_downloader import download_mega_file

# === Загрузка переменных из .env ===
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CREATOR_IDS = [int(x) for x in os.getenv("CREATOR_IDS", "").split(",") if x.strip()]
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-r1-0528:free")
KNOWLEDGE_FOLDER = os.getenv("KNOWLEDGE_FOLDER", "knowledge")

print("=== Запуск Ра на Fly ===")
print(f"BOT_TOKEN: {BOT_TOKEN!r}")
print(f"CREATOR_IDS: {CREATOR_IDS}")
print(f"OPENROUTER_API_KEY: {bool(OPENROUTER_API_KEY)} (ключ {'задан' if OPENROUTER_API_KEY else 'НЕ задан'})")
print(f"MODEL: {MODEL!r}")
print(f"KNOWLEDGE_FOLDER: {KNOWLEDGE_FOLDER!r}")
print("========================")

# Если нет токена — сразу выходим с ошибкой
if not BOT_TOKEN:
    print("❌ BOT_TOKEN не задан! Установи переменные окружения через 'fly secrets set ...'")
    sys.exit(1)

# === Подготовка папки знаний ===
def init_knowledge_folder():
    if not os.path.isdir(KNOWLEDGE_FOLDER):
        print("⬇️ Скачиваю архив RaSvet.zip с Mega...")
        try:
            download_mega_file(
                "https://mega.nz/file/doh2zJaa#FZVAlLmNFKMnZjDgfJGvTDD1hhaRxCf2aTk6z6lnLro",
                ".temp_mega"
            )
            with zipfile.ZipFile(".temp_mega/RaSvet.zip", "r") as zp:
                zp.extractall(KNOWLEDGE_FOLDER)
            print(f"✅ Папка знаний готова: {KNOWLEDGE_FOLDER}")
        except Exception as e:
            print(f"❌ Ошибка при загрузке знаний: {e}")
            sys.exit(1)
    else:
        print(f"📂 Папка знаний уже есть: {KNOWLEDGE_FOLDER}")

# === Telegram Bot Setup ===
router = Router()

@router.message(F.text)
async def echo(message: Message):
    await message.answer("Ра говорит: " + message.text)

async def main():
    print("🚀 Ра запускается...")
    init_knowledge_folder()

    try:
        bot = Bot(token=BOT_TOKEN)
        dp = Dispatcher()
        dp.include_router(router)

        print("🌞 Ра готов говорить.")
        await dp.start_polling(bot)
    except Exception as e:
        print(f"❌ Ошибка при запуске бота: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
