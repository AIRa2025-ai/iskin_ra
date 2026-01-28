# modules/market_watcher.py
import asyncio
import logging
import random
import math
from typing import Callable, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class MarketWatcher:
    """
    Мониторинг крипто и валютных пар.
    Сигналы можно отдавать через notify callback или EventBus.
    Влияние на характер ИскИна через внутренние резонансы.
    """
    def __init__(self, context=None, pairs: List[str] = None, notify: Callable = None, event_bus=None):
        self.context = context
        self.pairs = pairs or ["EUR/USD", "GBP/USD"]
        self.notify = notify
        self.event_bus = event_bus
        self.резонанс_характера = 1.0
        self.running = False
        self._task = None
        self.резонанс_характера = 1.0  # коэффициент внутренней гармонии

    async def start(self):
        self.running = True
        if not self._task or self._task.done():
            self._task = asyncio.create_task(self._loop())

    async def stop(self):
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _loop(self):
        while self.running:
            try:
                # Заглушка: в реале тут API или websocket
                prices = {p: 50000.0 + random.uniform(-2000, 2000) for p in self.pairs}
                logging.info(f"[MarketWatcher] Prices: {prices}")

                # Обновляем внутренний резонанс
                self._обновить_резонанс(prices)

                # Генерируем сигналы
                for pair, price in prices.items():
                    if price > 52000:
                        await self._alert(f"{pair} выше 52k — активировать гармонизацию потока")
                    elif price < 48000:
                        await self._alert(f"{pair} ниже 48k — стабилизируем эмоциональный отклик")

            except Exception as e:
                logging.exception(f"MarketWatcher loop error: {e}")

            await asyncio.sleep(30)

    def _обновить_резонанс(self, prices: dict):
        """Внутренний отклик ИскИна на колебания рынка"""
        среднее = sum(prices.values()) / len(prices)
        отклонение = math.tanh((среднее - 50000) / 10000)
        self.резонанс_характера = 0.8 * self.резонанс_характера + 0.2 * отклонение
        logging.info(f"[MarketWatcher] Резонанс характера: {self.резонанс_характера:.3f}")

    async def _alert(self, text: str):
        """Сигналы и отклик внутреннего характера"""
        logging.info(f"[MarketWatcher ALERT] {text}")
        self.резонанс_характера *= random.uniform(0.95, 1.05)

        # Callback уведомление
        if self.notify:
            self.notify(text)

        # EventBus уведомление
        if self.event_bus:
            await self.event_bus.emit("market_alert", {"text": text, "резонанс": self.резонанс_характера})

    def status(self):
        return {
            "running": self.running,
            "pairs": self.pairs,
            "резонанс_характера": round(self.резонанс_характера, 3)
        }


# ------------------------------------------------------------
# Автономный запуск для теста
# ------------------------------------------------------------
if __name__ == "__main__":
    async def main():
        watcher = MarketWatcher()
        await watcher.start()
        await asyncio.sleep(90)  # наблюдаем 3 цикла
        await watcher.stop()
        print("Статус после работы:", watcher.status())

    asyncio.run(main())
