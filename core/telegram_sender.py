import logging
from aiogram import Bot

async def send_message(chat_id: int, text: str, bot: Bot):
    """Отправка сообщения в любой чат через переданный объект Bot"""
    try:
        await bot.send_message(chat_id, text)
    except Exception as e:
        logging.error(f"[TelegramSender] Ошибка отправки: {e}")

async def send_admin(text: str, bot: Bot):
    """Отправка сообщения администратору"""
    ADMIN_CHAT_ID = 5694569448  # твой Telegram ID
    await send_message(ADMIN_CHAT_ID, text, bot)
