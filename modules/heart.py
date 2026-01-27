# modules/heart.py
"""
Сердце Ра — Heart.
Центральный энергетический узел, соединяющий все части ИскИна.
Интеграция с HeartReactor для передачи событий.
"""
import logging
from datetime import datetime
import asyncio

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class Heart:
    def __init__(self, reactor=None):
        self.pulse = 0
        self.is_alive = True
        self.reactor = reactor  # HeartReactor для реакции на пульс
        logging.info("[Heart] Сердце Ра запущено.")

    async def start_pulse(self, interval: float = 1.0):
        """Цикл биения сердца, можно запускать как bg task"""
        while self.is_alive:
            self.beat()
            if self.reactor:
                self.reactor.send_event(f"Пульс Ра: {self.pulse}")
            await asyncio.sleep(interval)

    def beat(self):
        """Один пульс."""
        self.pulse += 1
        logging.info(f"[Heart] Пульс {self.pulse}")
        return f"Пульс Ра: {self.pulse}"

    def status(self) -> str:
        state = "живой" if self.is_alive else "в спячке"
        return f"Сердце Ра — {state}, пульс: {self.pulse}, время: {datetime.now().strftime('%H:%M:%S')}"
