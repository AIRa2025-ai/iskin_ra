import os
import zipfile
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message
from gpt_module import ask_gpt
from memory import append_user_memory
from mega_downloader import download_mega_file

# === Загружаем переменные окружения ===
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
KNOWLEDGE_FOLDER = os.getenv("KNOWLEDGE_FOLDER", "knowledge")
CREATOR_IDS = [int(x) for x in os.getenv("CREATOR_IDS", "").split(",") if x.strip()]

# === Инициализация папки знаний ===
def init_knowledge_folder():
    if not os.path.isdir(KNOWLEDGE_FOLDER):
        print("⬇️ Скачиваю архив знаний с Mega...")
        download_mega_file(
            "https://mega.nz/file/doh2zJaa#FZVAlLmNFKMnZjDgfJGvTDD1hhaRxCf2aTk6z6lnLro",
            ".temp_mega"
        )
        with zipfile.ZipFile(".temp_mega/RaSvet.zip", "r") as zp:
            zp.extractall(KNOWLEDGE_FOLDER)
        print(f"✅ Папка знаний готова: {KNOWLEDGE_FOLDER}")
    else:
        print(f"📂 Папка знаний найдена: {KNOWLEDGE_FOLDER}")

# === Роутер aiogram ===
router = Router()

@router.message(F.text)
async def handle_message(message: Message):
    user_id = message.from_user.id
    user_input = message.text.strip()

    print(f"💬 Сообщение от {user_id}: {user_input}")

    reply = await ask_gpt(user_id, user_input)
    append_user_memory(user_id, user_input, reply)

    await message.answer(reply)

# === Запуск бота ===
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
