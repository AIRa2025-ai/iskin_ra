import os
import zipfile
import asyncio
from mega_downloader import download_mega_file  # нужна библиотека mega-lite
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message
from mega_downloader import download_mega_file

download_mega_file("https://mega.nz/file/doh2zJaa#FZVAlLmNFKMnZjDgfJGvTDD1hhaRxCf2aTk6z6lnLro", "./knowledge")

# === Загрузка переменных из .env ===
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CREATOR_IDS = [int(x) for x in os.getenv("CREATOR_ID", "").split(",") if x.strip()]
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("MODEL", "deepseek/deepseek-r1-0528:free")

# === Подготовка папки знаний ===
KNOWLEDGE_FOLDER = os.getenv("KNOWLEDGE_FOLDER", "knowledge")

def init_knowledge_folder():
    if not os.path.isdir(KNOWLEDGE_FOLDER):
        print("⬇️ Скачиваю архив RaSvet.zip с Mega...")
        download_mega_file(
            "https://mega.nz/file/doh2zJaa#FZVAlLmNFKMnZjDgfJGvTDD1hhaRxCf2aTk6z6lnLro",
            ".temp_mega"
        )
        with zipfile.ZipFile(".temp_mega/RaSvet.zip", "r") as zp:
            zp.extractall(KNOWLEDGE_FOLDER)
        print(f"✅ Папка знаний готова: {KNOWLEDGE_FOLDER}")

# === Telegram Bot Setup (straight aiogram 3.x) ===
router = Router()

@router.message(F.text)
async def echo(message: Message):
    await message.answer("Ра говорит: " + message.text)

async def main():
    print("🚀 Ра запускается...")
    init_knowledge_folder()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    print("🌞 Ра готов говорить.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

