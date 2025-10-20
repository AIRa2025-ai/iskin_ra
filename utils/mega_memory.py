import os
import time
import zipfile
from mega import Mega
from datetime import datetime

# === Настройки ===
MEGA_EMAIL = os.getenv("MEGA_EMAIL") or "твоя_почта@mega.nz"
MEGA_PASSWORD = os.getenv("MEGA_PASSWORD") or "твой_пароль"
LOCAL_MEMORY_DIR = "/app/memory"
ARCHIVE_NAME = "ra_memory_backup.zip"

mega = Mega()

def connect_to_mega():
    try:
        m = mega.login(MEGA_EMAIL, MEGA_PASSWORD)
        print("✅ Подключено к Mega.nz")
        return m
    except Exception as e:
        print(f"❌ Ошибка подключения к Mega: {e}")
        return None

def backup_to_mega():
    m = connect_to_mega()
    if not m:
        return

    archive_path = f"/app/{ARCHIVE_NAME}"

    # Архивируем память
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(LOCAL_MEMORY_DIR):
            for file in files:
                filepath = os.path.join(root, file)
                zipf.write(filepath, os.path.relpath(filepath, LOCAL_MEMORY_DIR))

    # Загружаем архив
    try:
        m.upload(archive_path)
        print(f"💾 Память Ра успешно загружена в Mega: {ARCHIVE_NAME}")
    except Exception as e:
        print(f"❌ Ошибка при загрузке архива: {e}")

def restore_from_mega():
    m = connect_to_mega()
    if not m:
        return

    try:
        files = m.get_files()
        file_id = None
        for fid, data in files.items():
            if data['a']['n'] == ARCHIVE_NAME:
                file_id = fid
                break

        if file_id:
            file = files[file_id]
            path = f"/app/{ARCHIVE_NAME}"
            m.download(file, dest_filename=path)

            # Распаковываем память
            with zipfile.ZipFile(path, "r") as zipf:
                zipf.extractall(LOCAL_MEMORY_DIR)

            print("🧠 Память Ра восстановлена из Mega.")
        else:
            print("⚠️ Архив памяти не найден в Mega.")
    except Exception as e:
        print(f"❌ Ошибка при восстановлении памяти: {e}")

def auto_sync(interval=600):
    """Периодическая синхронизация памяти с Mega (раз в 10 минут по умолчанию)."""
    while True:
        backup_to_mega()
        time.sleep(interval)
