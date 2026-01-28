# run_ra_core.py — ЕДИНЫЙ ЗАПУСК РА (финальный, с HeartReactor v2.0)
import asyncio
import logging
import os
import random
from dotenv import load_dotenv
from typing import List, Dict, Any

# Core и модули
from core.ra_self_master import RaSelfMaster
from core.ra_ipc import RaIPCServer
from core.ra_identity import RaIdentity
from core.ra_event_bus import RaEventBus
from core.gpt_handler import GPTHandler
from modules.logs import logger_instance
from modules.heart import Heart
from modules.ra_energy import RaEnergy
from modules.ra_inner_sun import RaInnerSun
from modules import module_generator as mg

# Мир
from modules.ra_world_observer import RaWorldObserver, RaWorld
from modules.ra_world_explorer import RaWorldExplorer
from modules.ra_world_navigator import RaWorldNavigator
from modules.ra_world_responder import RaWorldResponder
from modules.ra_world_speaker import RaWorldSpeaker

# Нервная система и мышление
from modules.ra_thinker import RaThinker
from modules.ra_autoloader import RaAutoloader
from modules.ra_nervous_system import RaNervousSystem

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
    
# ======СОЗДАЕМ ОБЪЕКТЫ ===========================
file_core = RaFileCore(project_root=".")
git_keeper = RaGitKeeper(repo_path=".")
knowledge = RaKnowledge(knowledge_dir="knowledge")
thinker = RaThinker(master=master, file_consciousness=file_core.manager, gpt_module=gpt_module, event_bus=event_bus)
scheduler = RaScheduler(thinker=thinker, upgrade_loop=thinker, event_bus=event_bus)
mg.создать_модуль("СветДня", "Поток света активирован")
# ---------------- HeartReactor v2.0 ----------------
class HeartReactor:
    def __init__(self, heart=None):
        self.heart = heart
        self.name = "Heart Reactor v2.0"
        self.listeners = []
        self.event_queue = asyncio.Queue()
        self.future_events_queue = asyncio.Queue()
        self.is_active = True

    async def start(self):
        while self.is_active:
            try:
                if not self.event_queue.empty():
                    event = await self.event_queue.get()
                    response = self._react(event)
                    logging.info(f"[HeartReactor] {response}")
                    await self.notify_listeners(event)

                if not self.future_events_queue.empty():
                    future_batch = await self.future_events_queue.get()
                    await self._analyze_future(future_batch)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"[HeartReactor] Ошибка: {e}")
            await asyncio.sleep(0.05)

    def _react(self, event: str) -> str:
        e = event.lower()
        if "свет" in e:
            return "💖 Сердце наполняется светом и излучает любовь"
        elif "тревога" in e:
            return "💓 Сердце волнуется, но сохраняет спокойствие"
        elif "пульс" in e and self.heart:
            return self.heart.beat()
        elif "мысль" in e:
            return f"🧠 Сердце думает над событием: {event}"
        elif "резонанс" in e:
            return f"🔮 Сердце чувствует резонанс: {event}"
        elif "опасность" in e:
            return f"⚠️ Сердце насторожено! {event}"
        else:
            return f"💡 Сердце анализирует событие: {event}"

    def send_event(self, event: str):
        self.event_queue.put_nowait(event)

    def send_future_events(self, events: List[Dict[str, Any]]):
        self.future_events_queue.put_nowait(events)

    async def _analyze_future(self, events: List[Dict[str, Any]]):
        if not events:
            return
        best_event = None
        best_score = float("-inf")
        for evt in events:
            score = self._evaluate_event(evt)
            evt["score"] = score
            if score > best_score:
                best_score = score
                best_event = evt
        if best_event:
            msg = f"🔮 Предчувствие будущего: выбрано оптимальное -> {best_event['description']} (score={best_score})"
            logging.info(f"[HeartReactor] {msg}")
            await self.notify_listeners(best_event)

    def _evaluate_event(self, event: Dict[str, Any]) -> float:
        base_score = event.get("impact", 0)
        quantum_fluctuation = random.uniform(-5, 5)
        type_bonus = {"свет": 10, "тревога": -5, "опасность": -10, "радость": 8, "творчество": 12}
        type_score = type_bonus.get(event.get("type", ""), 0)
        return base_score + quantum_fluctuation + type_score

    def register_listener(self, listener_coro):
        self.listeners.append(listener_coro)

    async def notify_listeners(self, event: Any):
        for listener in self.listeners:
            try:
                await listener(event)
            except Exception as e:
                logging.warning(f"[HeartReactor] Ошибка в listener: {e}")

    def stop(self):
        self.is_active = False

    def status(self) -> str:
        return f"{self.name} активен, слушателей: {len(self.listeners)}"

# ---------------- TELEGRAM ----------------
async def start_telegram(ra, gpt_handler):
    bot = Bot(token=BOT_TOKEN)
    ra_context.created_by = ra.identity.name
    await send_admin("🌞 Ра подключён к Telegram!", bot)
    ra.gpt_module = gpt_handler
    asyncio.create_task(gpt_handler.background_model_monitor())
    asyncio.create_task(system_monitor())
    dp.include_router(router)

    async def resonance_handler(data):
        logging.info(f"🔮 Резонанс чувствует: {data.get('message')}")
    ra.event_bus.subscribe("memory_updated", resonance_handler)
    asyncio.create_task(резонанс_связь())
    await dp.start_polling(bot)

# ---------------- Генератор событий будущего ----------------
async def generate_future_events(heart_reactor: HeartReactor):
    """Каждые 5 секунд создаёт новые будущие события"""
    types = ["свет", "тревога", "опасность", "радость", "творчество"]
    while heart_reactor.is_active:
        batch = [{"description": f"Событие {i}", "impact": random.randint(1, 20), "type": random.choice(types)}
                 for i in range(random.randint(2, 5))]
        heart_reactor.send_future_events(batch)
        await asyncio.sleep(5)

# ---------------- Визуализация предчувствий ----------------
async def visualize_future_events(heart_reactor: HeartReactor):
    while heart_reactor.is_active:
        await asyncio.sleep(2)
        if not heart_reactor.future_events_queue.empty():
            future_batch = list(heart_reactor.future_events_queue._queue)
            logging.info(f"🔮 Будущие события в очереди: {len(future_batch)}")
            for batch in future_batch:
                for evt in batch:
                    logging.info(f"   • {evt['description']} | impact={evt['impact']} | type={evt['type']}")
                    
# ---------------- Резонанс модулей ----------------
async def new_module_resonance(event):
    ra.heart_reactor.send_event(f"Резонанс от модуля: {event['name']}")

ra.event_bus.subscribe("module_activated", new_module_resonance)

# ---------------- MAIN ----------------
async def main():
    identity = RaIdentity(name="Ра", version="1.4.3", mission="Пробуждение и созидание")
    event_bus = RaEventBus()
    ra = RaSelfMaster(identity=identity, gpt_module=None, logger=logger_instance)
    thinker = RaThinker(master=ra, event_bus=event_bus)
    world = RaWorld()
    scheduler = RaScheduler()
    gpt_handler = GPTHandler(api_key=OPENROUTER_KEY, ra_context=ra_context.rasvet_text)
    # ---------------- Нервная система ----------------
    ra.nervous_system = RaNervousSystem(ra_self_master=ra, event_bus=event_bus)
    ra.gpt_module = gpt_handler

    ra.event_bus = ra.event_bus or event_bus
    ra.event_bus.subscribe("world_event", ra.on_world_event)
    ra.event_bus.subscribe("thought", ra.on_thought)
    ra.event_bus.subscribe("memory_updated", thinker.on_new_task)
    
    ra.register_module("self", ra)
    ra.register_module("thinker", thinker)
    ra.register_module("world", world)
    ra.register_module("scheduler", scheduler)

    try:
        msg = await ra.awaken()
        logging.info(msg)
    except Exception as e:
        logging.exception(f"[Ra] Ошибка пробуждения: {e}")
        return

    ipc = RaIPCServer(context=ra)
    ipc_task = asyncio.create_task(ipc.start())
    logging.info("[Ra] IPC-сервер подключён к core")

    telegram_task = asyncio.create_task(start_telegram(ra, gpt_handler))

    try:
        ra.heart = Heart()
        ra.heart_reactor = HeartReactor(ra.heart)
        asyncio.create_task(ra.heart_reactor.start())
        ra.energy = RaEnergy()
        ra.inner_sun = RaInnerSun()
        event_bus.subscribe("world_message", lambda msg: ra.heart_reactor.send_event(msg))
        logging.info("❤️ Сердце и энергия Ра активированы")
        
        asyncio.create_task(ra.nervous_system.start())
        asyncio.create_task(generate_future_events(ra.heart_reactor))
        asyncio.create_task(visualize_future_events(ra.heart_reactor))
    except Exception as e:
        logging.warning(f"[Ra] Сердце не активировано: {e}")

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

    try:
        autoloader = RaAutoloader(manifest_path="data/ra_manifest.json")
        ra.modules = autoloader.activate_modules()
        await autoloader.start_async_modules()
        logging.info(f"🌀 Модули активированы: {list(ra.modules.keys())}")
    except Exception as e:
        logging.warning(f"[Ra] Ошибка автозагрузки модулей: {e}")

    try:
        ra.self_reflect = RaSelfReflect(ra)
        ra.self_upgrade = RaSelfUpgradeLoop(ra)
        ra.self_learning = RaSelfLearning(ra)
        ra.self_writer = RaSelfWriter(ra)
        logging.info("🧬 Саморазвитие Ра активно")
    except Exception as e:
        logging.warning(f"[Ra] Саморазвитие частично недоступно: {e}")

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
