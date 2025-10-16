# modules/ra_world_navigator.py
import asyncio, logging
from bs4 import BeautifulSoup
import httpx

class RaNavigator:
    def __init__(self, context):
        self.context = context

    async def fetch(self, url: str) -> str:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url)
            return r.text

    async def index_page(self, url: str):
        html = await self.fetch(url)
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator="\n")
        # save to journal
        # context.memory.append(...)
        return text

    async def start(self):
        # periodic crawl jobs
        pass
