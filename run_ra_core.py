# run_ra_core.py — CORE + IPC для RaSelfMaster
import asyncio
import logging
from core.ra_self_master import RaSelfMaster
from core.ra_ipc import RaIPCServer

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


async def monitor_new_modules(autoloader, interval=30):
    """Динамическое отслеживание новых модулей и их запуск"""
    known = set(autoloader.modules.keys())
    while True:
        await asyncio.sleep(interval)
        current = set(autoloader.modules.keys())
        new = current - known

        for name in new:
            mod = autoloader.modules.get(name)
            if mod and hasattr(mod, "start") and asyncio.iscoroutinefunction(mod.start):
                logging.info(f"[CORE] Новый модуль активирован: {name}")
                try:
                    asyncio.create_task(mod.start())
                except Exception as e:
                    logging.warning(f"[CORE] Ошибка запуска модуля {name}: {e}")

        known = current


async def main():
    # -------------------------------
    # Инициализация RaSelfMaster
    # -------------------------------
    ra = RaSelfMaster()
    try:
        await ra.awaken()
    except Exception as e:
        logging.warning(f"[RaSelfMaster] awaken error: {e}")

    # -------------------------------
    # Автолоадер модулей
    # -------------------------------
    autoloader = getattr(ra, "autoloader", None)
    if not autoloader:
        logging.error("[CORE] autoloader не найден")
        return

    try:
        autoloader.activate_modules()
        await autoloader.start_async_modules()
    except Exception as e:
        logging.warning(f"[CORE] Ошибка активации модулей: {e}")

    # -------------------------------
    # Запуск мониторинга новых модулей
    # -------------------------------
    asyncio.create_task(monitor_new_modules(autoloader))

    # -------------------------------
    # Старт IPC-сервера для взаимодействия с Telegram
    # -------------------------------
    try:
        ipc = RaIPCServer(context=ra)
        asyncio.create_task(ipc.start())
        logging.info("[CORE] IPC-сервер запущен")
    except Exception as e:
        logging.error(f"[CORE] Ошибка запуска IPC: {e}")

    # -------------------------------
    # Основной цикл
    # -------------------------------
    try:
        while True:
            status_info = autoloader.status() if autoloader else {}
            logging.info(f"[CORE] Status: {status_info}")
            await asyncio.sleep(60)
    except asyncio.CancelledError:
        logging.info("[CORE] Завершение работы CORE...")
    except Exception as e:
        logging.exception(f"[CORE] Критическая ошибка в основном цикле: {e}")


# -------------------------------
# Запуск
# -------------------------------
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("🛑 CORE остановлен вручную")
    except Exception:
        logging.exception("💥 Критическая ошибка при запуске CORE")
