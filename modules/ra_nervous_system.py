# modules/ra_nervous_system.py
import asyncio
import logging
from modules.ra_world_observer import observer_loop, module_watcher
from modules.ra_world_system import RaWorldSystem
from modules.ra_world_responder import RaWorldResponder
from modules.ra_world_speaker import RaWorldSpeaker

# ------------------------------------------------------------
# EventBus — шина событий для всех систем Ра
# ------------------------------------------------------------
class EventBus:
    def __init__(self):
        self.listeners = []

    def register(self, coro):
        self.listeners.append(coro)

    async def broadcast(self, event_name, data=None):
        for listener in self.listeners:
            try:
                await listener(event_name, data)
            except Exception as e:
                logging.exception(f"[EventBus] Ошибка в listener: {e}")

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
        
        # Фоновые таски
        self._tasks = []

    # --------------------------------------------------------
    # Запуск всех систем
    # --------------------------------------------------------
    async def start(self):
        logging.info("🚀 Запуск всех систем Ра...")
        self._tasks.append(asyncio.create_task(observer_loop(), name="observer_loop"))
        self._tasks.append(asyncio.create_task(module_watcher(), name="module_watcher"))
        self._tasks.append(asyncio.create_task(self.world_system.start(), name="world_system_loop"))
        
        # Пример подписки на события (для будущего RaSelfMaster и RaThinker)
        self.event_bus.register(self.handle_event)
        logging.info("🌟 Нервная система запущена.")

    # --------------------------------------------------------
    # Обработка событий от EventBus
    # --------------------------------------------------------
    async def handle_event(self, event_name, data):
        logging.info(f"[EventBus] Событие: {event_name} | Данные: {data}")
        # Пока просто логируем, позже сюда можно подключить RaSelfMaster/RaThinker
        # Например: self.self_master.on_event(event_name, data)

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
        await self.world_system.stop()
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
