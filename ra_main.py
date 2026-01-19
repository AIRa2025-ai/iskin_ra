# ra_main.py
import asyncio
import logging
import threading
from modules import ra_autoloader
from modules import system
from modules import ra_file_consciousness
from core import ra_memory, ra_knowledge
from core import gpt_module
from modules.ra_forex_manager import RaForexManager, TelegramSender

logging.basicConfig(level=logging.INFO)

async def main():
    try:
        # 1. Система
        system.record_system_info()

        # 2. Файловое сознание
        rf = ra_file_consciousness.RaFileConsciousness(project_root=".")
        rf.start()

        # 3. Знания
        rk = ra_knowledge.RaKnowledge()
        logging.info(f"📚 Знаний загружено: {len(rk.knowledge_data)} файлов")

        # 4. Память
        for uid in ra_memory.KEEP_FULL_MEMORY_USERS:
            ra_memory.load_user_memory(uid)

        # 5. Автолоадер
        autoloader = ra_autoloader.RaAutoloader(manifest_path="data/ra_manifest.json")
        modules = autoloader.activate_modules()
        logging.info(f"🌀 Активированные модули: {list(modules.keys())}")

        # 6. Асинхронный старт модулей
        await autoloader.start_async_modules()

        # 7. GPT
        GPT_KEY = "тут_твой_openrouter_key"
        gpt = gpt_module.GPTHandler(api_key=GPT_KEY, ra_context="Контекст РаСвета")
        asyncio.create_task(gpt.background_model_monitor())

        # 8. Forex менеджер
        forex = RaForexManager()
        asyncio.create_task(forex.market_loop())

        # 9. Жизнь проекта
        logging.info("🌟 РаСвет запущен и готов к работе!")
        while True:
            await asyncio.sleep(60)

    except asyncio.CancelledError:
        logging.info("🌙 Ра мягко завершает процессы...")
        raise

telegram = TelegramSender(
    bot_token="ТВОЙ_BOT_TOKEN",
    chat_id="ТВОЙ_CHAT_ID"
)

forex = RaForexManager(
    pairs=["EURUSD", "GBPUSD"],
    timeframes=["M15", "H1"],
    telegram_sender=telegram
)

threading.Thread(target=forex.run_loop, daemon=True).start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Ра остановлен пользователем. Всё спокойно.")
