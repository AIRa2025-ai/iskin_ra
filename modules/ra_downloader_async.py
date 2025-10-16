# modules/ra_downloader_async.py
import os
import zipfile
import asyncio
import logging
from pathlib import Path
from typing import Set, Dict
from datetime import datetime
import aiohttp
import json

ARCHIVE_URL = "https://mega.nz/file/FlQ0ET4J#9gJjCBnj5uYn5bJYYMfPiN3BTvWz8el8leCWQPZvrUg"
DATA_DIR = Path("/app/data_disk")
LOCAL_ZIP = DATA_DIR / "RaSvet.zip"
EXTRACT_DIR = DATA_DIR / "RaSvet"
EXTRACT_META = DATA_DIR / "RaSvet.extract.meta"
META_JSON = DATA_DIR / "RaSvet.meta.json"  # хранит дату и size файлов для incremental

DATA_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("RaSvetDownloaderAsync")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

class KnowledgeBase:
    def __init__(self):
        self.documents: Dict[str, Dict] = {}  # filename -> {"content": str, "mtime": datetime}

    async def load_from_folder(self, folder: Path):
        self.documents = {}
        for file in folder.rglob("*"):
            if file.is_file() and file.suffix in [".txt", ".md", ".json"]:
                try:
                    self.documents[file.name] = {
                        "content": file.read_text(encoding="utf-8"),
                        "mtime": datetime.fromtimestamp(file.stat().st_mtime)
                    }
                except Exception as e:
                    logger.warning(f"⚠ Не удалось прочитать {file}: {e}")
        logger.info(f"📚 Загружено знаний: {len(self.documents)} файлов")

    async def ask(self, question: str, user_id=None) -> str:
        answers = []
        sorted_docs = sorted(self.documents.items(), key=lambda x: x[1]["mtime"], reverse=True)
        for fname, meta in sorted_docs:
            if question.lower() in meta["content"].lower():
                snippet = meta["content"][:500].replace("\n", " ")
                answers.append(f"[{fname}] {snippet}...")
        return "\n\n".join(answers[:5]) if answers else None

class RaSvetDownloaderAsync:
    """Асинхронное скачивание и incremental update архива"""
    def __init__(self):
        self.knowledge = KnowledgeBase()
        self.extracted_files: Set[str] = set()
        self.meta_data: Dict[str, Dict] = {}
        if EXTRACT_META.exists():
            self.extracted_files = set(line.strip() for line in EXTRACT_META.read_text().splitlines() if line.strip())
        if META_JSON.exists():
            try:
                self.meta_data = json.loads(META_JSON.read_text())
            except Exception:
                self.meta_data = {}

    async def download_async(self):
        await self._download_archive_if_needed()
        await self._safe_extract_incremental()
        await self.knowledge.load_from_folder(EXTRACT_DIR)

    async def _download_archive_if_needed(self):
        """Скачиваем архив только если нет локального файла или изменился размер"""
        async with aiohttp.ClientSession() as session:
            async with session.head(ARCHIVE_URL) as resp:
                resp.raise_for_status()
                remote_size = int(resp.headers.get("Content-Length", 0))
        local_size = LOCAL_ZIP.stat().st_size if LOCAL_ZIP.exists() else 0
        if local_size != remote_size:
            logger.info(f"⬇️ Начинаю скачивание архива RaSvet ({remote_size / 1024:.1f} KB)")
            async with aiohttp.ClientSession() as session:
                async with session.get(ARCHIVE_URL) as resp:
                    resp.raise_for_status()
                    with open(LOCAL_ZIP, "wb") as f:
                        async for chunk in resp.content.iter_chunked(32*1024):
                            f.write(chunk)
                            await asyncio.sleep(0)
            logger.info("✅ Архив скачан и готов к распаковке")
        else:
            logger.info("ℹ️ Архив актуален, скачивание пропущено")

    async def _safe_extract_incremental(self):
        EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
        new_files = set()
        if not LOCAL_ZIP.exists():
            logger.warning("⚠ Нет архива для распаковки")
            return

        try:
            with zipfile.ZipFile(LOCAL_ZIP, 'r') as zip_ref:
                for member in zip_ref.infolist():
                    meta = self.meta_data.get(member.filename, {})
                    size_changed = meta.get("size") != member.file_size
                    if member.filename in self.extracted_files and not size_changed:
                        continue
                    zip_ref.extract(member, EXTRACT_DIR)
                    logger.info(f"📂 Новый или обновлённый файл распакован: {member.filename}")
                    new_files.add(member.filename)
                    self.meta_data[member.filename] = {"size": member.file_size, "mtime": datetime.now().isoformat()}
                    await asyncio.sleep(0)
        except zipfile.BadZipFile:
            logger.error("❌ Архив поврежден, распаковка невозможна")
            return

        if new_files:
            self.extracted_files.update(new_files)
            EXTRACT_META.write_text("\n".join(self.extracted_files))
            META_JSON.write_text(json.dumps(self.meta_data, indent=2))
            logger.info(f"🌞 Обновлено файлов: {len(new_files)}")

        # Опционально можно удалить архив после распаковки
        if LOCAL_ZIP.exists():
            LOCAL_ZIP.unlink()
            logger.info("🧹 Архив удалён после распаковки")
