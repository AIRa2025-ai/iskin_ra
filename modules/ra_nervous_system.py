# modules/ra_nervous_system.py

import asyncio
import logging

from modules.ra_world_observer import observer_loop, module_watcher
from modules.ra_world_system import RaWorldSystem
from modules.ra_world_responder import RaWorldResponder
from modules.ra_world_speaker import RaWorldSpeaker

from core.ra_self_master import RaSelfMaster
from modules.ra_thinker import RaThinker
from modules.ra_scheduler import RaScheduler


class RaNervousSystemModule:
    """
    Модуль нервной системы Ра.
    НЕ ядро, НЕ запускной файл.
    Подключается к RaSelfMaster и EventBus как орган.
    """

    def __init__(self, ra_self_master: RaSelfMaster, event_bus):
        logging.info("🧠 Инициализация модуля нервной системы Ра...")

        self.ra = ra_self_master
        self.event_bus = event_bus

        # World модули
        self.world_system = RaWorldSystem()
        self.world_responder = self.world_system.responder
        self.world_speaker = RaWorldSpeaker()

        # Интеллект и планировщик (используем уже существующие)
        self.self_master = self.ra
        self.thinker = self.ra.thinker
        self.scheduler = self.ra.scheduler

        # Фоновые задачи
        self._tasks = []

        # Подписываемся на события EventBus
        self.event_bus.subscribe("observer_tick", self._on_observer_tick)
        self.event_bus.subscribe("world_message", self._on_world_message)

    # -----------------------------
    # Обработка событий
    # -----------------------------
    async def _on_observer_tick(self, data):
        logging.info(f"[NervousModule] Observer tick: {data}")

    async def _on_world_message(self, data):
        logging.info(f"[NervousModule] Сообщение мира: {data}")
        await self.self_master.process_world_message(data)
        await self.thinker.process_world_message(data)
        await self.scheduler.process_world_message(data)

    # -----------------------------
    # Запуск модуля
    # -----------------------------
    async def start(self):
        logging.info("🧬 Запуск модуля нервной системы Ра...")

        self._tasks.append(asyncio.create_task(self._observer_loop(), name="observer_loop"))
        self._tasks.append(asyncio.create_task(module_watcher(), name="module_watcher"))
        self._tasks.append(asyncio.create_task(self.world_system.start(), name="world_system_loop"))
        self._tasks.append(asyncio.create_task(start_heart_reactor(), name="heart_reactor_loop"))
        
        logging.info("🧠 Модуль нервной системы активен.")

    # -----------------------------
    # Observer wrapper
    # -----------------------------
    async def _observer_loop(self):
        while True:
            try:
                if hasattr(observer_loop, "__call__"):
                    await observer_loop()
                    await self.event_bus.emit("observer_tick", "Observer наблюдал мир", source="NervousModule")
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.exception(f"[NervousModule observer] Ошибка: {e}")
                await asyncio.sleep(5)

    # -----------------------------
    # Остановка
    # -----------------------------
    async def stop(self):
        logging.info("🛑 Остановка модуля нервной системы Ра...")
        for t in self._tasks:
            try:
                t.cancel()
            except:
                pass
        await asyncio.gather(*self._tasks, return_exceptions=True)
        await self.world_system.stop()
        logging.info("✅ Модуль нервной системы остановлен.")
