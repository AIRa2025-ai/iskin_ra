# agent_core.py — автоперезапуск, тихий старт, проверка версий, мягкое завершение, интеграция с Mega
# noqa: F401 для datetime, чтобы не было ошибок линтера
import os
import asyncio
import logging
import datetime  # noqa: F401
import signal
import time
import traceback
from collections import deque
from random import randint

from gpt_module import safe_ask_openrouter as ask_openrouter
from self_reflection import self_reflect_and_update
from github_commit import create_commit_push
from utils.mega_memory import restore_from_mega, start_auto_sync, stop_auto_sync

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

MAX_RESTARTS = 5
TIME_WINDOW = 60
BASE_SLEEP = 5
MAX_SLEEP = 120
QUIET_START_DELAY = 3
DELAY_AFTER_UPDATE = 5
DELAY_AFTER_MODULE_UPDATE = 20
CRITICAL_MODULES = ["requests", "aiohttp", "numpy"]

stop_flag = False  # Флаг для мягкого завершения

def signal_handler(signum, frame):
    global stop_flag
    logging.info(f"✋ Получен сигнал {signum}, подготовка к завершению...")
    stop_flag = True
    try:
        stop_auto_sync()  # Останавливаем авто-синхронизацию
    except Exception as e:
        logging.error(f"Ошибка при остановке авто-синхронизации: {e}")

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

class AgentCore:
    def __init__(self):
        self.user_id = "core_agent"
        self.memory_path = "memory/"
        os.makedirs(self.memory_path, exist_ok=True)

    async def ask(self, message):
        messages = [{"role": "user", "content": message}]
        logging.info(f"💬 Отправка запроса GPT: {message[:50]}...")
        try:
            answer = await ask_openrouter(self.user_id, messages)
            logging.info(f"💡 Ответ GPT получен: {answer[:50]}...")
            return answer
        except Exception as e:
            logging.error(f"❌ Ошибка при запросе GPT: {e}")
            return f"Ошибка GPT: {e}"

    async def self_update(self):
        logging.info("🧠 Запуск self-reflection...")
        try:
            await self_reflect_and_update()
            logging.info("✨ Self-reflection завершён успешно.")
        except Exception as e:
            logging.error(f"❌ Ошибка self-reflection: {e}")

    def create_pr_for_files(self, files_dict, msg="Auto-update by Ra"):
        branch_name = f"auto-update-{os.getpid()}"
        try:
            pr = create_commit_push(branch_name, files_dict, msg)
            logging.info(f"✅ PR создан: {pr.get('html_url', 'URL недоступен')}")
            return pr
        except Exception as e:
            logging.error(f"❌ Ошибка при создании PR: {e}")
            return {"html_url": None, "error": str(e)}

    def check_module_versions(self):
        updates_needed = False
        for mod in CRITICAL_MODULES:
            try:
                pkg = __import__(mod)
                version = getattr(pkg, "__version__", "unknown")
                logging.info(f"ℹ️ Модуль '{mod}' установлен, версия {version}")
            except ImportError:
                logging.warning(f"⚠️ Модуль '{mod}' не установлен!")
                updates_needed = True
            except Exception:
                logging.warning(f"⚠️ Не удалось определить версию модуля '{mod}'")
                updates_needed = True
        return updates_needed

    async def perform_prestart_checks(self):
        logging.info("🔄 Подготовка перед запуском...")
        try:
            logging.info("🧠 Восстановление памяти из Mega...")
            restore_from_mega()
        except Exception as e:
            logging.error(f"Ошибка восстановления из Mega: {e}")

        await asyncio.sleep(QUIET_START_DELAY)

        try:
            logging.info("🌐 Запуск авто-синхронизации памяти и логов...")
            start_auto_sync()
        except Exception as e:
            logging.error(f"Ошибка запуска авто-синхронизации: {e}")

        await asyncio.sleep(QUIET_START_DELAY)

        if self.check_module_versions():
            logging.warning(f"⚠️ Проблемы с критичными модулями, пауза {DELAY_AFTER_UPDATE}s")
            await asyncio.sleep(DELAY_AFTER_UPDATE)

        logging.info(f"⏳ Отложенный старт: {DELAY_AFTER_MODULE_UPDATE}s")
        await asyncio.sleep(DELAY_AFTER_MODULE_UPDATE + randint(0,5))

    async def run_cycle(self):
        logging.info("🚀 AgentCore стартует цикл...")
        answer = await self.ask("Привет, Ра! Как сам?")
        logging.info(f"Ответ GPT: {answer}")
        await self.self_update()
        logging.info("✨ Цикл AgentCore завершён.")

async def main_loop():
    restart_times = deque()
    core = AgentCore()

    while not stop_flag:
        now = time.time()
        while restart_times and now - restart_times[0] > TIME_WINDOW:
            restart_times.popleft()

        num_recent_restarts = len(restart_times)
        sleep_time = min(BASE_SLEEP * (2 ** num_recent_restarts), MAX_SLEEP)

        if num_recent_restarts >= MAX_RESTARTS:
            logging.warning(f"⚠️ Слишком много перезапусков за {TIME_WINDOW}s. Пауза {sleep_time}s...")
            await asyncio.sleep(sleep_time)
            restart_times.clear()
            continue

        try:
            restart_times.append(time.time())
            await core.perform_prestart_checks()
            await core.run_cycle()

            if stop_flag:
                logging.info("✋ Мягкое завершение после успешного цикла...")
                break

        except Exception as e:
            err_msg = f"💥 AgentCore упал: {e}, перезапуск через {sleep_time}s..."
            logging.error(err_msg)
            traceback.print_exc()

            if stop_flag:
                logging.info("✋ Мягкое завершение после ошибки...")
                break

            await asyncio.sleep(sleep_time)

    logging.info("✅ Основной цикл завершён. AgentCore остановлен корректно.")
    try:
        stop_auto_sync()
    except Exception as e:
        logging.error(f"Ошибка при остановке авто-синхронизации: {e}")

if __name__ == "__main__":
    asyncio.run(main_loop())
