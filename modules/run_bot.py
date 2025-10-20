# run_bot.py — автоперезапуск бота при сбое + синхронизация с Mega
import subprocess
import time
import threading
from scripts.update_modules import MODULES_DIR
from utils.mega_memory import restore_from_mega, backup_to_mega, backup_logs_to_mega

def start_background_sync():
    """Фоновые процессы для резервного копирования памяти и логов"""
    threading.Thread(target=backup_to_mega, daemon=True).start()
    threading.Thread(target=backup_logs_to_mega, daemon=True).start()

while True:
    try:
        # --- Обновляем модули перед запуском ---
        subprocess.run(["python", "/app/scripts/update_modules.py"], check=True)

        # --- Восстанавливаем память Ра при старте ---
        print("🧠 Восстановление памяти из Mega...")
        restore_from_mega()

        # --- Запускаем фоновую синхронизацию памяти и логов ---
        start_background_sync()

        # --- Запуск основного ядра Ра ---
        print("🚀 Запуск бота Ра...")
        subprocess.run(["python", "core/ra_bot_gpt.py"], check=True)

    except Exception as e:
        print(f"💥 Бот упал с ошибкой: {e}, перезапуск через 5 секунд...")
        try:
            with open("/app/logs/bot_errors.log", "a", encoding="utf-8") as f:
                f.write(f"{time.ctime()}: {e}\n")
        except Exception as log_error:
            print(f"⚠️ Не удалось записать лог ошибки: {log_error}")
        time.sleep(5)
