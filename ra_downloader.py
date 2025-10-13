import os
import zipfile
import time
from mega import Mega
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RaSvetDownloader")

ARCHIVE_URL = "https://mega.nz/file/514XQRRA#ppfZArsPd8dwq08sQBJTx4w4BRo-nr4ux_KNM3C44B0"
LOCAL_ZIP = "/data/RaSvet.zip"
EXTRACT_DIR = "/data/RaSvet"
EXTRACT_META = "/data/RaSvet.extract.meta"

os.makedirs(EXTRACT_DIR, exist_ok=True)

m = Mega()
m.login()  # анонимный логин

# --- Скачивание файла напрямую по ссылке ---
def download_file(url, local_path):
    if os.path.exists(local_path):
        logger.info(f"Файл {local_path} уже существует, пропускаем скачивание")
        return

    logger.info("📥 Начинаем скачивание архива...")
    m.download_url(url, dest_filename=local_path)
    logger.info("✅ Архив скачан полностью")

download_file(ARCHIVE_URL, LOCAL_ZIP)

# --- Распаковка с прогрессом ---
extracted_files = set()
if os.path.exists(EXTRACT_META):
    with open(EXTRACT_META, "r") as f:
        extracted_files = set(line.strip() for line in f if line.strip())

logger.info("📂 Начинаем распаковку архива...")

with zipfile.ZipFile(LOCAL_ZIP, 'r') as zip_ref:
    for member in zip_ref.infolist():
        if member.filename in extracted_files:
            continue
        zip_ref.extract(member, EXTRACT_DIR)
        logger.info(f"Распакован файл: {member.filename}")
        extracted_files.add(member.filename)
        # сохраняем прогресс после каждого файла
        with open(EXTRACT_META, "w") as f:
            for fname in extracted_files:
                f.write(fname + "\n")
        time.sleep(0.05)

logger.info("✅ Архив полностью распакован! Все файлы на месте.")
