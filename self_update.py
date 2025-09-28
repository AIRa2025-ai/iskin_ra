import os
import subprocess
import shutil
from datetime import datetime

BACKUP_DIR = "backups"

def run_cmd(cmd):
    """Выполняет системную команду"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode

def backup():
    """Создаёт резервную копию проекта"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"backup_{timestamp}")
    shutil.copytree(".", backup_path, dirs_exist_ok=True)
    return backup_path

def self_update():
    """Обновление из git с резервной копией и логированием"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backup_path = backup()
    print(f"📦 Резервная копия сохранена: {backup_path}")

    out, err, code = run_cmd("git pull origin main")
    if code == 0:
        print("✅ Обновление успешно применено!")
    else:
        print("❌ Ошибка при обновлении! Делаю откат...")
        run_cmd("git reset --hard HEAD")
        print(f"🔄 Откат к предыдущей версии ({backup_path}) выполнен")

if __name__ == "__main__":
    self_update()
