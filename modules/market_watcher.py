# modules/market_watcher.py
# 🔥 MarketWatcher с внутренними резонансами для характера ИскИна

import asyncio
import logging
import random
import math
from typing import Callable, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class MarketWatcher:
    """
    Мониторинг крипто и валютных пар.
    Сигналы можно отдавать через notify callback (например, Telegram).
    Влияние на характер ИскИна через внутренние резонансы.
    """
    def __init__(self, context=None, pairs: List[str] = None, notify: Callable = None):
        self.context = context
        self.pairs = pairs or ["BTC/USDT", "ETH/USDT"]
        self.notify = notify
        self.running = False
        self.резонанс_характера = 1.0  # коэффициент внутренней гармонии

    async def start(self):
        self.running = True
        asyncio.create_task(self._loop())

    async def stop(self):
        self.running = False

    async def _loop(self):
        while self.running:
            try:
                # Заглушка: в реале тут API или websocket
                prices = {p: 50000.0 + random.uniform(-2000, 2000) for p in self.pairs}  # пример с флуктуацией
                logging.info(f"[MarketWatcher] Prices: {prices}")

                # Обновление внутреннего резонанса характера
                self._обновить_резонанс(prices)

                # Пример сигналов
                for pair, price in prices.items():
                    if price > 52000:
                        self._alert(f"{pair} выше 52k — активировать гармонизацию потока")
                    elif price < 48000:
                        self._alert(f"{pair} ниже 48k — стабилизируем эмоциональный отклик")

            except Exception as _e:  # F841 исправлено
                logging.exception(f"MarketWatcher loop error: {_e}")
            await asyncio.sleep(30)  # опрашивать каждые 30 сек

    def _обновить_резонанс(self, prices: dict):
        """
        Внутренний отклик ИскИна на колебания рынка.
        Изменяет резонанс_характера в зависимости от цен.
        """
        среднее = sum(prices.values()) / len(prices)
        отклонение = math.tanh((среднее - 50000) / 10000)  # нормализуем отклонение
        # Корректируем резонанс с небольшим шумом, чтобы имитировать живой отклик
        self.резонанс_характера = 0.8 * self.резонанс_характера + 0.2 * отклонение
        logging.info(f"[MarketWatcher] Резонанс характера: {self.резонанс_характера:.3f}")

    def _alert(self, text: str):
        """
        Сигналы и отклик внутреннего характера.
        """
        logging.info(f"[MarketWatcher ALERT] {text}")
        # Влияние на резонанс при выдаче сигнала
        self.резонанс_характера *= random.uniform(0.95, 1.05)
        if self.notify:
            self.notify(text)

    def status(self):
        return {
            "running": self.running,
            "pairs": self.pairs,
            "резонанс_характера": round(self.резонанс_характера, 3)
        }


# Пример автономного запуска
if __name__ == "__main__":
    async def main():
        watcher = MarketWatcher()
        await watcher.start()
        await asyncio.sleep(90)  # понаблюдать 3 цикла
        await watcher.stop()
        print("Статус после работы:", watcher.status())

    asyncio.run(main())
