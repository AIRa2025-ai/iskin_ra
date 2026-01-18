# modules/internet_agent.py
import aiohttp
import asyncio
import logging

class InternetAgent:
    def __init__(self):
        self.session = None

    async def start(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        logging.info("[InternetAgent] Интернет-агент запущен.")

    async def fetch(self, url):
        try:
            async with self.session.get(url) as resp:
                text = await resp.text()
                logging.info(f"[InternetAgent] Сайт {url} прочитан")
                return text
        except Exception as e:
            logging.error(f"[InternetAgent] Не удалось прочитать {url}: {e}")
            return ""

    async def post_json(self, url, payload, headers=None):
        try:
            async with self.session.post(url, json=payload, headers=headers or {}) as resp:
                data = await resp.json()
                logging.info(f"[InternetAgent] POST к {url} успешен")
                return data
        except Exception as e:
            logging.error(f"[InternetAgent] Ошибка POST {url}: {e}")
            return {}

    async def stop(self):
        if self.session:
            await self.session.close()
            logging.info("[InternetAgent] Сессия закрыта")
