# utils/mega_memory.py
import os
import time
import zipfile
from mega import Mega
from datetime import datetime

# === Настройки Mega ===
MEGA_EMAIL = os.getenv("MEGA_EMAIL") or "твоя_почта@mega.nz"
MEGA_PASSWORD = os.getenv("MEGA_PASSWORD") or "твой_пароль"

# === Пути внутри контейнера ===
LOCAL_MEMORY_DIR = "/app/memory"
LOCAL_LOGS_DIR = "/app/logs"
BACKUP_DIR = "/app/backups"
os.makedirs(BACKUP_DIR, exist_ok=True)

# === Конфигурация ===
MAX_BACKUPS = 3              # сколько старых копий хранить
SYNC_INTERVAL_MEMORY = 3600  # каждые 1 час
SYNC_INTERVAL_LOGS = 7200    # каждые 2 часа

mega = Mega()

# -----------------------------------------------------------
#  Подключение
# -----------------------------------------------------------
def connect_to_mega():
    try:
        m = mega.login(MEGA_EMAIL, MEGA_PASSWORD)
        print("✅ Подключено к Mega.nz")
        return m
    except Exception as e:
        print(f"❌ Ошибка подключения к Mega: {e}")
        return None

# -----------------------------------------------------------
#  Создание zip архива
# -----------------------------------------------------------
def create_zip(source_dir, name_prefix):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"{name_prefix}_{timestamp}.zip"
    archive_path = os.path.join(BACKUP_DIR, archive_name)

    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(source_dir):
            for file in files:
                filepath = os.path.join(root, file)
                relpath = os.path.relpath(filepath, source_dir)
                zipf.write(filepath, relpath)

    return archive_path

# -----------------------------------------------------------
#  Очистка старых архивов
# -----------------------------------------------------------
def clean_old_backups(prefix="ra_memory"):
    backups = sorted(
        [f for f in os.listdir(BACKUP_DIR) if f.startswith(prefix)],
        reverse=True
    )
    for old_file in backups[MAX_BACKUPS:]:
        os.remove(os.path.join(BACKUP_DIR, old_file))
        print(f"🧹 Удалён старый архив: {old_file}")

# -----------------------------------------------------------
#  Загрузка архива на Mega
# -----------------------------------------------------------
def upload_to_mega(local_path):
    m = connect_to_mega()
    if not m:
        return
    try:
        m.upload(local_path)
        print(f"☁️ Загружен на Mega: {os.path.basename(local_path)}")
    except Exception as e:
        print(f"⚠️ Ошибка загрузки на Mega: {e}")

# -----------------------------------------------------------
#  Восстановление памяти из Mega
# -----------------------------------------------------------
def restore_from_mega():
    m = connect_to_mega()
    if not m:
        return

    try:
        files = m.get_files()
        latest = None
        latest_time = None

        for fid, data in files.items():
            name = data['a'].get('n', '')
            if name.startswith("ra_memory_") and name.endswith(".zip"):
                ts = data['ts']
                if latest_time is None or ts > latest_time:
                    latest_time = ts
                    latest = (fid, name)

        if not latest:
            print("⚠️ Архив памяти не найден в Mega.")
            return

        fid, name = latest
        dest = os.path.join(BACKUP_DIR, name)
        print(f"📥 Загружаем {name} из Mega...")
        m.download(files[fid], dest_filename=dest)

        with zipfile.ZipFile(dest, "r") as zipf:
            zipf.extractall(LOCAL_MEMORY_DIR)
        print("🧠 Память Ра восстановлена из Mega.")
    except Exception as e:
        print(f"❌ Ошибка при восстановлении памяти: {e}")

# -----------------------------------------------------------
#  Резервное копирование памяти
# -----------------------------------------------------------
def backup_memory_to_mega():
    archive_path = create_zip(LOCAL_MEMORY_DIR, "ra_memory")
    upload_to_mega(archive_path)
    clean_old_backups("ra_memory")

# -----------------------------------------------------------
#  Резервное копирование логов
# -----------------------------------------------------------
def backup_logs_to_mega():
    archive_path = create_zip(LOCAL_LOGS_DIR, "ra_logs")
    upload_to_mega(archive_path)
    clean_old_backups("ra_logs")

# -----------------------------------------------------------
#  Автосинхронизация
# -----------------------------------------------------------
def start_auto_sync():
    import threading

    def sync_memory():
        while True:
            try:
                backup_memory_to_mega()
            except Exception as e:
                print(f"⚠️ Ошибка бэкапа памяти: {e}")
            time.sleep(SYNC_INTERVAL_MEMORY)

    def sync_logs():
        while True:
            try:
                backup_logs_to_mega()
            except Exception as e:
                print(f"⚠️ Ошибка бэкапа логов: {e}")
            time.sleep(SYNC_INTERVAL_LOGS)

    threading.Thread(target=sync_memory, daemon=True).start()
    threading.Thread(target=sync_logs, daemon=True).start()
    print("🔄 Автосинхронизация Mega запущена.")
