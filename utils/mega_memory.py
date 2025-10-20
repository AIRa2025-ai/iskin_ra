# utils/mega_memory.py — прокачанная версия для Ра
import os
import time
import zipfile
import hashlib
from datetime import datetime
from mega import Mega
import threading
from utils.notify import notify

# === Конфигурация ===
MEGA_EMAIL = os.getenv("MEGA_EMAIL") or "твоя_почта@mega.nz"
MEGA_PASSWORD = os.getenv("MEGA_PASSWORD") or "твой_пароль"
LOCAL_MEMORY_DIR = "/app/memory"
LOCAL_LOGS_DIR = "/app/logs"
ARCHIVE_MEMORY = "ra_memory_backup.zip"
ARCHIVE_LOGS = "ra_logs_backup.zip"
CHECKSUM_FILE = "/app/memory/.last_sync_checksum"
SYNC_LOG = "/app/logs/mega_sync.log"
MAX_ARCHIVES = 5
SYNC_INTERVAL = 600  # секунд (10 минут)

# === Подготовка окружения ===
def ensure_dirs():
    for d in [LOCAL_MEMORY_DIR, LOCAL_LOGS_DIR]:
        os.makedirs(d, exist_ok=True)
    os.makedirs(os.path.dirname(SYNC_LOG), exist_ok=True)

def log(msg):
    ensure_dirs()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    try:
        with open(SYNC_LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except:
        pass

# === Подключение к Mega ===
def connect_to_mega():
    try:
        m = Mega().login(MEGA_EMAIL, MEGA_PASSWORD)
        log("✅ Подключено к Mega.nz")
        return m
    except Exception as e:
        log(f"❌ Ошибка подключения к Mega: {e}")
        notify(f"❌ Ошибка подключения к Mega: {e}")
        return None

# === Контрольная сумма папки ===
def get_directory_checksum(directory):
    hash_md5 = hashlib.md5()
    for root, _, files in os.walk(directory):
        for f in sorted(files):
            filepath = os.path.join(root, f)
            try:
                with open(filepath, "rb") as file:
                    for chunk in iter(lambda: file.read(4096), b""):
                        hash_md5.update(chunk)
            except:
                continue
    return hash_md5.hexdigest()

# === Создание архива ===
def create_zip(directory, archive_name):
    ensure_dirs()
    archive_path = f"/app/{archive_name}"
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(directory):
            for file in files:
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, directory)
                zipf.write(filepath, arcname)
    return archive_path

# === Очистка старых локальных архивов ===
def cleanup_local_archives(base_name, keep=MAX_ARCHIVES):
    dir_path = "/app"
    archives = [f for f in os.listdir(dir_path) if f.startswith(base_name) and f.endswith(".zip")]
    if len(archives) <= keep:
        return
    archives.sort()
    for f in archives[:-keep]:
        try:
            os.remove(os.path.join(dir_path, f))
            log(f"🗑️ Удалён локальный архив: {f}")
        except:
            log(f"⚠️ Не удалось удалить локальный архив: {f}")

# === Загрузка архива в Mega ===
def upload_to_mega(archive_name, archive_path):
    m = connect_to_mega()
    if not m:
        log(f"⚠️ Пропускаем загрузку {archive_name} — Mega недоступна.")
        notify(f"⚠️ Пропуск загрузки {archive_name} — Mega недоступна")
        return
    try:
        m.upload(archive_path)
        log(f"💾 Архив {archive_name} успешно загружен в Mega.")
        notify(f"💾 Архив {archive_name} успешно загружен в Mega")
        cleanup_local_archives(os.path.splitext(archive_name)[0])
    except Exception as e:
        log(f"❌ Ошибка при загрузке {archive_name}: {e}")
        notify(f"❌ Ошибка при загрузке {archive_name}: {e}")

# === Восстановление архива из Mega ===
def restore_from_mega():
    ensure_dirs()
    m = connect_to_mega()
    if not m:
        return
    try:
        files = m.get_files()
        archive_id = next((fid for fid, data in files.items() if data['a']['n'] == ARCHIVE_MEMORY), None)
        if not archive_id:
            log("⚠️ Архив памяти не найден в Mega.")
            notify("⚠️ Архив памяти не найден в Mega")
            return
        archive_path = f"/app/{ARCHIVE_MEMORY}"
        m.download(files[archive_id], dest_filename=archive_path)
        with zipfile.ZipFile(archive_path, "r") as zipf:
            zipf.extractall(LOCAL_MEMORY_DIR)
        log("🧠 Память Ра восстановлена из Mega.")
        notify("🧠 Память Ра восстановлена из Mega")
    except Exception as e:
        log(f"❌ Ошибка при восстановлении памяти: {e}")
        notify(f"❌ Ошибка при восстановлении памяти: {e}")

# === Резервное копирование памяти ===
def backup_to_mega():
    ensure_dirs()
    new_checksum = get_directory_checksum(LOCAL_MEMORY_DIR)
    old_checksum = None
    if os.path.exists(CHECKSUM_FILE):
        with open(CHECKSUM_FILE, "r") as f:
            old_checksum = f.read().strip()
    if new_checksum == old_checksum:
        log("🟢 Память не изменилась — пропускаем загрузку в Mega.")
        return
    archive_path = create_zip(LOCAL_MEMORY_DIR, ARCHIVE_MEMORY)
    upload_to_mega(ARCHIVE_MEMORY, archive_path)
    with open(CHECKSUM_FILE, "w") as f:
        f.write(new_checksum)

# === Резервное копирование логов ===
def backup_logs_to_mega():
    ensure_dirs()
    archive_path = create_zip(LOCAL_LOGS_DIR, ARCHIVE_LOGS)
    upload_to_mega(ARCHIVE_LOGS, archive_path)

# === Архивирование старых логов (>7 дней) ===
def archive_old_logs(days=7):
    cutoff = time.time() - days*24*3600
    for f in os.listdir(LOCAL_LOGS_DIR):
        path = os.path.join(LOCAL_LOGS_DIR, f)
        if os.path.isfile(path) and os.path.getmtime(path) < cutoff:
            archive_name = f"old_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            archive_path = os.path.join("/app", archive_name)
            with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(path, arcname=f)
            os.remove(path)
            upload_to_mega(archive_name, archive_path)

# === Автоматическая синхронизация памяти и логов ===
def start_auto_sync():
    ensure_dirs()
    def sync_loop():
        while True:
            try:
                backup_to_mega()
                backup_logs_to_mega()
                archive_old_logs()
                log("🔁 Синхронизация Mega завершена успешно.")
                notify("🔁 Синхронизация памяти и логов с Mega завершена успешно")
            except Exception as e:
                log(f"⚠️ Ошибка авто-синхронизации: {e}")
                notify(f"⚠️ Ошибка авто-синхронизации: {e}")
            time.sleep(SYNC_INTERVAL)
    threading.Thread(target=sync_loop, daemon=True).start()
    log("🌐 Авто-синхронизация Mega запущена.")
