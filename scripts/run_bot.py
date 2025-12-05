# scripts/run_bot_full.py — автоперезапуск бота при сбое + авто-синхронизация + тихий старт + проверка версий + отложенный рестарт + мягкое завершение + очистка процессов
import subprocess
import time
import sys
import traceback
import signal
import psutil  # pip install psutil
from collections import deque
from random import randint
from scripts.update_modules import MODULES_DIR  # noqa: F401
from utils.mega_memory import restore_from_mega, start_auto_sync, stop_auto_sync, log
from utils.notify import notify
import importlib
import pkg_resources

MAX_RESTARTS = 5
TIME_WINDOW = 60
BASE_SLEEP = 5
MAX_SLEEP = 120
QUIET_START_DELAY = 3
DELAY_AFTER_UPDATE = 5
DELAY_AFTER_MODULE_UPDATE = 20
CRITICAL_MODULES = ["requests", "aiohttp", "numpy"]

stop_flag = False  # Флаг для мягкого завершения
child_processes = []  # Для отслеживания процессов ra_bot_gpt

def signal_handler(signum, frame):
    global stop_flag
    log(f"✋ Получен сигнал {signum}, подготовка к завершению...")
    stop_flag = True
    stop_auto_sync()
    terminate_children()

def terminate_children():
    """Убиваем все зависшие процессы ra_bot_gpt и его потомков."""
    for proc in child_processes:
        try:
            if proc.poll() is None:  # если процесс ещё жив
                log(f"💀 Завершаем зависший процесс: PID {proc.pid}")
                parent = psutil.Process(proc.pid)
                for child in parent.children(recursive=True):
                    child.kill()
                parent.kill()
        except Exception as e:
            log(f"⚠️ Ошибка при завершении процесса {proc.pid}: {e}")
    child_processes.clear()

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def check_module_versions():
    updates_needed = False
    for mod in CRITICAL_MODULES:
        try:
            pkg = importlib.import_module(mod)
            installed_version = pkg.__version__
            log(f"ℹ️ Модуль '{mod}' установлен, версия {installed_version}")
        except ImportError:
            log(f"⚠️ Модуль '{mod}' не установлен!")
            updates_needed = True
        except AttributeError:
            try:
                installed_version = pkg_resources.get_distribution(mod).version
                log(f"ℹ️ Модуль '{mod}' установлен, версия {installed_version}")
            except Exception:
                log(f"⚠️ Не удалось определить версию модуля '{mod}'")
                updates_needed = True
    return updates_needed

def perform_prestart_checks():
    log("🔄 Обновление модулей перед запуском...")
    subprocess.run([sys.executable, "/app/scripts/update_modules.py"], check=True)
    time.sleep(QUIET_START_DELAY)

    log("🧠 Восстановление памяти Ра из Mega...")
    restore_from_mega()
    time.sleep(QUIET_START_DELAY)

    log("🌐 Запуск авто-синхронизации памяти и логов...")
    start_auto_sync()
    time.sleep(QUIET_START_DELAY)

    if check_module_versions():
        log(f"⚠️ Обнаружены проблемы с критичными модулями. Пауза {DELAY_AFTER_UPDATE} секунд...")
        time.sleep(DELAY_AFTER_UPDATE)

    log(f"⏳ Отложенный рестарт бота после обновления модулей: {DELAY_AFTER_MODULE_UPDATE} секунд...")
    time.sleep(DELAY_AFTER_MODULE_UPDATE + randint(0, 5))

def main_loop():
    restart_times = deque()

    while not stop_flag:
        now = time.time()
        while restart_times and now - restart_times[0] > TIME_WINDOW:
            restart_times.popleft()

        num_recent_restarts = len(restart_times)
        sleep_time = min(BASE_SLEEP * (2 ** num_recent_restarts), MAX_SLEEP)

        if num_recent_restarts >= MAX_RESTARTS:
            log(f"⚠️ Слишком много перезапусков за {TIME_WINDOW} секунд. Пауза {sleep_time} секунд...")
            time.sleep(sleep_time)
            restart_times.clear()
            continue

        try:
            restart_times.append(time.time())

            perform_prestart_checks()

            log("🚀 Запуск бота Ра...")
            proc = subprocess.Popen([sys.executable, "core/ra_bot_gpt.py"])
            child_processes.append(proc)

            # Ждём завершения процесса или стопа
            while proc.poll() is None and not stop_flag:
                time.sleep(1)

            if stop_flag:
                log("✋ Мягкое завершение после успешного запуска бота...")
                terminate_children()
                break

        except Exception as e:
            err_msg = f"💥 Бот упал с ошибкой: {e}, перезапуск через {sleep_time} секунд..."
            log(err_msg)
            notify(err_msg)

            try:
                log_file = "/app/logs/bot_errors.log"
                with open(log_file, "a+", encoding="utf-8") as f:
                    f.seek(0)
                    lines = f.readlines()
                    if len(lines) > 5000:
                        lines = lines[-2000:]
                        with open(log_file, "w", encoding="utf-8") as f2:
                            f2.writelines(lines)
                    f.write(f"{time.ctime()}:\n{traceback.format_exc()}\n\n")
            except Exception as log_error:
                log(f"⚠️ Не удалось записать лог ошибки: {log_error}")
                notify(f"⚠️ Не удалось записать лог ошибки: {log_error}")

            terminate_children()
            if stop_flag:
                log("✋ Мягкое завершение после ошибки...")
                break

            time.sleep(sleep_time)

    log("✅ Основной цикл завершен. Бот остановлен корректно.")

if __name__ == "__main__":
    main_loop()
