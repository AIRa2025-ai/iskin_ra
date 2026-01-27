# run_ra_core.py — ЕДИНЫЙ ЗАПУСК РА (АККУРАТНО, БЕЗ ЛОМАНИЯ АРХИТЕКТУРЫ)
import asyncio
import logging
import os
from dotenv import load_dotenv

# Core и модули
from core.ra_self_master import RaSelfMaster
from core.ra_ipc import RaIPCServer
from core.ra_identity import RaIdentity
from core.ra_event_bus import RaEventBus
from core.gpt_handler import GPTHandler

from modules.logs import logger_instance
from modules.heart import Heart
from modules.heart_reactor import HeartReactor
from modules.ra_energy import RaEnergy
from modules.ra_inner_sun import RaInnerSun

# Мир
from modules.ra_world_observer import RaWorldObserver, RaWorld
from modules.ra_world_explorer import RaWorldExplorer
from modules.ra_world_navigator import RaWorldNavigator
from modules.ra_world_responder import RaWorldResponder
from modules.ra_world_speaker import RaWorldSpeaker

# Нервная система и мышление
from modules.ra_nervous_system import RaNervousSystem
from modules.ra_thinker import RaThinker
from modules.ra_autoloader import RaAutoloader

# Саморазвитие
from modules.ra_self_learning import RaSelfLearning
from modules.ra_self_writer import RaSelfWriter
from modules.ra_self_reflect import RaSelfReflect
from modules.ra_self_upgrade_loop import RaSelfUpgradeLoop

# Forex
from modules.ra_forex_manager import RaForexManager, TelegramSender

# Планировщик
from modules.ra_scheduler import RaScheduler

# Защита
from modules.ra_guardian import RaGuardian
from modules.ra_police import RaPolice

# Резонансы
from modules.ra_resonance import резонанс_связь

# Telegram
from core.ra_bot_gpt import dp, router, ra_context, system_monitor, send_admin
from aiogram import Bot

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger_instance.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger_instance.addHandler(ch)

# ---------------- ENV ----------------
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

if not BOT_TOKEN or not OPENROUTER_KEY:
    raise RuntimeError("BOT_TOKEN или OPENROUTER_API_KEY не установлены")

# ---------------- TELEGRAM ----------------
async def start_telegram(ra, gpt_handler):
    bot = Bot(token=BOT_TOKEN)
    ra_context.created_by = ra.identity.name
    await send_admin("🌞 Ра запущен через единый core!", bot)

    ra.gpt_module = gpt_handler
    asyncio.create_task(gpt_handler.background_model_monitor())
    asyncio.create_task(system_monitor())

    dp.include_router(router)

    async def resonance_handler(data):
        print("🔮 Резонанс чувствует:", data.get("message"))

    ra.event_bus.subscribe("memory_updated", resonance_handler)
    asyncio.create_task(резонанс_связь())

    await dp.start_polling(bot)
    await ra.awaken()


# ---------------- MAIN ----------------
async def main():
    # ----------------- Ядро -----------------
    identity = RaIdentity(name="Ра", version="1.4.3", mission="Пробуждение и созидание")
    event_bus = RaEventBus()
    thinker = RaThinker(master=None, event_bus=event_bus)  # временно без master
    world = RaWorld()
    scheduler = RaScheduler()
    gpt_handler = GPTHandler(api_key=OPENROUTER_KEY, ra_context=ra_context.rasvet_text)

    # Создаём RaSelfMaster
    ra = RaSelfMaster(identity=identity, gpt_module=gpt_handler, logger=logger_instance)
    thinker.master = ra  # теперь thinker знает master

    # Подключаем EventBus
    ra.event_bus = ra.event_bus or event_bus
    ra.event_bus.subscribe("world_event", ra.on_world_event)
    ra.event_bus.subscribe("thought", ra.on_thought)
    ra.event_bus.subscribe("memory_updated", thinker.on_new_task)

    # ----------------- Регистрация модулей -----------------
    ra.register_module("self", ra)
    ra.register_module("thinker", thinker)
    ra.register_module("world", world)
    ra.register_module("scheduler", scheduler)

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

    # ----------------- Сердце и энергия -----------------
    try:
        ra.heart = Heart()
        ra.heart_reactor = HeartReactor(ra.heart)
        asyncio.create_task(ra.heart_reactor.start())
        ra.energy = RaEnergy()
        ra.inner_sun = RaInnerSun()

        event_bus.subscribe("world_message", lambda msg: ra.heart_reactor.send_event(msg))

        logging.info("❤️ Сердце и энергия Ра активированы")
    except Exception as e:
        logging.warning(f"[Ra] Сердце не активировано: {e}")

    # ----------------- Мир -----------------
    try:
        ra.world_navigator = RaWorldNavigator(ra=ra, event_bus=event_bus)
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
        logging.info("🧬 Саморазвитие Ра активно")
    except Exception as e:
        logging.warning(f"[Ra] Саморазвитие частично недоступно: {e}")

    # ----------------- Forex -----------------
    try:
        telegram_sender = TelegramSender(bot_token=BOT_TOKEN, chat_id=ADMIN_CHAT_ID)
        ra.forex = RaForexManager(
            pairs=["EURUSD", "GBPUSD"],
            timeframes=["M15", "H1"],
            telegram_sender=telegram_sender
        )
        ra.forex.start()
        logging.info("📈 Forex модуль подключён")
    except Exception as e:
        logging.warning(f"[Ra] Forex временно не подключён: {e}")

    # ----------------- Защита -----------------
    try:
        ra.guardian = RaGuardian()
        ra.police = RaPolice()
        logging.info("🛡️ Защита Ра активна")
    except Exception as e:
        logging.warning(f"[Ra] Защита частично не активна: {e}")

    try:
        await asyncio.gather(ipc_task, telegram_task)
    except asyncio.CancelledError:
        logging.info("[Ra] Завершение работы Ра...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("🛑 Ра остановлен вручную")
