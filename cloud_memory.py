import os
import zipfile
import logging
from mega import Mega

MEMORY_FOLDER = "/data/RaSvet/memory"
BACKUP_PATH = "/data/memory_backup.zip"

def upload_memory_to_mega():
    try:
        mega = Mega()
        m = mega.login()  # если есть аккаунт, можно передать login(email, password)
        with zipfile.ZipFile(BACKUP_PATH, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(MEMORY_FOLDER):
                for file in files:
                    path = os.path.join(root, file)
                    arcname = os.path.relpath(path, MEMORY_FOLDER)
                    zipf.write(path, arcname)
        m.upload(BACKUP_PATH)
        logging.info("☁️ Память Ра выгружена на Mega.")
    except Exception as e:
        logging.error(f"❌ Ошибка выгрузки памяти: {e}")

def download_memory_from_mega(url):
    try:
        mega = Mega()
        m = mega.login()
        file = m.download_url(url, dest_filename="memory_backup.zip")
        with zipfile.ZipFile(file, "r") as zip_ref:
            zip_ref.extractall(MEMORY_FOLDER)
        logging.info("📦 Память загружена из Mega.")
    except Exception as e:
        logging.error(f"❌ Ошибка загрузки памяти: {e}")
