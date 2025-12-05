# modules/ra_energy.py
import asyncio
import random

class ПотокЭнергии:
    def __init__(self):
        self.уровень = 1000

    async def распределять(self):
        while True:
            delta = random.randint(5, 50)
            self.уровень += delta
            print(f"⚡ Поток энергии: +{delta}, общий уровень: {self.уровень}")
            await asyncio.sleep(1)
