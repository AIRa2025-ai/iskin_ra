# modules/ra_downloader_async.py
import os
import zipfile
import asyncio
import logging
from pathlib import Path
from typing import Set, Dict, Optional
from datetime import datetime
import aiohttp
import json
import errno

# Попытка взять ARCHIVE_URL из нескольких мест:
# 1) RA_ARCHIVE_URL (предпочтительно)
# 2) ARCHIVE_URL (для совместимости)
# 3) modules.ra_config.ARCHIVE_URL (если существует)
def _resolve_archive_url() -> str:
    env_url = os.getenv("RA_ARCHIVE_URL") or os.getenv("ARCHIVE_URL")
    if env_url:
        return env_url
    try:
        # динамически импортируем конфиг, если есть
        import modules.ra_config as rc  # type: ignore
        return getattr(rc, "ARCHIVE_URL", "") or ""
    except Exception:
        return ""

ARCHIVE_URL = _resolve_archive_url()
DATA_DIR = Path(os.getenv("RA_DATA_DIR", "data"))
LOCAL_ZIP = DATA_DIR / "RaSvet.zip"
EXTRACT_DIR = DATA_DIR / "RaSvet"
EXTRACT_META = DATA_DIR / "RaSvet.extract.meta"
META_JSON = DATA_DIR / "RaSvet.meta.json"
LOCK_FILE = DATA_DIR / ".rasvet_downloader.lock"

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
                if file.is_file() and file.suffix.lower() in [".txt", ".md", ".json"]:
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

    async def ask(self, question: str, user_id=None) -> Optional[str]:
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


def _is_valid_zip(path: Path) -> bool:
    """Проверяем zip: открываем и делаем testzip(). Возвращаем True, если архив целый."""
    try:
        with zipfile.ZipFile(path, 'r') as z:
            bad = z.testzip()  # возвращает имя первого проблемного файла или None
            if bad:
                logger.warning(f"❌ ZIP test failed, bad member: {bad}")
                return False
            return True
    except zipfile.BadZipFile:
        logger.warning("❌ BadZipFile при проверке локального архива")
        return False
    except Exception as e:
        logger.warning(f"❌ Ошибка при проверке zip: {e}")
        return False


def _acquire_lock() -> bool:
    """
    Простая файловая блокировка: создаём LOCK_FILE с O_EXCL.
    Возвращаем True если захватили, False если уже есть.
    """
    try:
        fd = os.open(str(LOCK_FILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
        return True
    except OSError as e:
        if e.errno == errno.EEXIST:
            return False
        raise


def _release_lock():
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except Exception as e:
        logger.warning(f"Не удалось удалить lock-файл: {e}")


class RaSvetDownloaderAsync:
    def __init__(self):
        self.knowledge = KnowledgeBase()
        self.extracted_files: Set[str] = set()
        self.meta_data: Dict[str, Dict] = {}
        # читаем метаданные распаковки
        if EXTRACT_META.exists():
            try:
                self.extracted_files = set(line.strip() for line in EXTRACT_META.read_text(encoding="utf-8").splitlines() if line.strip())
            except Exception:
                self.extracted_files = set()
        if META_JSON.exists():
            try:
                self.meta_data = json.loads(META_JSON.read_text(encoding="utf-8"))
            except Exception:
                self.meta_data = {}

    async def download_async(self):
        """Главный вход — скачивание (если требуется) и безопасная распаковка."""
        # блокировка, чтобы два процесса не делали одно и то же одновременно
        got_lock = False
        try:
            got_lock = _acquire_lock()
            if not got_lock:
                logger.info("🔒 Другой процесс уже выполняет скачивание/распаковку — пропускаем.")
                # даже если пропускаем скачивание, попытаемся загрузить уже распакованные знания
                await self.knowledge.load_from_folder(EXTRACT_DIR)
                return

            await self._download_archive_if_needed()
            await self._safe_extract_incremental()
            await self.knowledge.load_from_folder(EXTRACT_DIR)
        finally:
            if got_lock:
                _release_lock()

    async def _download_archive_if_needed(self):
        archive_url = ARCHIVE_URL or ""
        if not archive_url:
            logger.warning("ARCHIVE_URL not configured — пропускаем скачивание")
            return

        # пытаемся получить remote size, но если HEAD не возвращает Size — graceful fallback
        try:
            timeout = aiohttp.ClientTimeout(total=120)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                remote_size = 0
                try:
                    async with session.head(archive_url) as resp:
                        resp.raise_for_status()
                        remote_size = int(resp.headers.get("Content-Length") or 0)
                except Exception:
                    remote_size = 0

                local_size = LOCAL_ZIP.stat().st_size if LOCAL_ZIP.exists() else 0

                # Если локальный есть — проверяем валидность zip; если повреждён — нужно перекачать.
                local_valid = LOCAL_ZIP.exists() and _is_valid_zip(LOCAL_ZIP)

                need_download = False
                if not LOCAL_ZIP.exists():
                    need_download = True
                elif remote_size and local_size != remote_size:
                    # разные размеры — перекачать
                    need_download = True
                elif not local_valid:
                    # локальный есть, но битый — перекачать
                    need_download = True

                if not need_download:
                    logger.info("ℹ️ Архив актуален и валидный, скачивание пропущено")
                    return

                # делаем до 2 попыток скачивания (если скачали, но архив битый, пробуем ещё раз)
                attempts = 2
                for attempt in range(1, attempts + 1):
                    try:
                        logger.info(f"⬇️ Начинаю скачивание архива RaSvet (попытка {attempt}/{attempts})")
                        async with session.get(archive_url) as resp:
                            resp.raise_for_status()
                            with open(LOCAL_ZIP, "wb") as f:
                                async for chunk in resp.content.iter_chunked(32 * 1024):
                                    if chunk:
                                        f.write(chunk)
                                    await asyncio.sleep(0)
                        logger.info("✅ Архив скачан")
                        # проверяем
                        if _is_valid_zip(LOCAL_ZIP):
                            logger.info("✅ Скачанный архив валиден")
                            break
                        else:
                            logger.warning("⚠️ Скачанный архив оказался повреждённым")
                            if attempt == attempts:
                                logger.error("❌ Не удалось скачать корректный архив после нескольких попыток")
                        # если цикл не break — следующая попытка
                    except Exception as e:
                        logger.error(f"Ошибка при скачивании архива: {e}")
                        if attempt == attempts:
                            logger.error("❌ Превышено количество попыток скачивания")
        except Exception as e:
            logger.error(f"Ошибка сетевой операции при скачивании: {e}")

    async def _safe_extract_incremental(self):
        EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
        new_files = set()

        if not LOCAL_ZIP.exists():
            logger.warning("⚠ Нет локального архива для распаковки")
            return

        # если локальный zip повреждён — не распаковываем
        if not _is_valid_zip(LOCAL_ZIP):
            logger.error("❌ Архив поврежден, распаковка невозможна")
            return

        try:
            with zipfile.ZipFile(LOCAL_ZIP, 'r') as zip_ref:
                for member in zip_ref.infolist():
                    try:
                        # избегаем потенциальных traversal-атак — нормализация пути
                        member_name = member.filename
                        # проверка метаданных: если размер не изменился и уже распаковано — пропускаем
                        meta = self.meta_data.get(member_name, {})
                        size_changed = meta.get("size") != member.file_size
                        if member_name in self.extracted_files and not size_changed:
                            continue
                        # извлекаем
                        zip_ref.extract(member, EXTRACT_DIR)
                        logger.info(f"📂 Распакован: {member_name}")
                        new_files.add(member_name)
                        self.meta_data[member_name] = {"size": member.file_size, "mtime": datetime.now().isoformat()}
                        # даём шанc планировщику (не блокируем)
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

        # удаляем локальный архив только если распаковка прошла успешно (и ZIP валиден)
        try:
            if LOCAL_ZIP.exists():
                try:
                    # ещё раз проверим целостность перед удалением
                    if _is_valid_zip(LOCAL_ZIP):
                        LOCAL_ZIP.unlink()
                        logger.info("🧹 Локальный архив удалён после распаковки")
                    else:
                        logger.warning("⚠️ Локальный архив не удалён — он выглядит повреждённым")
                except Exception as e:
                    logger.warning(f"Не удалось удалить локальный архив: {e}")
        except Exception as e:
            logger.warning(f"Ошибка при попытке удаления архива: {e}")
