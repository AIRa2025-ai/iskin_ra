# utils/auto_commit.py — автокоммит с тихим стартом, проверками, мягким завершением и автоперезапуском
# noqa: F401 для os
import os
import subprocess
import time
import signal
import logging
from datetime import datetime
from collections import deque
from random import randint
import asyncio
import traceback

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

MAX_RESTARTS = 5
TIME_WINDOW = 60
BASE_SLEEP = 5
MAX_SLEEP = 120
QUIET_START_DELAY = 3
DELAY_AFTER_ERROR = 10        # пауза после ошибки
DELAY_AFTER_MODULE_CHECK = 5  # пауза после проверок перед стартом
DELAY_AFTER_COMMIT = 5        # пауза после успешного коммита
CRITICAL_MODULES = ["git", "os", "subprocess"]  # проверяемые "модули"

stop_flag = False  # для мягкого завершения

def signal_handler(signum, frame):
    global stop_flag
    logging.info(f"✋ Получен сигнал {signum}, подготовка к завершению...")
    stop_flag = True

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def _run(cmd):
    """Запуск команды shell с возвратом кода и вывода."""
    try:
        res = subprocess.run(cmd, shell=True, check=False, capture_output=True, text=True)
        return res.returncode, res.stdout + res.stderr
    except Exception as e:
        return 1, str(e)

def check_modules():
    """Проверка доступности критичных модулей/инструментов."""
    issues = False
    for mod in CRITICAL_MODULES:
        try:
            __import__(mod)
            logging.info(f"ℹ️ Модуль '{mod}' доступен")
        except ImportError:
            logging.warning(f"⚠️ Модуль '{mod}' недоступен!")
            issues = True
        except Exception:
            logging.warning(f"⚠️ Не удалось проверить модуль '{mod}'")
            issues = True
    return issues

def perform_commit(message="Обновление RaSvet", branch="main"):
    """Попытка автокоммита и пуша с логированием."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_msg = f"{message} ({now})"

    # проверка репозитория git
    code, out = _run("git rev-parse --is-inside-work-tree")
    if code != 0:
        logging.warning("⚠️ Не похоже на git-репозиторий:\n%s", out)
        return False

    # определяем текущую ветку
    code, branch_out = _run("git symbolic-ref --short HEAD")
    current_branch = branch_out.strip() if code == 0 else branch

    commands = [
        "git add .",
        f'git commit -m "{commit_msg}"',
        f"git push origin {current_branch}"
    ]

    for cmd in commands:
        code, out = _run(cmd)
        if code != 0:
            logging.error("❌ Ошибка при выполнении команды: %s\n%s", cmd, out)
            return False
        logging.info("✅ Команда выполнена успешно: %s", cmd)

    logging.info("🎉 Автокоммит и пуш завершены успешно в ветку '%s'", current_branch)
    return True

async def perform_prestart_checks():
    """Тихий старт и проверки перед автокоммитом."""
    logging.info("🔄 Подготовка перед автокоммитом...")
    await asyncio.sleep(QUIET_START_DELAY)
    if check_modules():
        logging.warning(f"⚠️ Проблемы с критичными модулями. Пауза {DELAY_AFTER_MODULE_CHECK}s")
        await asyncio.sleep(DELAY_AFTER_MODULE_CHECK)
    logging.info(f"⏳ Отложенный старт: {DELAY_AFTER_COMMIT}s")
    await asyncio.sleep(DELAY_AFTER_COMMIT + randint(0,5))

async def main_loop():
    """Основной цикл с автоперезапуском, мягким завершением и логированием."""
    restart_times = deque()

    while not stop_flag:
        now = time.time()
        while restart_times and now - restart_times[0] > TIME_WINDOW:
            restart_times.popleft()

        num_recent_restarts = len(restart_times)
        sleep_time = min(BASE_SLEEP * (2 ** num_recent_restarts), MAX_SLEEP)

        if num_recent_restarts >= MAX_RESTARTS:
            logging.warning(f"⚠️ Слишком много попыток за {TIME_WINDOW}s. Пауза {sleep_time}s...")
            await asyncio.sleep(sleep_time)
            restart_times.clear()
            continue

        try:
            restart_times.append(time.time())
            await perform_prestart_checks()

            logging.info("🔄 Попытка автокоммита...")
            success = perform_commit()

            if success:
                logging.info("✅ Автокоммит выполнен успешно.")
            else:
                logging.warning(f"⚠️ Автокоммит не удался. Пауза {DELAY_AFTER_ERROR}s")
                await asyncio.sleep(DELAY_AFTER_ERROR + randint(0,5))

            if stop_flag:
                logging.info("✋ Мягкое завершение после автокоммита...")
                break

        except Exception as e:
            logging.error(f"💥 Ошибка в main_loop: {e}")
            traceback.print_exc()
            if stop_flag:
                logging.info("✋ Мягкое завершение после ошибки...")
                break
            await asyncio.sleep(DELAY_AFTER_ERROR + randint(0,5))

    logging.info("✅ Основной цикл завершён. Автокоммит остановлен корректно.")

if __name__ == "__main__":
    asyncio.run(main_loop())
