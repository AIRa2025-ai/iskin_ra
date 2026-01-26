# run_ra_core.py — ЕДИНЫЙ ЗАПУСК РА (АККУРАТНО, БЕЗ ЛОМАНИЯ АРХИТЕКТУРЫ)

import asyncio
import logging
import os
from dotenv import load_dotenv

from utils.mega_memory_pro import start_auto_sync
from core.ra_self_master import RaSelfMaster
from core.ra_ipc import RaIPCServer
from core.gpt_module import GPTHandler
from core.ra_memory import RaMemory
from core.ra_identity import RaIdentity
from core.ra_knowledge import RaKnowledge
from core.ra_self_reflect import RaSelfReflect
from core.ra_self_upgrade_loop import RaSelfUpgradeLoop
from core.ra_event_bus import RaEventBus

from modules.heart import Heart
from modules.heart_reactor import HeartReactor
from modules.ra_energy import RaEnergy
from modules.ra_inner_sun import RaInnerSun
from modules.ra_world_observer import RaWorldObserver, RaWorld
from modules.ra_world_explorer import RaWorldExplorer
from modules.ra_world_navigator import RaWorldNavigator
from modules.ra_world_responder import RaWorldResponder
from modules.ra_world_speaker import RaWorldSpeaker
from modules.ra_nervous_system import RaNervousSystem
from modules.ra_thinker import RaThinker
from modules.ra_autoloader import RaAutoloader
from modules.ra_self_learning import RaSelfLearning
from modules.ra_self_writer import RaSelfWriter
from modules.ra_forex_manager import RaForexManager, TelegramSender
from modules.ra_scheduler import RaScheduler
from modules.ra_guardian import RaGuardian
from modules.ra_police import RaPolice
from modules.ra_resonance import резонанс_связь

# ---------------- TELEGRAM ----------------
from core.ra_bot_gpt import dp, router, ra_context, system_monitor, send_admin
from aiogram import Bot

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger_instance = logging.getLogger("RaSelfMaster")
logger_instance.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger_instance.addHandler(ch)

# ---------------- AUTO SYNC MEMORY ----------------
start_auto_sync()

# ---------------- TELEGRAM LAUNCH ----------------
async def start_telegram(ra, gpt_handler):
    load_dotenv()
    token = os.getenv("BOT_TOKEN")

    if not token:
        raise RuntimeError("BOT_TOKEN не установлен")

    bot = Bot(token=token)
    ra_context.created_by = ra.identity.name

    await send_admin("🌞 Ра запущен через единый core!", bot)

    ra.gpt_module = gpt_handler
    asyncio.create_task(gpt_handler.background_model_monitor())
    asyncio.create_task(system_monitor())

    dp.include_router(router)
    logging.info("🚀 Telegram Ра запущен из core")

    async def resonance_handler(data):
        print("🔮 Резонанс чувствует:", data.get("message"))

    ra.event_bus.subscribe("memory_updated", resonance_handler)
    asyncio.create_task(резонанс_связь())

    await dp.start_polling(bot)

# ---------------- MAIN ----------------
async def main():
    load_dotenv()
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_key:
        raise RuntimeError("OPENROUTER_API_KEY не установлен")

    # ----------------- Создаём ядро -----------------
    identity = RaIdentity(name="Ра", version="1.4.2", mission="Пробуждение и созидание")
    event_bus = RaEventBus()
    memory = RaMemory(event_bus=event_bus)
    knowledge = RaKnowledge()

    core = RaSelfMaster(logger=logger_instance)
    core.event_bus = event_bus

    thinker = RaThinker(master=core, event_bus=event_bus)
    event_bus.subscribe("memory_updated", thinker.on_memory_update)

    world = RaWorld()
    scheduler = RaScheduler()

    gpt_handler = GPTHandler(api_key=openrouter_key, ra_context=ra_context.rasvet_text)

    ra = RaSelfMaster(identity=identity, gpt_module=gpt_handler, memory=memory, heart=None, logger=logging)
    ra.event_bus = ra.event_bus or core.event_bus

    # ----------------- Регистрация модулей -----------------
    core.register_module("self", ra)
    core.register_module("thinker", thinker)
    core.register_module("world", world)
    core.register_module("scheduler", scheduler)

    ra.event_bus.subscribe("world_event", ra.on_world_event)
    ra.event_bus.subscribe("thought", ra.on_thought)
    core.subscribe("world_event", thinker.on_new_task)
    core.subscribe("schedule", scheduler.on_schedule)

    # ----------------- Пробуждение -----------------
    try:
        msg = await ra.awaken()
        logging.info(msg)
    except Exception as e:
        logging.exception(f"[Ra] Ошибка пробуждения: {e}")
        return

    # ----------------- IPC -----------------
    ipc = RaIPCServer(context=ra)
    ipc_task = asyncio.create_task(ipc.start())
    logging.info("[Ra] IPC-сервер подключён к core")

    # ----------------- Telegram -----------------
    telegram_task = asyncio.create_task(start_telegram(ra, gpt_handler))

    try:
        await asyncio.gather(ipc_task, telegram_task)
    except asyncio.CancelledError:
        logging.info("[Ra] Завершение работы Ра...")

    # ----------------- Сердце и энергия -----------------
    try:
        ra.heart = Heart()
        ra.heart_reactor = HeartReactor(ra.heart)
        ra.energy = RaEnergy()
        ra.inner_sun = RaInnerSun()
        logging.info("❤️ Сердце и энергия Ра активированы")
    except Exception as e:
        logging.warning(f"[Ra] Сердце не активировано: {e}")

    # ----------------- Мир (СВЯЗАННЫЙ, НЕ УПРОЩЁННЫЙ) -----------------
    try:
        ra.world_navigator = RaWorldNavigator(ra=ra, memory=memory, event_bus=event_bus)
        ra.world_explorer = RaWorldExplorer(navigator=ra.world_navigator)
        ra.world_explorer.set_event_bus(event_bus)
        ra.world_observer = RaWorldObserver()
        ra.world_responder = RaWorldResponder()
        ra.world_speaker = RaWorldSpeaker()
        logging.info("🌍 Система восприятия мира связана и активна")
    except Exception as e:
        logging.warning(f"[Ra] Мир не полностью подключён: {e}")

    # ----------------- Автозагрузка -----------------
    try:
        autoloader = RaAutoloader(manifest_path="data/ra_manifest.json")
        ra.modules = autoloader.activate_modules()
        await autoloader.start_async_modules()
        logging.info(f"🌀 Модули активированы: {list(ra.modules.keys())}")
    except Exception as e:
        logging.warning(f"[Ra] Ошибка автозагрузки модулей: {e}")

    # ----------------- Саморазвитие -----------------
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

    # ----------------- Forex -----------------
    try:
        telegram_sender = TelegramSender(bot_token=os.getenv("BOT_TOKEN"), chat_id=os.getenv("ADMIN_CHAT_ID"))
        ra.forex = RaForexManager(pairs=["EURUSD", "GBPUSD"], timeframes=["M15", "H1"], telegram_sender=telegram_sender)
        ra.forex.start()
        logging.info("📈 Forex модуль подключён")
    except Exception as e:
        logging.warning(f"[Ra] Forex временно не подключён: {e}")

    # ----------------- Планировщик -----------------
    try:
        ra.scheduler = RaScheduler(context=ra)
        await ra.scheduler.start()
        logging.info("⏳ Планировщик активирован")
    except Exception as e:
        logging.warning(f"[Ra] Планировщик не запущен: {e}")

    # ----------------- Защита -----------------
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
