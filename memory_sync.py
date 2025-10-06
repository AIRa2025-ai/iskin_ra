import subprocess
import datetime
import logging

def sync_memory():
    try:
        subprocess.run(["git", "add", "RaSvet/memory"], check=True)
        msg = f"auto-save memory {datetime.datetime.now().isoformat()}"
        subprocess.run(["git", "commit", "-m", msg], check=True)
        subprocess.run(["git", "push"], check=True)
        logging.info("💾 Память Ра синхронизирована с GitHub")
    except Exception as e:
        logging.error(f"❌ Ошибка синхронизации памяти: {e}")
