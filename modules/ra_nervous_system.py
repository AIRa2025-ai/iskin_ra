# modules/ra_nervous_system.py

import asyncio
import logging

from modules.ra_world_system import RaWorldSystem
from modules.ra_world_responder import RaWorldResponder
from modules.ra_world_speaker import RaWorldSpeaker
from modules.ra_inner_sun import RaInnerSun
from modules.ra_thinker import RaThinker
from modules.ra_scheduler import RaScheduler
from modules.ra_energy import RaEnergy  # 🌟 Подключаем поток энергии
from modules.ra_world_observer import RaWorldObserver
from modules.ra_intent_engine import RaIntentEngine
from modules.ra_light import излучать_мудрость, делиться_теплом

# глобальный объект intent engine
intent_engine = RaIntentEngine()

class RaNervousSystem:
    """
    Модуль нервной системы Ра.
    НЕ ядро, НЕ запускной файл.
    Подключается к RaSelfMaster и EventBus как орган.
    """

    def __init__(self, ra_self_master, event_bus):
        logging.info("🧠 Инициализация модуля нервной системы Ра...")

        self.ra = ra_self_master
        self.event_bus = event_bus
        self.thinker = getattr(self.ra, "thinker", None)
        self.scheduler = getattr(self.ra, "scheduler", None)
        
        # Используем уже существующие мир и observer из Ра
        self.world_observer = getattr(self.ra, "world_observer", None)

        # Используем существующие модули Ра
        if self.thinker:
            self.thinker.set_event_bus(self.event_bus)

        if self.scheduler and self.event_bus:
            self.event_bus.subscribe("schedule", self.scheduler.on_schedule)
            
        if self.scheduler and self.thinker:
            self.scheduler.thinker = self.thinker
            
        # World system (если нет — создаём)
        self.world_system = getattr(self.ra, "world_system", None) or RaWorldSystem()
        self.world_responder = self.world_system.responder
        self.world_speaker = RaWorldSpeaker()

        # Энергетика
        self.energy = RaEnergy()
        self.inner_sun = RaInnerSun()
        self.heart_reactor = getattr(self.ra, "heart_reactor", None)
        self._tasks = []

        # Подписка на события
        if hasattr(self.event_bus, "subscribe"):
            self.event_bus.subscribe("harmony_updated", self.on_harmony_signal)
            self.event_bus.subscribe("observer_tick", self._on_observer_tick)
            self.event_bus.subscribe("world_message", self._on_world_message)
       
    # -----------------------------
    # Обработка событий
    # -----------------------------
    async def _on_observer_tick(self, data):
        logging.info(f"[NervousModule] Observer tick: {data}")

    async def _on_world_message(self, data):
        logging.info(f"[NervousModule] Сообщение мира: {data}")
        if self.ra:
            await self.ra.process_world_message(data)
        if self.thinker:
            await self.thinker.process_world_message(data)
        if self.scheduler:
            await self.scheduler.process_world_message(data)
        # --- фиксируем intent ---
        if intent_engine:
            intent_engine.propose({
                "type": "world_message",
                "message": data,
                "timestamp": datetime.datetime.utcnow().isoformat()
            })
            
    async def on_harmony_signal(self, data):
        harmony = data["гармония"]

        if harmony < -60:
            self.cooldown_seconds = 120
        elif harmony > 60:
            self.cooldown_seconds = 10
        else:
            self.cooldown_seconds = 30
            self.event_bus.emit("nervous_rhythm_updated", {
                "cooldown": self.cooldown_seconds
            })
        # --- фиксируем intent гармонии ---
        if intent_engine:
            intent_engine.propose({
                "type": "world_harmony",
                "harmony": harmony,
                "cooldown": self.cooldown_seconds,
                "timestamp": datetime.datetime.utcnow().isoformat()
            })

    async def _лучистая_активация(self):
        while True:
            await излучать_мудрость()
            await делиться_теплом()
            await asyncio.sleep(5)  # пауза между излучениями
            
    # -----------------------------
    # Запуск модуля
    # -----------------------------
    async def start(self):
        logging.info("🧬 Запуск модуля нервной системы Ра...")

        if self.world_observer:
            self._tasks.append(asyncio.create_task(self.world_observer.observer_loop(), name="observer_loop"))
            self._tasks.append(asyncio.create_task(self.world_observer.module_watcher(), name="module_watcher"))

        self._tasks.append(asyncio.create_task(self.world_system.start(), name="world_system_loop"))
        self._tasks.append(asyncio.create_task(self.energy.start(), name="energy_loop"))
        self._tasks.append(asyncio.create_task(self.inner_sun.start(), name="inner_sun_loop"))
        self._tasks.append(asyncio.create_task(self._лучистая_активация(), name="light_task"))
        
    # HeartReactor
        if self.heart_reactor:
            self._tasks.append(
                asyncio.create_task(self.heart_reactor.listen_and_respond(), name="heart_reactor_loop")
            )

        # Внутри start() после запуска потоков энергии
        self.energy.on_energy_update = lambda level: intent_engine.propose({
            "type": "energy_level",
            "level": level,
            "timestamp": datetime.datetime.utcnow().isoformat()
        })

        self.inner_sun.on_radiance_update = lambda level: intent_engine.propose({
            "type": "inner_sun_radiance",
            "level": level,
            "timestamp": datetime.datetime.utcnow().isoformat()
        })

        logging.info("🧠 Модуль нервной системы активен.")
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

        # Остановка потока энергии
        await self.energy.stop()

        logging.info("✅ Модуль нервной системы остановлен.")
