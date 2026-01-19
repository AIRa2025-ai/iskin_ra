# core/telegram_sender.py
import logging
from core.ra_bot_gpt import bot

async def send_message(chat_id: int, text: str):
    try:
        await bot.send_message(chat_id, text)
    except Exception as e:
        logging.error(f"[TelegramSender] Ошибка отправки: {e}")

async def send_admin(text: str):
    ADMIN_CHAT_ID = 5694569448  # твой Telegram ID
    await send_message(ADMIN_CHAT_ID, text)
