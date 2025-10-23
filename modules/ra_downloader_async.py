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

# ARCHIVE_URL желательно задавать в modules/ra_config.py или через env RA_ARCHIVE_URL
ARCHIVE_URL = os.getenv("RA_ARCHIVE_URL", "")  # укажи свой корректный URL в окружении
DATA_DIR = Path(os.getenv("RA_DATA_DIR", "data"))
LOCAL_ZIP = DATA_DIR / "RaSvet.zip"
EXTRACT_DIR = DATA_DIR / "RaSvet"
EXTRACT_META = DATA_DIR / "RaSvet.extract.meta"
META_JSON = DATA_DIR / "RaSvet.meta.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)
EXTRACT_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("RaSvetDownloaderAsync")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)

class KnowledgeBase:
    def __init__(self):
        self.documents: Dict[str, Dict] = {}

    async def load_from_folder(self, folder: Path):
        self.documents = {}
        try:
            for file in Path(folder).rglob("*"):
                if file.is_file() and file.suffix in [".txt", ".md", ".json"]:
                    try:
                        self.documents[file.name] = {
                            "content": file.read_text(encoding="utf-8"),
                            "mtime": datetime.fromtimestamp(file.stat().st_mtime)
                        }
                    except Exception as e:
                        logger.warning(f"⚠ Не удалось прочитать {file}: {e}")
            logger.info(f"📚 Загружено знаний: {len(self.documents)} файлов")
        except Exception as e:
            logger.error(f"Ошибка при загрузке из папки {folder}: {e}")

    async def ask(self, question: str, user_id=None) -> str:
        if not question:
            return None
        answers = []
        sorted_docs = sorted(self.documents.items(), key=lambda x: x[1].get("mtime", datetime.min), reverse=True)
        for fname, meta in sorted_docs:
            try:
                if question.lower() in meta["content"].lower():
                    snippet = meta["content"][:500].replace("\n", " ")
                    answers.append(f"[{fname}] {snippet}...")
            except Exception:
                continue
        return "\n\n".join(answers[:5]) if answers else None

class RaSvetDownloaderAsync:
    def __init__(self):
        self.knowledge = KnowledgeBase()
        self.extracted_files: Set[str] = set()
        self.meta_data: Dict[str, Dict] = {}
        if EXTRACT_META.exists():
            try:
                self.extracted_files = set(line.strip() for line in EXTRACT_META.read_text().splitlines() if line.strip())
            except Exception:
                self.extracted_files = set()
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
        if not ARCHIVE_URL:
            logger.warning("ARCHIVE_URL not configured — пропускаем скачивание")
            return

        try:
            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # HEAD may not return Content-Length — обрабатываем gracefully
                try:
                    async with session.head(ARCHIVE_URL) as resp:
                        resp.raise_for_status()
                        remote_size = int(resp.headers.get("Content-Length") or 0)
                except Exception:
                    remote_size = 0

                local_size = LOCAL_ZIP.stat().st_size if LOCAL_ZIP.exists() else 0
                need_download = (local_size == 0) or (remote_size and local_size != remote_size)

                if not need_download:
                    logger.info("ℹ️ Архив актуален, скачивание пропущено")
                    return

                logger.info(f"⬇️ Начинаю скачивание архива RaSvet ({remote_size / 1024:.1f} KB)" if remote_size else "⬇️ Начинаю скачивание архива RaSvet")
                async with session.get(ARCHIVE_URL) as resp:
                    resp.raise_for_status()
                    with open(LOCAL_ZIP, "wb") as f:
                        async for chunk in resp.content.iter_chunked(32*1024):
                            f.write(chunk)
                            await asyncio.sleep(0)
                logger.info("✅ Архив скачан и готов к распаковке")
        except Exception as e:
            logger.error(f"Ошибка при скачивании архива: {e}")

    async def _safe_extract_incremental(self):
        EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
        new_files = set()
        if not LOCAL_ZIP.exists():
            logger.warning("⚠ Нет архива для распаковки")
            return

        try:
            with zipfile.ZipFile(LOCAL_ZIP, 'r') as zip_ref:
                for member in zip_ref.infolist():
                    try:
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
                        logger.error("❌ Архив поврежден при чтении member")
                        continue
                    except Exception as e:
                        logger.warning(f"Ошибка при распаковке {member.filename}: {e}")
        except zipfile.BadZipFile:
            logger.error("❌ Архив поврежден, распаковка невозможна")
            return
        except Exception as e:
            logger.error(f"Ошибка при распаковке архива: {e}")
            return

        if new_files:
            self.extracted_files.update(new_files)
            try:
                EXTRACT_META.write_text("\n".join(sorted(self.extracted_files)), encoding="utf-8")
                META_JSON.write_text(json.dumps(self.meta_data, ensure_ascii=False, indent=2), encoding="utf-8")
                logger.info(f"🌞 Обновлено файлов: {len(new_files)}")
            except Exception as e:
                logger.warning(f"Ошибка при записи метаданных распаковки: {e}")

        try:
            if LOCAL_ZIP.exists():
                LOCAL_ZIP.unlink()
                logger.info("🧹 Архив удалён после распаковки")
        except Exception as e:
            logger.warning(f"Не удалось удалить локальный архив: {e}")
