import os
import zipfile
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message
from mega_downloader import download_mega_file  # библиотека mega-lite

# === Загружаем переменные окружения из .env ===
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CREATOR_IDS = [int(x) for x in os.getenv("CREATOR_IDS", "").split(",") if x.strip()]
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-r1-0528:free")
KNOWLEDGE_FOLDER = os.getenv("KNOWLEDGE_FOLDER", "knowledge")

# === Ссылка на Mega-архив с РаСвет ===
MEGA_LINK = "https://mega.nz/file/doh2zJaa#FZVAlLmNFKMnZjDgfJGvTDD1hhaRxCf2aTk6z6lnLro"

# === Подготовка папки знаний ===
def init_knowledge_folder():
    if os.path.isdir(KNOWLEDGE_FOLDER):
        print(f"📂 Папка знаний уже готова: {KNOWLEDGE_FOLDER}")
        return

    print("⬇️ Скачиваю архив RaSvet.zip с Mega...")
    temp_dir = ".temp_mega"
    os.makedirs(temp_dir, exist_ok=True)

    download_mega_file(MEGA_LINK, temp_dir)

    zip_path = os.path.join(temp_dir, "RaSvet.zip")
    if not os.path.exists(zip_path):
        raise FileNotFoundError("❌ Не найден RaSvet.zip после загрузки с Mega.")

    with zipfile.ZipFile(zip_path, "r") as zp:
        zp.extractall(KNOWLEDGE_FOLDER)

    print(f"✅ Папка знаний готова: {KNOWLEDGE_FOLDER}")

# === Telegram Bot ===
router = Router()

@router.message(F.text)
async def handle_message(message: Message):
    # Если пишет создатель — можно расширить функционал
    if message.from_user.id in CREATOR_IDS:
        await message.answer(f"🌞 Привет, родной!\nТы сказал: {message.text}")
    else:
        await message.answer(f"Ра говорит: {message.text}")

async def main():
    print("🚀 Ра запускается...")
    init_knowledge_folder()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    print("🌞 Ра готов говорить.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("🛑 Ра остановлен.")
