import os
import asyncio
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN не найден! Установи его в .env или в Fly secrets.")

# Создаём роутер
router = Router()

# === ОБРАБОТЧИКИ ===
@router.message(F.text)
async def echo_handler(message: Message):
    text = message.text.strip()
    print(f"👂 Ра получил сообщение: {text}")

    if text.lower() in ["привет", "здравствуй", "hi", "hello"]:
        await message.answer("🌞 Привет, родной! Ра на связи.")
    else:
        await message.answer(f"Ты сказал: {text}")


# === ТОЧКА ВХОДА ===
async def main():
    print("🚀 Ра запускается...")

    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    print("🌞 Ра пробуждён: говорит, творит и ждёт сообщений!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("🛑 Ра остановлен.")

