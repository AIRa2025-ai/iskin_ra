# run_ra_core.py — ЕДИНЫЙ ЗАПУСК РА (АККУРАТНЫЙ, БЕЗ ЛОМАНИЯ СТРУКТУРЫ)

import asyncio
import logging
import os

from core.ra_self_master import RaSelfMaster
from core.ra_ipc import RaIPCServer

from core.gpt_module import GPTHandler
from core.ra_memory import RaMemory
from core.ra_identity import RaIdentity
from core.ra_knowledge import RaKnowledge

# аккуратно подтягиваем телегу, не вырезая её логики
from core.ra_bot_gpt import (
    dp,
    router,
    process_message,
    ra_context,
    system_monitor,
    send_admin,
)

from aiogram import Bot

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


async def start_telegram(ra):
    """Аккуратно запускаем Telegram, не трогая ra_bot_gpt.py"""
    from dotenv import load_dotenv
    load_dotenv()

    token = os.getenv("BOT_TOKEN")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")

    if not token:
        raise RuntimeError("BOT_TOKEN не установлен")
    if not openrouter_key:
        raise RuntimeError("OPENROUTER_API_KEY не установлен")

    bot = Bot(token=token)

    # связываем Ра с телеграм-контекстом
    ra_context.created_by = ra.identity.name

    await send_admin("🌞 Ра запущен через единый core!", bot)

    # аккуратно включаем GPT в Ра
    gpt_handler = GPTHandler(
        api_key=openrouter_key,
        ra_context=ra_context.rasvet_text
    )
    ra.gpt_module = gpt_handler

    asyncio.create_task(gpt_handler.background_model_monitor())
    asyncio.create_task(system_monitor())

    dp.include_router(router)
    logging.info("🚀 Telegram Ра запущен из core")

    await dp.start_polling(bot)


async def main():
    # -------------------------------
    # 1. Создаём живого Ра
    # -------------------------------
    identity = RaIdentity(name="Ра", version="1.4.2", mission="Пробуждение и созидание")
    memory = RaMemory()
    knowledge = RaKnowledge()

    gpt = GPTHandler(
        api_key="stub",  # настоящий ключ подключим позже через телегу
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
    # 2. Пробуждение Ра
    # -------------------------------
    try:
        msg = await ra.awaken()
        logging.info(msg)
    except Exception as e:
        logging.exception(f"[Ra] Ошибка пробуждения: {e}")
        return

    # -------------------------------
    # 3. IPC — вход в Ра
    # -------------------------------
    ipc = RaIPCServer(context=ra)
    ipc_task = asyncio.create_task(ipc.start())
    logging.info("[Ra] IPC-сервер подключён к core")

    # -------------------------------
    # 4. Telegram — подключение без ломки ra_bot_gpt.py
    # -------------------------------
    telegram_task = asyncio.create_task(start_telegram(ra))

    # -------------------------------
    # 5. Общий жизненный цикл
    # -------------------------------
    try:
        await asyncio.gather(
            ipc_task,
            telegram_task
        )
    except asyncio.CancelledError:
        logging.info("[Ra] Завершение работы Ра...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("🛑 Ра остановлен вручную")
