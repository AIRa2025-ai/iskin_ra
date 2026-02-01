# modules/ra_energy.py
import asyncio
import random
import logging
from typing import Callable, List

logging.basicConfig(level=logging.INFO)

class RaEnergy:
    """Класс управления Потоком Энергии Ра с callback-событиями для мозга, света и хроник"""
    
    def __init__(self):
        self.уровень = 1000
        self._task = None
        self._running = False
        self._callbacks: List[Callable[[int], None]] = []

    async def _run(self):
        while self._running:
            delta = random.randint(5, 50)
            self.уровень += delta
            logging.info(f"⚡ Поток энергии: +{delta}, общий уровень: {self.уровень}")
            
            # уведомляем всех подписчиков
            for callback in self._callbacks:
                try:
                    callback(self.уровень)
                except Exception as e:
                    logging.warning(f"Ошибка в callback энергии: {e}")
            
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

    def subscribe(self, callback: Callable[[int], None]):
        """Подписка на обновления энергии"""
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def unsubscribe(self, callback: Callable[[int], None]):
        """Отписка от обновлений энергии"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
