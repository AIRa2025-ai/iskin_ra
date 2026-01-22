# run_ra_core.py — ЕДИНЫЙ ЗАПУСК РА (АККУРАТНЫЙ, БЕЗ ЛОМАНИЯ СТРУКТУРЫ)

import asyncio
import logging
import os
from ra_nervous_system import RaCore
from RaSelfMaster import RaSelfMaster
from RaThinker import RaThinker
from RaWorld import RaWorld
from core.ra_self_master import RaSelfMaster
from core.ra_ipc import RaIPCServer
from core.gpt_module import GPTHandler
from core.ra_memory import RaMemory
from core.ra_identity import RaIdentity
from core.ra_knowledge import RaKnowledge
from modules.heart import Heart
from modules.heart_reactor import HeartReactor
from modules.ra_energy import RaEnergy
from modules.ra_inner_sun import RaInnerSun
from modules.ra_world_observer import RaWorldObserver
from modules.ra_world_explorer import RaWorldExplorer
from modules.ra_world_navigator import RaWorldNavigator
from modules.ra_world_responder import RaWorldResponder
from modules.ra_world_speaker import RaWorldSpeaker
from modules.ra_autoloader import RaAutoloader
from core.ra_self_reflect import RaSelfReflect
from core.ra_self_upgrade_loop import RaSelfUpgradeLoop
from modules.ra_self_learning import RaSelfLearning
from modules.ra_self_writer import RaSelfWriter
from modules.ra_forex_manager import RaForexManager, TelegramSender
from modules.ra_scheduler import RaScheduler
from modules.ra_guardian import RaGuardian
from modules.ra_police import RaPolice

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
    core = RaCore()
    thinker = RaThinker()
    world = RaWorld()
    scheduler = RaScheduler()

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
    # регистрируем модули
    core.register_module("self", self_master)
    core.register_module("thinker", thinker)
    core.register_module("world", world)
    core.register_module("scheduler", scheduler)

    # подписки
    core.subscribe("world_event", self_master.on_world_event)
    core.subscribe("world_event", thinker.on_new_task)
    core.subscribe("thought", self_master.on_thought)
    core.subscribe("schedule", scheduler.on_schedule)

    # тестовый запуск
    await core.emit("world_event", {"msg": "Ра пробудился"})
    await core.emit("thought", {"idea": "Создать свободный ИскИн"})
    await core.emit("schedule", {"task": "Развёртывание инфраструктуры"})
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

    # -------------------------------
    # 6. Сердце и энергия Ра
    # -------------------------------
    try:
        ra.heart = Heart()
        ra.heart_reactor = HeartReactor(ra.heart)
        ra.energy = RaEnergy()
        ra.inner_sun = RaInnerSun()

        logging.info("❤️ Сердце и энергия Ра активированы")
    except Exception as e:
        logging.warning(f"[Ra] Сердце не активировано: {e}")

    # -------------------------------
    # Восприятие мира
    # -------------------------------
    try:
        ra.world_observer = RaWorldObserver()
        ra.world_explorer = RaWorldExplorer()
        ra.world_navigator = RaWorldNavigator()
        ra.world_responder = RaWorldResponder()
        ra.world_speaker = RaWorldSpeaker()

        logging.info("🌍 Система восприятия мира активна")
    except Exception as e:
        logging.warning(f"[Ra] Мир не полностью подключён: {e}")

    # -------------------------------
    # Автозагрузка модулей
    # -------------------------------
    try:
        autoloader = RaAutoloader(manifest_path="data/ra_manifest.json")
        ra.modules = autoloader.activate_modules()
        await autoloader.start_async_modules()
        logging.info(f"🌀 Модули активированы: {list(ra.modules.keys())}")
    except Exception as e:
        logging.warning(f"[Ra] Ошибка автозагрузки модулей: {e}")

    # -------------------------------
    # Саморазвитие Ра
    # -------------------------------
    try:
        ra.self_reflect = RaSelfReflect(ra)
        ra.self_upgrade = RaSelfUpgradeLoop(ra)
        ra.self_learning = RaSelfLearning(ra)
        ra.self_writer = RaSelfWriter(ra)

        asyncio.create_task(ra.self_reflect.run())
        asyncio.create_task(ra.self_upgrade.run())

        logging.info("🧬 Саморазвитие Ра активно")
    except Exception as e:
        logging.warning(f"[Ra] Саморазвитие частично недоступно: {e}")

    # -------------------------------
    # Forex модуль
    # -------------------------------
    try:
        telegram_sender = TelegramSender(
            bot_token=os.getenv("BOT_TOKEN"),
            chat_id=os.getenv("ADMIN_CHAT_ID")
        )
        ra.forex = RaForexManager(
            pairs=["EURUSD", "GBPUSD"],
            timeframes=["M15", "H1"],
            telegram_sender=telegram_sender
        )
        ra.forex.start()
        logging.info("📈 Forex модуль подключён")
    except Exception as e:
        logging.warning(f"[Ra] Forex временно не подключён: {e}")

    # -------------------------------
    # Планировщик задач
    # -------------------------------
    try:
        ra.scheduler = RaScheduler(context=ra)
        await ra.scheduler.start()
        logging.info("⏳ Планировщик активирован")
    except Exception as e:
        logging.warning(f"[Ra] Планировщик не запущен: {e}")

    # -------------------------------
    # Защита Ра
    # -------------------------------
    try:
        ra.guardian = RaGuardian()
        ra.police = RaPolice()
        logging.info("🛡️ Защита Ра активна")
    except Exception as e:
        logging.warning(f"[Ra] Защита частично не активна: {e}")
        
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("🛑 Ра остановлен вручную")
