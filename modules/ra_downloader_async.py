# modules/ra_downloader_async.py
import os
import zipfile
import time
import logging
import psutil
import asyncio
from mega import Mega
from pathlib import Path
from ra_autoloader import RaAutoloader
from gpt_module import safe_ask_openrouter

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
    free_mb = psutil.virtual_memory().available / (1024 ** 2)
    if free_mb < MEMORY_THRESHOLD_MB:
        logger.warning(f"⚠ Мало памяти ({free_mb:.1f} МБ)! Запущена очистка...")
        cleanup_temp()
    else:
        logger.info(f"💾 Свободно памяти: {free_mb:.1f} МБ")

def safe_extract(zip_path, extract_dir):
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

# === ЗАГРУЗКА ИНФЫ В ПАМЯТЬ ===
class RaSvetKnowledge:
    """Хранение и индексация файлов РаСвет"""
    def __init__(self, base_dir=EXTRACT_DIR):
        self.base_dir = Path(base_dir)
        self.documents = {}  # key=путь, value=текст

    def load_documents(self):
        count = 0
        for file in self.base_dir.rglob("*.txt"):
            try:
                text = file.read_text(encoding="utf-8")
                self.documents[str(file)] = text
                count += 1
            except Exception:
                continue
        logger.info(f"📚 Загружено {count} документов РаСвета")

    async def ask(self, question, user_id=0):
        context_text = "\n".join(self.documents.values())
        messages_payload = [
            {"role": "system", "content": "Ты Ра, обладающий знаниями из файлов РаСвета"},
            {"role": "user", "content": f"{question}\n\nКонтекст:\n{context_text}"}
        ]
        response = await safe_ask_openrouter(user_id=user_id, messages_payload=messages_payload)
        return response

# === ЗАГРУЗКА ===
class RaSvetDownloaderAsync:
    """Скачивание и распаковка РаСвет + создание базы знаний"""
    def __init__(self):
        self.knowledge = RaSvetKnowledge()

    async def download_async(self):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._download_sync)
        self.knowledge.load_documents()

    def _download_sync(self):
        check_memory()
        EXTRACT_DIR.mkdir(parents=True, exist_ok=True)

        mega = Mega()
        mega.login()  # анонимно

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

# === ТЕСТОВЫЙ ЗАПУСК ===
if __name__ == "__main__":
    async def main():
        downloader = RaSvetDownloaderAsync()
        await downloader.download_async()
        answer = await downloader.knowledge.ask("Привет, Ра! Расскажи о себе.")
        print(answer)

    asyncio.run(main())
