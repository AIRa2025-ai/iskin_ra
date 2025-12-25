#===test_commands.py===
import asyncio
from core.ra_bot_gpt import dp, process_user_message
from aiogram.types import Message, User

class DummyMessage:
    def __init__(self, text, user_id):
        self.text = text
        self.from_user = User(id=user_id, is_bot=False, first_name="Тест")
    async def answer(self, text):
        print(f"Бот ответил: {text}")

async def test():
    # /start
    msg_start = DummyMessage("/start", 12345)
    await process_user_message(msg_start)

    # /help
    msg_help = DummyMessage("/help", 12345)
    await process_user_message(msg_help)

    # обычное сообщение
    msg_text = DummyMessage("Привет, Ра!", 12345)
    await process_user_message(msg_text)

asyncio.run(test())
