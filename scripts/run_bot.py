# scripts/run_bot.py — serverless версия для Railway Free Plan
import asyncio
import logging
import os
import sys

# Добавляем путь к корню проекта, чтобы импорты работали
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT_DIR)

from core.ra_bot_gpt import main as run_ra_bot

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("🚀 Запуск РаСвет (serverless режим)...")

    try:
        asyncio.run(run_ra_bot())  # просто запускаем, без бесконечного цикла
        logging.info("✅ РаСвет завершил работу без ошибок.")
    except KeyboardInterrupt:
        logging.info("🛑 Остановка вручную.")
    except Exception as e:
        logging.error(f"💥 Ошибка при запуске Ра: {e}")
