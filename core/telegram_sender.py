import logging
from core.ra_bot_gpt import bot

async def send_message(chat_id, text):
    try:
        await bot.send_message(chat_id, text)
    except Exception as e:
        logging.error(f"[TelegramSender] Ошибка отправки: {e}")
