# run_ra_core.py
import asyncio
import logging

from modules.ra_self_master import RaSelfMaster
from modules.ra_autoloader import RaAutoloader

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

async def main():
    # 1️⃣ Инициализируем самоконтроль Ра
    ra = RaSelfMaster()

    # 2️⃣ Пробуждение (активируем автолоадер, загружаем манифест, старт полиции)
    ra.awaken()

    # 3️⃣ Получаем автолоадер и активируем все модули
    autoloader = ra.autoloader
    if autoloader:
        autoloader.activate_modules()
        await autoloader.start_async_modules()

    # 4️⃣ Специальная инициализация ключевых модулей
    modules_to_check = [
        "market_watcher",
        "ra_world_navigator",
        "ra_scheduler",
        "ra_self_learning"
    ]
    for name in modules_to_check:
        mod = autoloader.get_module(name)
        if mod:
            logging.info(f"[CORE] Модуль {name} готов к работе.")
            # Если есть start() coroutine — запускаем
            if hasattr(mod, "start") and asyncio.iscoroutinefunction(mod.start):
                asyncio.create_task(mod.start())

    # 5️⃣ Основной цикл — можно добавить наблюдение, анализ, сигналы
    try:
        while True:
            # Периодический лог статуса модулей
            status = autoloader.status()
            logging.info(f"[CORE] Status: {status}")
            await asyncio.sleep(60)  # проверка каждую минуту
    except asyncio.CancelledError:
        # Остановка всех async модулей при завершении
        if autoloader:
            await autoloader.stop_async_modules()
        logging.info("[CORE] Ра завершает работу.")

if __name__ == "__main__":
    asyncio.run(main())
