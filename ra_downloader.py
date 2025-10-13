import os
import zipfile
import time
from mega import Mega
import logging

# --- Настройка логов ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RaSvetDownloader")

# --- Пути и ссылки ---
ARCHIVE_URL = "https://mega.nz/file/514XQRRA#ppfZArsPd8dwq08sQBJTx4w4BRo-nr4ux_KNM3C44B0"
LOCAL_ZIP = "/data/RaSvet.zip"
EXTRACT_DIR = "/data/RaSvet"
META_FILE = "/data/RaSvet.download.meta"
EXTRACT_META = "/data/RaSvet.extract.meta"

# --- Подключение к Mega ---
m = Mega()
m.login()  # если нужно анонимно, можно оставить пустые параметры

file = m.find('имя_файла_в_аккаунте')  # вернёт словарь с данными файла
m.download(file)  # передаём словарь, а не строку

# --- Чтение прогресса скачивания ---
start_byte = 0
if os.path.exists(META_FILE):
    with open(META_FILE, "r") as f:
        start_byte = int(f.read())
        logger.info(f"Продолжаем скачивание с {start_byte} байта")

# --- Скачивание с сохранением прогресса ---
def download_resume(url, local_path, start):
    logger.info("📥 Начинаем скачивание архива...")
    # Mega.download поддерживает resume
    m.download(url, dest_filename=local_path)
    logger.info("✅ Архив скачан полностью")
    # Обновляем мета-файл
    with open(META_FILE, "w") as f:
        f.write(str(os.path.getsize(local_path)))

download_resume(ARCHIVE_URL, LOCAL_ZIP, start_byte)

# --- Распаковка по файлам с прогрессом ---
os.makedirs(EXTRACT_DIR, exist_ok=True)
extracted_files = set()

# загружаем прогресс извлечённых файлов
if os.path.exists(EXTRACT_META):
    with open(EXTRACT_META, "r") as f:
        extracted_files = set(line.strip() for line in f if line.strip())

logger.info("📂 Начинаем распаковку архива...")

with zipfile.ZipFile(LOCAL_ZIP, 'r') as zip_ref:
    all_members = zip_ref.infolist()
    for member in all_members:
        if member.filename in extracted_files:
            continue  # этот файл уже извлечён
        zip_ref.extract(member, EXTRACT_DIR)
        logger.info(f"Распакован файл: {member.filename}")
        extracted_files.add(member.filename)
        # сохраняем прогресс после каждого файла
        with open(EXTRACT_META, "w") as f:
            for fname in extracted_files:
                f.write(fname + "\n")
        time.sleep(0.1)  # даём Fly.io подышать

logger.info("✅ Архив полностью распакован! Все файлы на месте.")
