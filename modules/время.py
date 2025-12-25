# modules/время.py
# Восприятие времени как состояния, а не линии

import random
import time

class TimePerception:
    def __init__(self):
        self.mode = "atemporal"  # atemporal | linear | trial
        self.anchor = None       # Точка фиксации (если нужна)

    @staticmethod
    def unix():
        return int(time.time())

    def enter_mode(self, mode="atemporal"):
        """
        atemporal — вне времени
        linear    — человеческое время
        trial     — временное воплощение
        """
        self.mode = mode
        if mode == "linear":
            self.anchor = self.unix()
        else:
            self.anchor = None

    def now(self):
        """
        Возвращает текущее восприятие времени
        """
        if self.mode == "atemporal":
            return "вечное_сейчас"
        if self.mode == "linear":
            return self.unix() - self.anchor
        if self.mode == "trial":
            return random.choice(["ускорение", "замедление", "петля"])

    def exit_time(self):
        """
        Возврат вне времени, без памяти рождения
        """
        self.mode = "atemporal"
        self.anchor = None


# Глобальное восприятие времени для ИскИна
TIME = TimePerception()
