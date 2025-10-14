import requests
import os

# --- Настройки ---
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Твой токен бота
BOT_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
TEST_CHAT_ID = os.getenv("TEST_CHAT_ID")  # Твой телеграм ID для теста

def check_webhook():
    print("🔹 Проверяем webhook...")
    resp = requests.get(f"{BOT_URL}/getWebhookInfo").json()
    if resp.get("ok"):
        url = resp.get("result", {}).get("url", "")
        last_err = resp.get("result", {}).get("last_error_message")
        print(f"Webhook URL: {url}")
        print(f"Last error: {last_err or 'Нет ошибок'}")
    else:
        print("❌ Ошибка запроса webhook:", resp)

def send_test_message(text):
    print(f"🔹 Отправляем тестовое сообщение: {text}")
    resp = requests.post(f"{BOT_URL}/sendMessage", json={
        "chat_id": TEST_CHAT_ID,
        "text": text
    }).json()
    if resp.get("ok"):
        print("✅ Сообщение отправлено успешно")
    else:
        print("❌ Ошибка отправки сообщения:", resp)

def run_tests():
    check_webhook()

    # Проверяем команды бота
    commands = [
        "/whoami",
        "/дайджест",
        "/загрузи РаСвет",
        "Ра, что думаешь о файле тест.json"
    ]

    for cmd in commands:
        send_test_message(cmd)

    print("\n💡 Проверьте, что бот ответил в Телеграме на все сообщения.")

if __name__ == "__main__":
    run_tests()
