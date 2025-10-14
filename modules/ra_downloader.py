import os
import zipfile
import time
import logging
import psutil
from mega import Mega

# === НАСТРОЙКА ===
ARCHIVE_URL = "https://mega.nz/file/FlQ0ET4J#9gJjCBnj5uYn5bJYYMfPiN3BTvWz8el8leCWQPZvrUg"
DATA_DIR = "/app/data_disk"  # папка на диске, чтобы не нагружать RAM
LOCAL_ZIP = os.path.join(DATA_DIR, "RaSvet.zip")
EXTRACT_DIR = os.path.join(DATA_DIR, "RaSvet")
EXTRACT_META = os.path.join(DATA_DIR, "RaSvet.extract.meta")

# Создаём папку на диске, если ещё нет
os.makedirs(DATA_DIR, exist_ok=True)

# === ЛОГИ ===
logger = logging.getLogger("RaSvetDownloader")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===
def cleanup_temp(folder=DATA_DIR, older_than_hours=3):
    """Удаляет старые файлы из папки, чтобы не переполнять память"""
    now = time.time()
    removed = 0
    for root, _, files in os.walk(folder):
        for name in files:
            path = os.path.join(root, name)
            try:
                if now - os.path.getmtime(path) > older_than_hours * 3600:
                    os.remove(path)
                    removed += 1
            except Exception:
                pass
    if removed:
        logger.info(f"🧹 Удалено старых файлов: {removed}")

def check_memory():
    """Проверяет доступную память, если меньше 150 МБ — чистит временные данные"""
    free_mb = psutil.virtual_memory().available / (1024 ** 2)
    if free_mb < 150:
        logger.warning(f"⚠ Мало памяти ({free_mb:.1f} МБ)! Запущена очистка...")
        cleanup_temp()
    else:
        logger.info(f"💾 Свободно памяти: {free_mb:.1f} МБ")

def safe_extract(zip_path, extract_dir):
    """Безопасная распаковка архива с контролем памяти"""
    os.makedirs(extract_dir, exist_ok=True)
    extracted_files = set()

    # Восстанавливаем прогресс
    if os.path.exists(EXTRACT_META):
        with open(EXTRACT_META, "r") as f:
            extracted_files = set(line.strip() for line in f if line.strip())

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for member in zip_ref.infolist():
            if member.filename in extracted_files:
                continue

            check_memory()  # Проверяем перед каждым файлом
            zip_ref.extract(member, extract_dir)
            logger.info(f"📂 Распакован: {member.filename}")
            extracted_files.add(member.filename)

            # Сохраняем прогресс
            with open(EXTRACT_META, "w") as f:
                for fname in extracted_files:
                    f.write(fname + "\n")

            time.sleep(0.03)  # даём системе "вдохнуть"

    logger.info("✅ Архив полностью распакован!")

def download_and_extract_rasvet():
    """Главная функция скачивания и распаковки архива РаСвета"""
    check_memory()
    os.makedirs(EXTRACT_DIR, exist_ok=True)

    mega = Mega()
    mega.login()  # анонимно

    # Проверяем, нужен ли повторный скач
    if not os.path.exists(LOCAL_ZIP) or os.path.getsize(LOCAL_ZIP) == 0:
        logger.info("📥 Скачивание архива с Mega...")
        mega.download_url(ARCHIVE_URL, dest_filename=LOCAL_ZIP)
        logger.info("✅ Архив скачан успешно")
    else:
        logger.info("ℹ️ Архив уже существует — пропускаем скачивание")

    # Распаковка
    safe_extract(LOCAL_ZIP, EXTRACT_DIR)

    # Удаляем архив после успешной распаковки
    if os.path.exists(LOCAL_ZIP):
        os.remove(LOCAL_ZIP)
        logger.info(f"🧹 Удалён архив: {LOCAL_ZIP}")

    cleanup_temp()
    logger.info("🌞 РаСвет обновлён и чист!")

class RaSvetDownloader:
    """Класс-обёртка для удобного вызова"""
    def download(self):
        print("⚙ Скачиваем данные РаСвета...")
        download_and_extract_rasvet()

if __name__ == "__main__":
    downloader = RaSvetDownloader()
    downloader.download()
