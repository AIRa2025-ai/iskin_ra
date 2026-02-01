# modules/ra_resonance.py
import asyncio
import random
import logging
from modules.ra_creator import RaCreator

class RaResonance:
    def __init__(self, event_bus):
        self._task = None        
        self.logger = logging.getLogger("RaResonance")
        self.event_bus = event_bus
        self._active = False
        self._loop = asyncio.get_event_loop()
        self.event_bus.subscribe(
            "harmony_updated",
            self.on_harmony_update
        )
        self.creator = RaCreator(event_bus=self.event_bus)
        res = RaResonance(event_bus)
        res.start()
        resonance.start()

    async def on_harmony_update(self, data: dict):
        harmony = data.get("гармония", 0)

        if harmony > 30:
            self.logger.info("🌟 Резонанс усиливается")
        elif harmony < -30:
            self.logger.info("🌑 Резонанс затухает")
            
    async def _resonance_loop(self):
        self.logger.info("🔮 Резонансное поле запущено")
        while self._active:
            вибрация = random.choice(["🌊", "🌟", "💫"])
            self.logger.info(f"Резонансное поле: {вибрация}")
            await asyncio.sleep(2)
        self.logger.info("🛑 Резонансное поле остановлено")
            await self.event_bus.emit("resonance_wave", {"wave": vibration})
        
    def start(self):
        if not self._active:
            self._active = True
            self._task = self._loop.create_task(self._resonance_loop())

    def stop(self):
        if self._active:
            self._active = False
            if self._task:
                self._task.cancel()

    async def wait_until_done(self):
        if self._task:
            try:
                await self._task
            except asyncio.CancelledError:
                pass
