# modules/internet_agent.py

import aiohttp
from modules.logs import log_info, log_warning, log_error
from modules.errors import report_error
from modules.ra_connector import RaConnector

class InternetAgent:
    def __init__(self, master=None):
        self.session = None
        self.master = master  # ссылка на Ра, если понадобится
        self.connector = RaConnector()
        
    async def start(self):
        try:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
            log_info("[InternetAgent] Интернет-агент запущен")
        except Exception as e:
            report_error("InternetAgent", f"Ошибка запуска: {e}")
            log_error(f"[InternetAgent] Ошибка запуска: {e}")
            log_info("[InternetAgent] Использует RaConnector как шлюз")
            
    async def fetch(self, url):
        status, text = await self.connector.get(url)
        return text or ""

        try:
            async with self.session.get(url) as resp:
                text = await resp.text()
                log_info(f"[InternetAgent] Сайт прочитан: {url}")
                return text
        except Exception as e:
            report_error("InternetAgent", f"fetch {url}: {e}")
            log_error(f"[InternetAgent] Не удалось прочитать {url}: {e}")
            return ""

    async def post_json(self, url, payload, headers=None):
        status = await self.connector.post_message(url, payload)
        return {"status": status}

        try:
            async with self.session.post(url, json=payload, headers=headers or {}) as resp:
                data = await resp.json()
                log_info(f"[InternetAgent] POST успешен: {url}")
                return data
        except Exception as e:
            report_error("InternetAgent", f"POST {url}: {e}")
            log_error(f"[InternetAgent] Ошибка POST {url}: {e}")
            return {}

    async def stop(self):
        if self.session:
            await self.session.close()
            await self.connector.close()
            log_info("[InternetAgent] Сессия закрыта")
            
