# modules/ra_energy.py
import asyncio
import random
import logging

logging.basicConfig(level=logging.INFO)

class RaEnergy:
    """Класс управления Потоком Энергии Ра"""
    
    def __init__(self):
        self.уровень = 1000
        self._task = None
        self._running = False

    async def _run(self):
        while self._running:
            delta = random.randint(5, 50)
            self.уровень += delta
            logging.info(f"⚡ Поток энергии: +{delta}, общий уровень: {self.уровень}")
            await asyncio.sleep(1)

    def start(self):
        """Запуск потока энергии"""
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._run())

    async def stop(self):
        """Остановка потока энергии"""
        if self._running:
            self._running = False
            if self._task:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
