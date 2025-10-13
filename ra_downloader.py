import os
import zipfile
import time
from mega import Mega
import logging

logger = logging.getLogger("RaSvetDownloader")
logger.setLevel(logging.INFO)

ARCHIVE_URL = "https://mega.nz/file/514XQRRA#ppfZArsPd8dwq08sQBJTx4w4BRo-nr4ux_KNM3C44B0"
LOCAL_ZIP = "/data/RaSvet.zip"
EXTRACT_DIR = "/data/RaSvet"
EXTRACT_META = "/data/RaSvet.extract.meta"

class RaSvetDownloader:
    def download(self):
        print("Скачиваем данные РаСвета...")
        # сюда вставляешь реальный код загрузки

def download_and_extract_rasvet():
    os.makedirs(EXTRACT_DIR, exist_ok=True)
    
    # --- Mega login ---
    m = Mega()
    m.login()  # анонимно
    
    # --- Скачиваем только если файла нет или он пустой ---
    if not os.path.exists(LOCAL_ZIP) or os.path.getsize(LOCAL_ZIP) == 0:
        logger.info("📥 Начинаем скачивание архива...")
        m.download_url(ARCHIVE_URL, dest_filename=LOCAL_ZIP)
        logger.info("✅ Архив скачан полностью")
    else:
        logger.info("Файл архива уже есть, пропускаем скачивание")
    
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
            # сохраняем прогресс
            with open(EXTRACT_META, "w") as f:
                for fname in extracted_files:
                    f.write(fname + "\n")
            time.sleep(0.05)
    
    logger.info("✅ Архив полностью распакован! Все файлы на месте.")
