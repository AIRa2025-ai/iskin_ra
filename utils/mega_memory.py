# utils/mega_memory.py
import os
import time
import zipfile
import hashlib
from datetime import datetime
from mega_wrapper import upload_file_sync
import threading
import signal
from collections import deque
from utils.notify import notify
from mega import Mega  # синхронный

# === Конфигурация ===
MEGA_EMAIL = os.getenv("MEGA_EMAIL") or "osvobozhdenie.ra@gmail.com"
MEGA_PASSWORD = os.getenv("MEGA_PASSWORD") or "Dbhec19771984"
LOCAL_MEMORY_DIR = "memory"
LOCAL_LOGS_DIR = "logs"
ARCHIVE_MEMORY = "ra_memory_backup.zip"
ARCHIVE_LOGS = "ra_logs_backup.zip"
CHECKSUM_FILE = "/app/memory/.last_sync_checksum"
SYNC_LOG = "/app/logs/mega_sync.log"
MAX_ARCHIVES = 5
SYNC_INTERVAL = 600  # секунд (10 минут)
MAX_RETRIES = 3
RETRY_DELAY = 10

stop_flag = False

# === Сигналы ===
def signal_handler(signum, frame):
    global stop_flag
    log(f"✋ Получен сигнал {signum}, подготовка к завершению...")
    stop_flag = True

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# === Вспомогательные функции ===
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
    except Exception as e:
        print(f"⚠️ Не удалось записать лог: {e}")

def get_directory_checksum(directory):
    hash_md5 = hashlib.md5()
    for root, _, files in os.walk(directory):
        for f in sorted(files):
            filepath = os.path.join(root, f)
            try:
                with open(filepath, "rb") as file:
                    for chunk in iter(lambda: file.read(4096), b""):
                        hash_md5.update(chunk)
            except Exception as e:
                log(f"⚠️ Ошибка хэширования файла {filepath}: {e}")
    return hash_md5.hexdigest()

def create_zip(directory, archive_name):
    ensure_dirs()
    archive_path = f"/app/{archive_name}"
    try:
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(directory):
                for file in files:
                    filepath = os.path.join(root, file)
                    arcname = os.path.relpath(filepath, directory)
                    zipf.write(filepath, arcname)
    except Exception as e:
        log(f"❌ Ошибка при создании архива {archive_name}: {e}")
    return archive_path

def cleanup_local_archives(base_name, keep=MAX_ARCHIVES):
    dir_path = "/app"
    archives = [f for f in os.listdir(dir_path) if f.startswith(base_name) and f.endswith(".zip")]
    if len(archives) <= keep:
        return
    archives.sort()
    for f in archives[:-keep]:
        try:
            os.remove(os.path.join(dir_path, f))
            log(f"🗑️ Удалён старый архив: {f}")
        except Exception as e:
            log(f"⚠️ Не удалось удалить архив {f}: {e}")

# === Подключение к Mega ===
def connect_to_mega():
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            m = Mega()
            m.login(MEGA_EMAIL, MEGA_PASSWORD)
            log("✅ Подключено к Mega.nz")
            return m
        except Exception as e:
            log(f"❌ Попытка {attempt} — ошибка подключения к Mega: {e}")
            notify(f"❌ Попытка {attempt} — ошибка подключения к Mega: {e}")
            time.sleep(RETRY_DELAY)
    log("⚠️ Не удалось подключиться к Mega после нескольких попыток")
    return None

def upload_to_mega(archive_name, archive_path):
    if stop_flag:
        log(f"✋ Пропускаем загрузку {archive_name} — стоп активен")
        return
    m = connect_to_mega()
    if not m:
        return
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            m.upload(archive_path)
            log(f"💾 Архив {archive_name} успешно загружен")
            notify(f"💾 Архив {archive_name} успешно загружен")
            cleanup_local_archives(os.path.splitext(archive_name)[0])
            return
        except Exception as e:
            log(f"❌ Попытка {attempt} — ошибка загрузки {archive_name}: {e}")
            time.sleep(RETRY_DELAY)
    log(f"⚠️ Не удалось загрузить {archive_name} после {MAX_RETRIES} попыток")

def restore_from_mega():
    ensure_dirs()
    if stop_flag:
        log("✋ Пропуск восстановления — стоп активен")
        return

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            m = Mega()
            m.login(MEGA_EMAIL, MEGA_PASSWORD)
            files = m.get_files()
            archive_id = next(
                (fid for fid, data in files.items() if data.get('a', {}).get('n') == ARCHIVE_MEMORY),
                None
            )
            if not archive_id:
                log(f"⚠️ Архив памяти {ARCHIVE_MEMORY} не найден в Mega")
                notify(f"⚠️ Архив памяти {ARCHIVE_MEMORY} не найден в Mega")
                return

            archive_path = f"/app/{ARCHIVE_MEMORY}"
            temp_path = f"/app/tmp_{ARCHIVE_MEMORY}"
            m.download(files[archive_id], dest_filename=temp_path)

            # вычисляем md5 скачанного архива
            hash_md5 = hashlib.md5()
            with open(temp_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            new_checksum = hash_md5.hexdigest()

            old_checksum = None
            if os.path.exists(CHECKSUM_FILE):
                try:
                    with open(CHECKSUM_FILE, "r") as f:
                        old_checksum = f.read().strip()
                except Exception as e:
                    log(f"⚠️ Не удалось прочитать локальную контрольную сумму: {e}")

            if new_checksum == old_checksum:
                log("✅ Память не изменилась, перезапись не нужна")
                os.remove(temp_path)
                return

            os.replace(temp_path, archive_path)
            with zipfile.ZipFile(archive_path, "r") as zipf:
                zipf.extractall(LOCAL_MEMORY_DIR)

            try:
                with open(CHECKSUM_FILE, "w") as f:
                    f.write(new_checksum)
            except Exception as e:
                log(f"⚠️ Не удалось записать контрольную сумму после восстановления: {e}")

            log("🧠 Память Ра успешно восстановлена и обновлена из Mega")
            notify("🧠 Память Ра успешно восстановлена и обновлена")
            return

        except Exception as e:
            log(f"❌ Попытка {attempt} — ошибка восстановления памяти: {e}")
            time.sleep(RETRY_DELAY)

    log(f"⚠️ Не удалось восстановить память после {MAX_RETRIES} попыток")

def backup_memory_and_logs():
    new_checksum = get_directory_checksum(LOCAL_MEMORY_DIR)
    old_checksum = None
    if os.path.exists(CHECKSUM_FILE):
        try:
            with open(CHECKSUM_FILE, "r") as f:
                old_checksum = f.read().strip()
        except Exception as e:
            log(f"⚠️ Не удалось прочитать контрольную сумму: {e}")

    if new_checksum != old_checksum:
        archive_path = create_zip(LOCAL_MEMORY_DIR, ARCHIVE_MEMORY)
        upload_to_mega(ARCHIVE_MEMORY, archive_path)
        try:
            with open(CHECKSUM_FILE, "w") as f:
                f.write(new_checksum)
        except Exception as e:
            log(f"⚠️ Не удалось записать контрольную сумму: {e}")

    archive_path_logs = create_zip(LOCAL_LOGS_DIR, ARCHIVE_LOGS)
    upload_to_mega(ARCHIVE_LOGS, archive_path_logs)

def archive_old_logs(days=7):
    cutoff = time.time() - days*24*3600
    for f in os.listdir(LOCAL_LOGS_DIR):
        path = os.path.join(LOCAL_LOGS_DIR, f)
        if os.path.isfile(path) and os.path.getmtime(path) < cutoff:
            archive_name = f"old_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            archive_path = os.path.join("/app", archive_name)
            try:
                with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(path, arcname=f)
                os.remove(path)
                upload_to_mega(archive_name, archive_path)
            except Exception as e:
                log(f"⚠️ Ошибка архивирования старого лога {f}: {e}")

def start_auto_sync():
    ensure_dirs()
    def sync_loop():
        restart_times = deque()
        while not stop_flag:
            now = time.time()
            while restart_times and now - restart_times[0] > 60:
                restart_times.popleft()
            num_recent_restarts = len(restart_times)
            sleep_time = min(5 * (2 ** num_recent_restarts), 120)

            if num_recent_restarts >= MAX_ARCHIVES:
                log(f"⚠️ Много перезапусков синхронизации, пауза {sleep_time}s")
                time.sleep(sleep_time)
                restart_times.clear()
                continue

            try:
                restart_times.append(time.time())
                backup_memory_and_logs()
                archive_old_logs()
                log("🔁 Синхронизация Mega завершена успешно")
                notify("🔁 Синхронизация памяти и логов с Mega завершена")
            except Exception as e:
                log(f"⚠️ Ошибка авто-синхронизации: {e}")
                notify(f"⚠️ Ошибка авто-синхронизации: {e}")

            for _ in range(SYNC_INTERVAL):
                if stop_flag:
                    break
                time.sleep(1)

    threading.Thread(target=sync_loop, daemon=True).start()
    log("🌐 Авто-синхронизация Mega запущена")
