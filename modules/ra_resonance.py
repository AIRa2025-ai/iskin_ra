# modules/ra_resonance.py
import asyncio
import random
import logging

class RaResonance:
    def __init__(self):
        self._task = None
        self._active = False
        self._loop = asyncio.get_event_loop()
        self.logger = logging.getLogger("RaResonance")

    async def _resonance_loop(self):
        self.logger.info("🔮 Резонансное поле запущено")
        while self._active:
            вибрация = random.choice(["🌊", "🌟", "💫"])
            self.logger.info(f"Резонансное поле: {вибрация}")
            await asyncio.sleep(2)
        self.logger.info("🛑 Резонансное поле остановлено")

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
