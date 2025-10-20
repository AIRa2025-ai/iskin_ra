# run_bot.py — автоперезапуск бота при сбое
import subprocess
import time
from scripts.update_modules import MODULES_DIR
from utils.mega_memory import restore_from_mega, backup_to_mega
import threading

while True:
    try:
        # Перед каждым запуском обновляем модули
        subprocess.run(["python", "/app/scripts/update_modules.py"], check=True)
        
        # Запускаем бота
        print("Запуск бота Ра...")
        subprocess.run(["python", "core/ra_bot_gpt.py"], check=True)
   except Exception as e:
       print(f"Бот упал с ошибкой: {e}, перезапуск через 5 секунд...")
       with open("/app/logs/bot_errors.log", "a") as f:
           f.write(f"{time.ctime()}: {e}\n")
       time.sleep(5)
