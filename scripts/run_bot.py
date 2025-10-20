# scripts/run_bot.py — автоперезапуск бота при сбое + авто-синхронизация с Mega
import subprocess
import time
from scripts.update_modules import MODULES_DIR
from utils.mega_memory import restore_from_mega, start_auto_sync, log

def main_loop():
    while True:
        try:
            log("🔄 Обновление модулей перед запуском...")
            subprocess.run(["python", "/app/scripts/update_modules.py"], check=True)

            log("🧠 Восстановление памяти Ра из Mega...")
            restore_from_mega()

            log("🌐 Запуск авто-синхронизации памяти и логов...")
            start_auto_sync()  # запускает фоновые потоки и управляет ими сам

            log("🚀 Запуск бота Ра...")
            subprocess.run(["python", "core/ra_bot_gpt.py"], check=True)

        except Exception as e:
            err_msg = f"💥 Бот упал с ошибкой: {e}, перезапуск через 5 секунд..."
            log(err_msg)
            try:
                with open("/app/logs/bot_errors.log", "a", encoding="utf-8") as f:
                    f.write(f"{time.ctime()}: {e}\n")
            except Exception as log_error:
                log(f"⚠️ Не удалось записать лог ошибки: {log_error}")
            time.sleep(5)

if __name__ == "__main__":
    main_loop()
