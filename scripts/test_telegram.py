import os
from telegram import Bot

bot_token = os.getenv("TELEGRAM_TOKEN")  # или TELEGRAM_BOT_TOKEN
chat_id = os.getenv("CHAT_ID")

bot = Bot(token=bot_token)

try:
    bot.send_message(chat_id=chat_id, text="💫 Тест Телеграм RaSvet")
    print("Сообщение отправлено!")
except Exception as e:
    print("Ошибка отправки:", e)
