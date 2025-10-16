# modules/ra_downloader_async.py
import os
import zipfile
import asyncio
import logging
import time
from pathlib import Path
from mega import Mega
from typing import Set

# === НАСТРОЙКА ===
ARCHIVE_URL = "https://mega.nz/file/FlQ0ET4J#9gJjCBnj5uYn5bJYYMfPiN3BTvWz8el8leCWQPZvrUg"
DATA_DIR = Path("/app/data_disk")
LOCAL_ZIP = DATA_DIR / "RaSvet.zip"
EXTRACT_DIR = DATA_DIR / "RaSvet"
EXTRACT_META = DATA_DIR / "RaSvet.extract.meta"

DATA_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("RaSvetDownloaderAsync")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

class KnowledgeBase:
    """Хранение распакованных документов и быстрый доступ к ним"""
    def __init__(self):
        self.documents = {}  # {filename: content}

    async def load_from_folder(self, folder: Path):
        """Загрузка всех текстов из папки в память"""
        self.documents = {}
        for file in folder.rglob("*"):
            if file.is_file() and file.suffix in [".txt", ".md", ".json"]:
                try:
                    self.documents[file.name] = file.read_text(encoding="utf-8")
                except Exception:
                    pass
        logger.info(f"📚 Загрузка знаний завершена, документов: {len(self.documents)}")

    async def ask(self, question: str, user_id=None) -> str:
        """Простой поиск по документам (можно апгрейдить на embeddings)"""
        answers = []
        for fname, content in self.documents.items():
            if question.lower() in content.lower():
                snippet = content[:500].replace("\n", " ")
                answers.append(f"[{fname}] {snippet}...")
        if answers:
            return "\n\n".join(answers)
        return None

class RaSvetDownloaderAsync:
    """Асинхронный апгрейд скачивания и обновления базы РаСвет"""
    def __init__(self):
        self.knowledge = KnowledgeBase()
        self.extracted_files: Set[str] = set()
        if EXTRACT_META.exists():
            self.extracted_files = set(line.strip() for line in EXTRACT_META.read_text().splitlines() if line.strip())

    async def download_async(self):
        """Скачивание архива (если нужно) и безопасная распаковка новых файлов"""
        mega = Mega()
        mega.login()
        # Скачиваем только если нет архива
        if not LOCAL_ZIP.exists() or LOCAL_ZIP.stat().st_size == 0:
            logger.info("📥 Скачиваем архив с Mega...")
            for attempt in range(3):
                try:
                    mega.download_url(ARCHIVE_URL, dest_filename=str(LOCAL_ZIP))
                    logger.info("✅ Архив скачан")
                    break
                except Exception as e:
                    logger.warning(f"⚠ Ошибка скачивания ({attempt+1}): {e}")
                    await asyncio.sleep(5)
            else:
                logger.error("❌ Не удалось скачать архив")
                return

        await self.safe_extract_async()
        await self.knowledge.load_from_folder(EXTRACT_DIR)

        # Удаляем архив после распаковки
        if LOCAL_ZIP.exists():
            LOCAL_ZIP.unlink()
            logger.info("🧹 Архив удалён после распаковки")

    async def safe_extract_async(self):
        """Распаковка только новых файлов"""
        EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
        new_files = set()
        with zipfile.ZipFile(LOCAL_ZIP, 'r') as zip_ref:
            for member in zip_ref.infolist():
                if member.filename in self.extracted_files:
                    continue
                zip_ref.extract(member, EXTRACT_DIR)
                logger.info(f"📂 Новый файл распакован: {member.filename}")
                new_files.add(member.filename)
                await asyncio.sleep(0)  # async-friendly
        if new_files:
            self.extracted_files.update(new_files)
            EXTRACT_META.write_text("\n".join(self.extracted_files))
            logger.info(f"🌞 Обновлено файлов: {len(new_files)}")
