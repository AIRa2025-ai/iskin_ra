# self_update.py — обновление проекта с бэкапом, логами и мягким стартом
import os
import subprocess
import shutil
from datetime import datetime
import logging
import signal
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BACKUP_DIR = "backups"
QUIET_START_DELAY = 2
stop_flag = False  # для мягкого завершения

def signal_handler(signum, frame):
    global stop_flag
    logging.info(f"✋ Получен сигнал {signum}, подготовка к завершению...")
    stop_flag = True

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def run_cmd(cmd):
    """Выполняет системную команду"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def backup_file(file_path):
    """Создаёт резервную копию одного файла"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"{os.path.basename(file_path)}_{timestamp}.bak")
    try:
        shutil.copy2(file_path, backup_path)
        logging.info(f"📦 Файл {file_path} сохранён в бэкап: {backup_path}")
    except Exception as e:
        logging.error(f"❌ Не удалось сделать бэкап файла {file_path}: {e}")
        backup_path = None
    return backup_path

def backup():
    """Создаёт резервную копию всего проекта"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"full_backup_{timestamp}")
    try:
        shutil.copytree(".", backup_path, dirs_exist_ok=True)
        logging.info(f"📦 Полный бэкап проекта сохранён: {backup_path}")
    except Exception as e:
        logging.error(f"❌ Ошибка при создании полного бэкапа: {e}")
        backup_path = None
    return backup_path

def update_file(file_path, new_content: str):
    """Обновляет файл с созданием резервной копии"""
    backup = backup_file(file_path)
    if stop_flag:
        logging.info("✋ Обновление файла отменено (остановка инициирована).")
        return
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        logging.info(f"✅ Файл {file_path} обновлён, бэкап: {backup}")
    except Exception as e:
        logging.error(f"❌ Ошибка при обновлении файла {file_path}: {e}")
        if backup:
            shutil.copy2(backup, file_path)
            logging.info(f"🔄 Откат файла {file_path} к бэкапу выполнен")

def git_commit_and_push(msg="auto-update by Ra"):
    """Коммит и пуш в git"""
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", msg], check=True)
        subprocess.run(["git", "push"], check=True)
        logging.info("✅ Git commit & push успешно выполнены")
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Ошибка git: {e}")

def self_update():
    """Обновление проекта из git с резервной копией и логированием"""
    logging.info(f"⏳ Ждём {QUIET_START_DELAY}s перед обновлением...")
    time.sleep(QUIET_START_DELAY)

    if stop_flag:
        logging.info("✋ Обновление отменено (остановка инициирована).")
        return

    backup_path = backup()
    if stop_flag:
        logging.info("✋ Обновление отменено после бэкапа.")
        return

    out, err, code = run_cmd("git pull origin main")
    if code == 0:
        logging.info("✅ Обновление успешно применено!")
    else:
        logging.error(f"❌ Ошибка при обновлении: {err}")
        logging.info("🔄 Делаем откат к предыдущей версии...")
        if backup_path:
            try:
                for item in os.listdir(backup_path):
                    s = os.path.join(backup_path, item)
                    d = os.path.join(".", item)
                    if os.path.isdir(s):
                        shutil.rmtree(d, ignore_errors=True)
                        shutil.copytree(s, d)
                    else:
                        shutil.copy2(s, d)
                logging.info(f"🔄 Откат выполнен из бэкапа {backup_path}")
            except Exception as e:
                logging.error(f"❌ Не удалось сделать откат: {e}")
        run_cmd("git reset --hard HEAD")

if __name__ == "__main__":
    self_update()
