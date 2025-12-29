import os
import asyncio
import json
import logging
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

IPC_HOST = "127.0.0.1"
IPC_PORT = 8765

async def send_to_core(user_id, message_text):
    try:
        reader, writer = await asyncio.open_connection(IPC_HOST, IPC_PORT)
        payload = json.dumps({"user_id": user_id, "message": message_text}, ensure_ascii=False)
        writer.write(payload.encode())
        await writer.drain()

        data = await reader.read(65536)
        writer.close()
        await writer.wait_closed()
        reply = json.loads(data.decode()).get("response", "⚠️ CORE молчит")
        return reply
    except Exception as e:
        logging.warning(f"[IPC Client] Ошибка: {e}")
        return "⚠️ Ошибка соединения с CORE"

async def process_message(message: Message):
    text = (message.text or "").strip()
    if not text:
        return
    reply = await send_to_core(message.from_user.id, text)
    await message.answer(reply)

dp = Dispatcher()
router = Router()

@router.message(Command("start"))
async def start_cmd(m: Message):
    await m.answer("🌞 Ра на связи. Пиши.")

@router.message()
async def all_text(m: Message):
    if m.text.startswith("/"):
        return
    await process_message(m)

async def main():
    bot = Bot(os.getenv("BOT_TOKEN"))
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
