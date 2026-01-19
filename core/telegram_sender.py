import logging
from core.ra_bot_gpt import bot

async def send_message(chat_id, text):
    try:
        await bot.send_message(chat_id, text)
    except Exception as e:
        logging.error(f"[TelegramSender] Ошибка отправки: {e}")

if "евро" in text.lower():
    from modules.ra_forex_manager import forex_manager
    signal = forex_manager.get_signal("EURUSD")
    await bot.send_message(chat_id, f"📊 EURUSD: {signal}")
