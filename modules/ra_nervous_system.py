# modules/ra_nervous_system.py
import asyncio
import logging
from modules.ra_world_observer import observer_loop, module_watcher
from modules.ra_world_system import RaWorldSystem
from modules.ra_world_responder import RaWorldResponder
from modules.ra_world_speaker import RaWorldSpeaker

# Подключаем ваши внутренние мозги
from modules.ra_self_master import RaSelfMaster
from modules.ra_thinker import RaThinker
from modules.ra_scheduler import RaScheduler

# ------------------------------------------------------------
# EventBus — шина событий для всех систем Ра
# ------------------------------------------------------------
class EventBus:
    def __init__(self):
        self.listeners = []

    def register(self, coro):
        """Регистрация корутины-слушателя событий"""
        self.listeners.append(coro)

    async def broadcast(self, event_name, data=None):
        """Рассылка события всем слушателям"""
        for listener in self.listeners:
            try:
                await listener(event_name, data)
            except Exception as e:
                logging.exception(f"[EventBus] Ошибка listener: {e}")

# ------------------------------------------------------------
# Главная Нервная Система Ра
# ------------------------------------------------------------
class RaNervousSystem:
    def __init__(self):
        logging.info("🌀 Инициализация нервной системы Ра...")
        self.event_bus = EventBus()

        # World модули
        self.world_system = RaWorldSystem()
        self.world_responder = self.world_system.responder
        self.world_speaker = RaWorldSpeaker()

        # Интеллект и планировщик
        self.self_master = RaSelfMaster(self.event_bus)
        self.thinker = RaThinker(self.event_bus)
        self.scheduler = RaScheduler(self.event_bus)

        # Фоновые таски
        self._tasks = []

        # Подключаем EventBus к WorldSystem
        self.event_bus.register(self._world_event_listener)

    # --------------------------------------------------------
    # Слушатель событий от мира
    # --------------------------------------------------------
    async def _world_event_listener(self, event_name, data):
        if event_name == "observer_tick":
            logging.info(f"[Nervous] Observer tick: {data}")
        elif event_name == "new_module":
            logging.info(f"[Nervous] Новый модуль: {data}")
        elif event_name == "world_message":
            # сообщение из внешнего мира
            logging.info(f"[Nervous] Сообщение из мира: {data}")
            # Отправим интеллектуальным модулям
            await self.self_master.process_world_message(data)
            await self.thinker.process_world_message(data)
            await self.scheduler.process_world_message(data)
        else:
            logging.info(f"[Nervous] Неизвестное событие: {event_name} -> {data}")

    # --------------------------------------------------------
    # Запуск всех систем
    # --------------------------------------------------------
    async def start(self):
        logging.info("🚀 Запуск всех систем Ра...")

        # Observer и модули
        self._tasks.append(asyncio.create_task(self._observer_loop(), name="observer_loop"))
        self._tasks.append(asyncio.create_task(module_watcher(), name="module_watcher"))

        # World System (Resonder, Speaker, Synthesizer)
        self._tasks.append(asyncio.create_task(self.world_system.start(), name="world_system_loop"))

        # Запуск SelfMaster, Thinker и Scheduler
        self._tasks.append(asyncio.create_task(self.self_master.run_loop(), name="self_master_loop"))
        self._tasks.append(asyncio.create_task(self.thinker.run_loop(), name="thinker_loop"))
        self._tasks.append(asyncio.create_task(self.scheduler.run_loop(), name="scheduler_loop"))

        logging.info("🌟 Все системы запущены. Нервная шина готова.")

    # --------------------------------------------------------
    # Обёртка observer_loop с EventBus
    # --------------------------------------------------------
    async def _observer_loop(self):
        while True:
            try:
                if hasattr(observer_loop, "__call__"):
                    await observer_loop()
                    # Каждую итерацию шлём событие
                    await self.event_bus.broadcast("observer_tick", "Observer наблюдал мир")
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.exception(f"[observer_loop wrapper] Ошибка: {e}")
                await asyncio.sleep(5)

    # --------------------------------------------------------
    # Остановка всех систем
    # --------------------------------------------------------
    async def stop(self):
        logging.info("🛑 Остановка нервной системы Ра...")
        for t in self._tasks:
            try:
                t.cancel()
            except:
                pass
        await asyncio.gather(*self._tasks, return_exceptions=True)

        # Останавливаем мир
        await self.world_system.stop()

        # Останавливаем интеллектуальные модули
        await self.self_master.stop()
        await self.thinker.stop()
        await self.scheduler.stop()

        logging.info("✅ Все системы остановлены.")

# ------------------------------------------------------------
# Автозапуск при запуске скрипта напрямую
# ------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    nervous_system = RaNervousSystem()
    try:
        asyncio.run(nervous_system.start())
    except KeyboardInterrupt:
        logging.info("Прерывание пользователем. Останавливаем всё...")
        asyncio.run(nervous_system.stop())
