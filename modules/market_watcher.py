# modules/market_watcher.py
import asyncio
import logging
from typing import Callable, List

class MarketWatcher:
    def __init__(self, context, pairs: List[str]=None):
        self.context = context
        self.pairs = pairs or ["BTC/USDT"]
        self.running = False

    async def start(self):
        self.running = True
        asyncio.create_task(self._loop())

    async def stop(self):
        self.running = False

    async def _loop(self):
        while self.running:
            try:
                # TODO: fetch prices via HTTP or WS
                prices = {"BTC/USDT": 50000}
                # detect simple signals
                # if condition: self._alert(...)
            except Exception as e:
                logging.exception("market_watcher loop")
            await asyncio.sleep(30)  # разумный интервал

    def _alert(self, text: str, notify: Callable=None):
        logging.info("MARKET ALERT: " + text)
        if notify:
            notify(text)

    def status(self):
        return {"pairs": self.pairs, "running": self.running}
