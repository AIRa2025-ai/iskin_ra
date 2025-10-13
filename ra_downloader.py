# ra_downloader.py
import os
import zipfile
import time
import logging
from mega import Mega
import json
import hashlib

# === Настройка логирования ===
logger = logging.getLogger("RaSvetDownloader")
logger.setLevel(logging.INFO)

# === Пути и ссылки ===
ARCHIVE_URL = "https://mega.nz/file/FlQ0ET4J#9gJjCBnj5uYn5bJYYMfPiN3BTvWz8el8leCWQPZvrUg"
LOCAL_ZIP = "/data/RaSvet.zip"
EXTRACT_DIR = "/data/RaSvet"
EXTRACT_META = "/data/RaSvet.extract.meta"


# === Вспомогательные функции ===
def md5(fname):
    """Возвращает MD5-хэш файла (для проверки изменений)."""
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def collect_rasvet_knowledge(base_folder: str) -> str:
    """Собирает знания РаСвета в один context.json"""
    knowledge = []
    if not os.path.exists(base_folder):
        return ""
    for root, _, files in os.walk(base_folder):
        for file in files:
            if file.endswith((".json", ".txt", ".md")):
                try:
                    path = os.path.join(root, file)
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                        knowledge.append(f"\n--- {file} ---\n{content}")
                except Exception as e:
                    logger.warning(f"Ошибка чтения {file}: {e}")

    context_path = os.path.join(base_folder, "context.json")
    try:
        with open(context_path, "w", encoding="utf-8") as f:
            json.dump({"context": "\n".join(knowledge)}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Не удалось записать context.json: {e}")
    return context_path


# === Класс загрузчика РаСвета ===
class RaSvetDownloader:
    def __init__(self, url=ARCHIVE_URL, local_zip=LOCAL_ZIP, extract_dir=EXTRACT_DIR):
        self.url = url
        self.local_zip = local_zip
        self.extract_dir = extract_dir
        self.meta_file = EXTRACT_META

    def download(self):
        """Скачивает архив, если его нет."""
        os.makedirs(self.extract_dir, exist_ok=True)
        m = Mega()
        m.login()

        if not os.path.exists(self.local_zip) or os.path.getsize(self.local_zip) == 0:
            logger.info("📥 Начинаем скачивание архива...")
            m.download_url(self.url, dest_filename=self.local_zip)
            logger.info("✅ Архив скачан полностью")
        else:
            logger.info("Файл архива уже есть, пропускаем скачивание")

    def extract(self):
        """Распаковывает архив с сохранением прогресса."""
        extracted_files = set()
        if os.path.exists(self.meta_file):
            with open(self.meta_file, "r") as f:
                extracted_files = set(line.strip() for line in f if line.strip())

        logger.info("📂 Начинаем распаковку архива...")
        with zipfile.ZipFile(self.local_zip, 'r') as zip_ref:
            for member in zip_ref.infolist():
                if member.filename in extracted_files:
                    continue
                zip_ref.extract(member, self.extract_dir)
                logger.info(f"Распакован файл: {member.filename}")
                extracted_files.add(member.filename)
                # сохраняем прогресс
                with open(self.meta_file, "w") as f:
                    for fname in extracted_files:
                        f.write(fname + "\n")
                time.sleep(0.02)

        logger.info("✅ Архив полностью распакован!")
        return collect_rasvet_knowledge(self.extract_dir)

    def run(self):
        """Полный цикл загрузки и распаковки."""
        self.download()
        return self.extract()


# === Обёртка для совместимости с другими файлами ===
def download_and_extract_rasvet():
    """Функция для внешнего вызова (например, из ra_bot_gpt.py)."""
    downloader = RaSvetDownloader()
    return downloader.run()


# === Тестовое исполнение ===
if __name__ == "__main__":
    path = download_and_extract_rasvet()
    print("✅ Готово. Context сохранён в:", path)
