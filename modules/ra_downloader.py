import os
import zipfile
import time
import logging
import psutil
from mega import Mega
from pathlib import Path

# === НАСТРОЙКА ===
ARCHIVE_URL = "https://mega.nz/file/FlQ0ET4J#9gJjCBnj5uYn5bJYYMfPiN3BTvWz8el8leCWQPZvrUg"
DATA_DIR = Path("/app/data_disk")  # папка на диске
LOCAL_ZIP = DATA_DIR / "RaSvet.zip"
EXTRACT_DIR = DATA_DIR / "RaSvet"
EXTRACT_META = DATA_DIR / "RaSvet.extract.meta"
MAX_TEMP_AGE_HOURS = 3
MEMORY_THRESHOLD_MB = 150

DATA_DIR.mkdir(parents=True, exist_ok=True)

# === ЛОГИ ===
logger = logging.getLogger("RaSvetDownloader")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===
def cleanup_temp(folder=DATA_DIR, older_than_hours=MAX_TEMP_AGE_HOURS):
    """Удаляет старые файлы из папки"""
    now = time.time()
    removed = 0
    for path in folder.glob("**/*"):
        if path.is_file() and now - path.stat().st_mtime > older_than_hours * 3600:
            try:
                path.unlink()
                removed += 1
            except Exception:
                pass
    if removed:
        logger.info(f"🧹 Удалено старых файлов: {removed}")

def check_memory():
    """Проверяет доступную память"""
    free_mb = psutil.virtual_memory().available / (1024 ** 2)
    if free_mb < MEMORY_THRESHOLD_MB:
        logger.warning(f"⚠ Мало памяти ({free_mb:.1f} МБ)! Запущена очистка...")
        cleanup_temp()
    else:
        logger.info(f"💾 Свободно памяти: {free_mb:.1f} МБ")

def safe_extract(zip_path, extract_dir):
    """Безопасная распаковка архива с контролем памяти и прогрессом"""
    extract_dir.mkdir(parents=True, exist_ok=True)
    extracted_files = set()

    if EXTRACT_META.exists():
        extracted_files = set(line.strip() for line in EXTRACT_META.read_text().splitlines() if line.strip())

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for member in zip_ref.infolist():
            if member.filename in extracted_files:
                continue
            check_memory()
            zip_ref.extract(member, extract_dir)
            logger.info(f"📂 Распакован: {member.filename}")
            extracted_files.add(member.filename)
            EXTRACT_META.write_text("\n".join(extracted_files))
            time.sleep(0.01)

    logger.info("✅ Архив полностью распакован!")

def download_and_extract_rasvet():
    """Главная функция скачивания и распаковки архива РаСвета"""
    check_memory()
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)

    mega = Mega()
    mega.login()  # анонимно

    # Скачиваем архив только если его нет или он пустой
    if not LOCAL_ZIP.exists() or LOCAL_ZIP.stat().st_size == 0:
        logger.info("📥 Скачивание архива с Mega...")
        for attempt in range(3):
            try:
                mega.download_url(ARCHIVE_URL, dest_filename=str(LOCAL_ZIP))
                logger.info("✅ Архив скачан успешно")
                break
            except Exception as e:
                logger.warning(f"⚠ Ошибка скачивания (попытка {attempt+1}): {e}")
                time.sleep(5)
        else:
            logger.error("❌ Не удалось скачать архив после 3 попыток")
            return
    else:
        logger.info("ℹ️ Архив уже существует — пропускаем скачивание")

    safe_extract(LOCAL_ZIP, EXTRACT_DIR)

    if LOCAL_ZIP.exists():
        LOCAL_ZIP.unlink()
        logger.info(f"🧹 Удалён архив: {LOCAL_ZIP}")

    cleanup_temp()
    logger.info("🌞 РаСвет обновлён и чист!")

class RaSvetDownloader:
    """Класс для удобного вызова"""
    def download(self):
        logger.info("⚙ Скачиваем данные РаСвета...")
        download_and_extract_rasvet()

if __name__ == "__main__":
    RaSvetDownloader().download()
