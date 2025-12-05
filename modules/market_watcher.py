# modules/market_watcher.py
import asyncio
import logging
from typing import Callable, List

class MarketWatcher:
    """
    Мониторинг крипто и валютных пар.
    Сигналы можно отдавать через notify callback (например, Telegram).
    """
    def __init__(self, context=None, pairs: List[str]=None, notify: Callable=None):
        self.context = context
        self.pairs = pairs or ["BTC/USDT", "ETH/USDT"]
        self.notify = notify
        self.running = False

    async def start(self):
        self.running = True
        asyncio.create_task(self._loop())

    async def stop(self):
        self.running = False

    async def _loop(self):
        while self.running:
            try:
                # Заглушка: в реале тут API или websocket
                prices = {p: 50000.0 for p in self.pairs}  # пример данных
                logging.info(f"[MarketWatcher] Prices: {prices}")
                # TODO: условия сигналов
                # if prices['BTC/USDT'] > 60000:
                #     self._alert("BTC выше 60k")
            except Exception as _e:  # F841 исправлено
                logging.exception(f"MarketWatcher loop error: {_e}")
            await asyncio.sleep(30)  # опрашивать каждые 30 сек

    def _alert(self, text: str):
        logging.info(f"[MarketWatcher ALERT] {text}")
        if self.notify:
            self.notify(text)

    def status(self):
        return {"running": self.running, "pairs": self.pairs}
