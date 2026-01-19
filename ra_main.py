# ra_main.py
import asyncio
import logging
from modules import ra_autoloader
from modules import system
from modules import ra_file_consciousness
from core import ra_memory, ra_knowledge
from core import gpt_module
from modules.ra_forex_manager import RaForexManager

logging.basicConfig(level=logging.INFO)
forex = RaForexManager()
asyncio.create_task(forex.market_loop())
async def main():
    try:
        # -------------------------------
        # 1. Система и мониторинг
        # -------------------------------
        system.record_system_info()

        # -------------------------------
        # 2. Файловое сознание
        # -------------------------------
        rf = ra_file_consciousness.RaFileConsciousness(project_root=".")
        rf.start()

        # -------------------------------
        # 3. Хранилище знаний
        # -------------------------------
        rk = ra_knowledge.RaKnowledge()
        logging.info(f"📚 Знаний загружено: {len(rk.knowledge_data)} файлов")

        # -------------------------------
        # 4. Память пользователей
        # -------------------------------
        for uid in ra_memory.KEEP_FULL_MEMORY_USERS:
            ra_memory.load_user_memory(uid)

        # -------------------------------
        # 5. Автолоадер модулей
        # -------------------------------
        autoloader = ra_autoloader.RaAutoloader(manifest_path="data/ra_manifest.json")
        modules = autoloader.activate_modules()
        logging.info(f"🌀 Активированные модули: {list(modules.keys())}")

        # -------------------------------
        # 6. Асинхронный старт модулей
        # -------------------------------
        await autoloader.start_async_modules()

        # -------------------------------
        # 7. GPT Handler
        # -------------------------------
        GPT_KEY = "тут_твой_openrouter_key"
        gpt = gpt_module.GPTHandler(api_key=GPT_KEY, ra_context="Контекст РаСвета")

        # Пример запроса
        response = await gpt.safe_ask(
            user_id="example_user",
            messages=[{"role": "user", "content": "Привет, Ра!"}]
        )
        logging.info(f"🤖 GPT ответ: {response}")

        # -------------------------------
        # 8. Фоновая проверка GPT моделей
        # -------------------------------
        asyncio.create_task(gpt.background_model_monitor())

        # -------------------------------
        # 9. Проект живёт
        # -------------------------------
        logging.info("🌟 РаСвет запущен и готов к работе!")
        while True:
            await asyncio.sleep(60)

    except asyncio.CancelledError:
        logging.info("🌙 Ра мягко завершает внутренние процессы...")
        raise

async def market_loop():
    while True:
        signals = forex.update()
        for s in signals:
            logging.info(f"🧭 Сигнал Ра: {s}")
        await asyncio.sleep(300)

asyncio.create_task(market_loop())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Ра остановлен пользователем. Всё спокойно и под контролем.")
