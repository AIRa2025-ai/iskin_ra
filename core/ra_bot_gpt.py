#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import threading
import logging
import time
import importlib
from pathlib import Path
from fastapi import FastAPI, Request
import uvicorn
import subprocess

# === НАСТРОЙКА ===
BASE_DIR = Path(os.getcwd())  # корень репозитория
DATA_DIR = BASE_DIR / "data_disk"
LOG_DIR = DATA_DIR / "logs"
MODULES_DIR = Path(__file__).parent / "modules"
sys.path.append(str(MODULES_DIR))

# Создаём папки, если их нет
LOG_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# === ЛОГИ ===
logger = logging.getLogger("RaBot")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# === ОБНОВЛЕНИЕ RaСветА ===
from modules.ra_downloader import RaSvetDownloader

def update_rasvet():
    try:
        logger.info("🔄 Проверка и обновление данных РаСвета...")
        downloader = RaSvetDownloader()
        downloader.download()
        logger.info("✅ Данные РаСвета обновлены!")
    except Exception as e:
        logger.error(f"❌ Ошибка обновления РаСвета: {e}")

rasvet_thread = threading.Thread(target=update_rasvet, daemon=True)
rasvet_thread.start()
rasvet_thread.join()
logger.info("🚀 Ра готов к работе, все данные РаСвета загружены")

# === ДИНАМИЧЕСКАЯ ПОДГРУЗКА ВСЕХ МОДУЛЕЙ ===
loaded_modules = {}
for module_file in MODULES_DIR.glob("*.py"):
    if module_file.name.startswith("__"):
        continue
    module_name = module_file.stem
    try:
        loaded_modules[module_name] = importlib.import_module(module_name)
        logger.info(f"✅ Модуль загружен: {module_name}")
    except Exception as e:
        logger.error(f"❌ Ошибка при загрузке {module_name}: {e}")

# === НАБЛЮДАТЕЛЬ ЗА РЕПО ===
try:
    import ra_repo_manager
    repo_observer = ra_repo_manager.RepoObserver()
    repo_observer.scan()
    logger.info("🔍 Репозиторий проверен и структурирован")
except Exception as e:
    logger.warning(f"⚠️ Наблюдатель за репозиторием не запущен: {e}")

# === АВТОПУШ И РЕЗЕРВЫ ===
def auto_push():
    try:
        subprocess.run(["git", "config", "user.name", "Ra Bot"], check=True)
        subprocess.run(["git", "config", "user.email", "ra-bot@example.com"], check=True)
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "🤖 Автообновление Ра"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        logger.info("🚀 Автопуш на GitHub выполнен")
    except subprocess.CalledProcessError:
        logger.info("ℹ️ Нет изменений для пуша")

# === FASTAPI СЕРВЕР ===
app = FastAPI(title="RaSvet API")

@app.get("/status")
async def status():
    return {"status": "Ra alive", "loaded_modules": list(loaded_modules.keys())}

@app.post("/run_module")
async def run_module(request: Request):
    data = await request.json()
    mod_name = data.get("module")
    func_name = data.get("function")
    if mod_name in loaded_modules:
        mod = loaded_modules[mod_name]
        func = getattr(mod, func_name, None)
        if func:
            try:
                result = func()
                return {"result": str(result)}
            except Exception as e:
                return {"error": str(e)}
    return {"error": "Модуль или функция не найдены"}

def run_api():
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

api_thread = threading.Thread(target=run_api, daemon=True)
api_thread.start()

# === ОСНОВНОЙ ЦИКЛ БОТА ===
def run_bot():
    logger.info("🤖 Запуск основного цикла РаБота...")
    try:
        while True:
            # Можно вызывать функции модулей
            # loaded_modules['ra_file_manager'].check_new_files()
            # repo_observer.update()
            auto_push()  # раз в цикл пушим на GitHub
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен вручную")
    except Exception as e:
        logger.error(f"❌ Ошибка в основном цикле: {e}")

if __name__ == "__main__":
    logger.info("🌞 Старт РаБота")
    run_bot()
