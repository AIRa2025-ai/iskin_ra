# init_rasvet.py — проверка и загрузка данных RaSvet с Mega, автоперезапуск, прогресс, мягкое завершение
import os
import json
import logging
import zipfile
import requests
import signal
import asyncio
import traceback
import time
from collections import deque
from random import randint

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

QUIET_START_DELAY = 2
DELAY_AFTER_ERROR = 5
MAX_RESTARTS = 5
TIME_WINDOW = 60
BASE_SLEEP = 5
MAX_SLEEP = 120

stop_flag = False  # для мягкого завершения

def signal_handler(signum, frame):
    global stop_flag
    logging.info(f"✋ Получен сигнал {signum}, подготовка к завершению...")
    stop_flag = True

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

async def download_and_extract_with_progress(mega_url, archive_path, knowledge_folder):
    """Скачивание с прогрессом и распаковка архива"""
    if stop_flag:
        logging.info("✋ Прерывание перед началом загрузки RaSvet.")
        return False

    # скачивание
    logging.info("⬇️ Качаем архив из Mega...")
    try:
        with requests.get(mega_url, stream=True, timeout=30) as response:
            response.raise_for_status()
            total = int(response.headers.get('content-length', 0))
            downloaded = 0
            chunk_size = 8192
            last_percent = 0
            with open(archive_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if stop_flag:
                        logging.info("✋ Прерывание загрузки архива RaSvet.")
                        return False
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        percent = int(downloaded / total * 100)
                        if percent != last_percent and percent % 5 == 0:
                            logging.info(f"📥 Загрузка: {percent}%")
                            last_percent = percent
    except Exception as e:
        logging.error(f"❌ Ошибка при загрузке архива: {e}")
        await asyncio.sleep(DELAY_AFTER_ERROR + randint(0,3))
        return False

    # распаковка
    logging.info("📦 Распаковываем архив RaSvet...")
    try:
        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            zip_ref.extractall(knowledge_folder)
        os.remove(archive_path)
    except Exception as e:
        logging.error(f"❌ Ошибка при распаковке архива: {e}")
        await asyncio.sleep(DELAY_AFTER_ERROR + randint(0,3))
        return False

    logging.info("🌞 RaSvet готов к работе в папке RaSvet")
    return True

async def ensure_rasvet_data():
    await asyncio.sleep(QUIET_START_DELAY)
    if stop_flag:
        logging.info("✋ Прерывание перед началом проверки RaSvet.")
        return False

    try:
        with open("bot_config.json", "r", encoding="utf-8") as f:
            config = json.load(f)

        mega_url = config.get("mega_url")
        knowledge_folder = config.get("knowledge_folder", "RaSvet")
        archive_path = "RaSvet.zip"

        if os.path.exists(knowledge_folder):
            logging.info("✅ Папка RaSvet уже существует, пропускаем загрузку.")
            return True

        return await download_and_extract_with_progress(mega_url, archive_path, knowledge_folder)

    except FileNotFoundError:
        logging.error("❌ Файл bot_config.json не найден!")
    except Exception as e:
        logging.error(f"❌ Ошибка в ensure_rasvet_data: {e}")
        traceback.print_exc()
        await asyncio.sleep(DELAY_AFTER_ERROR + randint(0,3))
    return False

async def main_loop():
    """Автоперезапуск с контролем частоты и мягким завершением"""
    restart_times = deque()

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
            success = await ensure_rasvet_data()

            if success:
                logging.info("✅ Данные RaSvet загружены успешно, цикл завершён.")
                break

            if stop_flag:
                logging.info("✋ Мягкое завершение...")
                break

            logging.info(f"🔄 Попытка загрузки не удалась, повтор через {sleep_time}s...")
            await asyncio.sleep(sleep_time)

        except Exception as e:
            logging.error(f"💥 Основной цикл упал: {e}")
            traceback.print_exc()
            if stop_flag:
                logging.info("✋ Мягкое завершение после ошибки...")
                break
            await asyncio.sleep(sleep_time)

    logging.info("✅ Основной цикл init_rasvet завершён корректно.")

if __name__ == "__main__":
    asyncio.run(main_loop())
