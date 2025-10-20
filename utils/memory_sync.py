# utils/memory_sync.py
import logging
import subprocess
import os
from datetime import datetime

# Путь к корню репозитория
GIT_REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def sync_to_github(commit_message=None):
    """Синхронизация изменений проекта с GitHub."""
    if commit_message is None:
        commit_message = f"Auto memory update: {datetime.utcnow().isoformat()}"

    try:
        subprocess.run(["git", "add", "."], cwd=GIT_REPO_DIR, check=True)
        subprocess.run(["git", "commit", "-m", commit_message], cwd=GIT_REPO_DIR, check=True)
        subprocess.run(["git", "push"], cwd=GIT_REPO_DIR, check=True)
        print(f"✅ Memory synced to Git: {commit_message}")
        logging.info("💾 Память Ра синхронизирована с GitHub")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Git sync skipped or no changes: {e}")
    except Exception as e:
        logging.error(f"❌ Ошибка синхронизации памяти: {e}")
