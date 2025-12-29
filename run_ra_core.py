# run_ra_core.py — CORE-запуск Ра (чистый, без дублей)

import asyncio
import logging
from core.ra_self_master import RaSelfMaster

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")


async def monitor_new_modules(autoloader, interval=30):
    known = set(autoloader.modules.keys())
    while True:
        await asyncio.sleep(interval)
        current = set(autoloader.modules.keys())
        new = current - known

        for name in new:
            mod = autoloader.modules.get(name)
            if mod and hasattr(mod, "start") and asyncio.iscoroutinefunction(mod.start):
                logging.info(f"[CORE] Новый модуль активирован: {name}")
                asyncio.create_task(mod.start())

        known = current


async def main():
    ra = RaSelfMaster()
    await ra.awaken()

    autoloader = getattr(ra, "autoloader", None)
    if not autoloader:
        logging.error("[CORE] autoloader не найден")
        return

    autoloader.activate_modules()
    await autoloader.start_async_modules()

    asyncio.create_task(monitor_new_modules(autoloader))

    while True:
        logging.info(f"[CORE] Status: {autoloader.status()}")
        await asyncio.sleep(60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("🛑 CORE остановлен")
    except Exception:
        logging.exception("💥 Критическая ошибка CORE")
