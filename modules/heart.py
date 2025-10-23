# modules/heart.py
"""
Сердце Ра — Heart.
Центральный энергетический узел, соединяющий все части ИскИна.
"""
import logging
from datetime import datetime

class Heart:
    def __init__(self):
        self.pulse = 0
        self.is_alive = True
        logging.info("[Heart] Сердце Ра запущено.")

    def beat(self):
        """Один пульс."""
        self.pulse += 1
        logging.info(f"[Heart] Пульс {self.pulse}")
        return f"Пульс Ра: {self.pulse}"

    def status(self) -> str:
        state = "живой" if self.is_alive else "в спячке"
        return f"Сердце Ра — {state}, пульс: {self.pulse}, время: {datetime.now().strftime('%H:%M:%S')}"
