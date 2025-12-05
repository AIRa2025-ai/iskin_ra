# run_ra_core.py — Динамический автопилот для Ра с автолоадером и async модулями
import asyncio
import logging
from modules.ra_self_master import RaSelfMaster

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

async def monitor_new_modules(autoloader, interval=30):
    """Проверка новых модулей каждые interval секунд и запуск их, если есть start()"""
    known_modules = set(autoloader.modules.keys())
    while True:
        await asyncio.sleep(interval)
        current_modules = set(autoloader.modules.keys())
        new_modules = current_modules - known_modules
        for name in new_modules:
            mod = autoloader.modules[name]
            if mod:
                logging.info(f"[CORE] Новый модуль {name} найден и готов к работе.")
                if hasattr(mod, "start") and asyncio.iscoroutinefunction(mod.start):
                    asyncio.create_task(mod.start())
        known_modules = current_modules

async def main():
    # 1️⃣ Инициализация самоконтроля Ра
    ra = RaSelfMaster()

    # 2️⃣ Пробуждение (автолоадер, манифест, полиция)
    await ra.awaken() if asyncio.iscoroutinefunction(ra.awaken) else ra.awaken()

    # 3️⃣ Получаем автолоадер и активируем все модули
    autoloader = getattr(ra, "autoloader", None)
    if autoloader:
        autoloader.activate_modules()
        await autoloader.start_async_modules()

        # Запускаем существующие модули
        for name, mod in autoloader.modules.items():
            if mod and hasattr(mod, "start") and asyncio.iscoroutinefunction(mod.start):
                asyncio.create_task(mod.start())

        # 4️⃣ Старт динамического мониторинга новых модулей
        asyncio.create_task(monitor_new_modules(autoloader))

    # 5️⃣ Основной цикл наблюдения и логирования
    try:
        while True:
            if autoloader:
                status = autoloader.status()
                logging.info(f"[CORE] Status: {status}")
            await asyncio.sleep(60)
    except asyncio.CancelledError:
        logging.info("[CORE] Завершение работы Ра...")
        if autoloader:
            await autoloader.stop_async_modules()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("🛑 Остановка run_ra_core")
    except Exception:
        logging.exception("Критическая ошибка при запуске run_ra_core")
