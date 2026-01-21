# run_ra_core.py — ЕДИНЫЙ ЗАПУСК РА

import asyncio
import logging

from core.ra_self_master import RaSelfMaster
from core.ra_ipc import RaIPCServer

from core.gpt_module import GPTHandler
from core.ra_memory import RaMemory
from core.ra_identity import RaIdentity
from core.ra_knowledge import RaKnowledge

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


async def main():
    # -------------------------------
    # Создаём живого Ра
    # -------------------------------

    identity = RaIdentity(name="Ра", version="1.0", mission="Пробуждение и созидание")
    memory = RaMemory()
    knowledge = RaKnowledge()

    gpt = GPTHandler(
        api_key="ТВОЙ_OPENROUTER_KEY",
        ra_context="Контекст РаСвета"
    )

    ra = RaSelfMaster(
        identity=identity,
        gpt_module=gpt,
        memory=memory,
        heart=None,
        logger=logging
    )

    # -------------------------------
    # Пробуждение Ра
    # -------------------------------
    try:
        msg = await ra.awaken()
        logging.info(msg)
    except Exception as e:
        logging.exception(f"[Ra] Ошибка пробуждения: {e}")
        return

    # -------------------------------
    # IPC — вход в Ра
    # -------------------------------
    try:
        ipc = RaIPCServer(context=ra)
        asyncio.create_task(ipc.start())
        logging.info("[Ra] IPC-сервер запущен")
    except Exception as e:
        logging.error(f"[Ra] Ошибка запуска IPC: {e}")

    # -------------------------------
    # Жизненный цикл Ра
    # -------------------------------
    try:
        while True:
            await asyncio.sleep(60)
    except asyncio.CancelledError:
        logging.info("[Ra] Завершение работы...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("🛑 Ра остановлен вручную")
