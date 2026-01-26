# utils/memory_sync.py

import logging
import subprocess
import os
from datetime import datetime

GIT_REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def sync_to_github(commit_message=None):
    if commit_message is None:
        commit_message = f"Auto memory update: {datetime.utcnow().isoformat()}"

    try:
        subprocess.run(["git", "add", "memory"], cwd=GIT_REPO_DIR, check=True)
        subprocess.run(["git", "commit", "-m", commit_message], cwd=GIT_REPO_DIR, check=True)
        subprocess.run(["git", "push"], cwd=GIT_REPO_DIR, check=True)
        logging.info("☁️ Память синхронизирована с Git")
    except subprocess.CalledProcessError:
        logging.info("ℹ️ Нет изменений для коммита")
    except Exception as e:
        logging.error(f"❌ Ошибка Git sync: {e}")
