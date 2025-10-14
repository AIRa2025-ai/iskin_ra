import logging
import subprocess
import os
from datetime import datetime

# Можно хранить токен в переменной окружения
GIT_REPO_DIR = os.path.dirname(os.path.abspath(__file__))  # текущая папка

def sync_to_github(commit_message=None):
    if commit_message is None:
        commit_message = f"Auto memory update: {datetime.utcnow().isoformat()}"

    try:
        # Добавляем все изменения
        subprocess.run(["git", "add", "."], cwd=GIT_REPO_DIR, check=True)
        # Коммитим
        subprocess.run(["git", "commit", "-m", commit_message], cwd=GIT_REPO_DIR, check=True)
        # Пушим
        subprocess.run(["git", "push"], cwd=GIT_REPO_DIR, check=True)
        print(f"✅ Memory synced to Git: {commit_message}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git sync failed: {e}")
        logging.info("💾 Память Ра синхронизирована с GitHub")
    except Exception as e:
        logging.error(f"❌ Ошибка синхронизации памяти: {e}")
