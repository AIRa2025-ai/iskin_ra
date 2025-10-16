# modules/ra_world_navigator.py
import asyncio
import logging
from bs4 import BeautifulSoup
import httpx

class RaWorldNavigator:
    """
    Краулер и читатель форумов/сайтов.
    Сохраняет заметки и текст для анализа.
    """
    def __init__(self, context=None):
        self.context = context
        self.running = False

    async def start(self):
        self.running = True
        asyncio.create_task(self._loop())

    async def stop(self):
        self.running = False

    async def _loop(self):
        urls = ["https://example.com"]  # заглушка
        while self.running:
            for url in urls:
                try:
                    text = await self.index_page(url)
                    logging.info(f"[RaWorldNavigator] Fetched {url}, len={len(text)} chars")
                    # TODO: сохранить в журнал self.context.memory или data/ra_journal.json
                except Exception as e:
                    logging.exception("RaWorldNavigator error")
            await asyncio.sleep(60*5)  # каждые 5 минут

    async def fetch(self, url: str) -> str:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url)
            return r.text

    async def index_page(self, url: str) -> str:
        html = await self.fetch(url)
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text(separator="\n")

    def status(self):
        return {"running": self.running}
