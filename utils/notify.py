# utils/notify.py — уведомления через Telegram
import os
import requests
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def notify(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text = f"[{timestamp}] {msg}"
    print(text)  # выводим в консоль
    if not BOT_TOKEN or not CHAT_ID:
        print("⚠️ Telegram сикреты не настроены — уведомление пропущено")
        return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text})
    except Exception as e:
        print(f"⚠️ Не удалось отправить уведомление Telegram: {e}")
