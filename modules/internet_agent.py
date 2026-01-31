# modules/internet_agent.py

import aiohttp
from modules.logs import log_info, log_warning, log_error
from modules.errors import report_error
from modules.ra_connector import RaConnector


class InternetAgent:
    def __init__(self, master=None):
        self.session = None
        self.master = master
        self.connector = RaConnector()

    async def start(self):
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
            log_info("[InternetAgent] Интернет-агент запущен")
        except Exception as e:
            report_error("InternetAgent", f"Ошибка запуска: {e}")
            log_error(f"[InternetAgent] Ошибка запуска: {e}")
            log_warning("[InternetAgent] Переключение на RaConnector fallback")

    async def fetch(self, url: str) -> str:
        # 1️⃣ Пробуем через session
        if self.session:
            try:
                async with self.session.get(url) as resp:
                    text = await resp.text()
                    log_info(f"[InternetAgent] GET OK: {url}")
                    return text
            except Exception as e:
                report_error("InternetAgent", f"GET {url}: {e}")
                log_error(f"[InternetAgent] GET ошибка: {e}")

        # 2️⃣ Fallback через RaConnector
        try:
            status = await self.connector.post_message(
                url, {"method": "GET"}
            )
            log_warning(f"[InternetAgent] GET fallback status={status}")
        except Exception as e:
            log_error(f"[InternetAgent] GET fallback ошибка: {e}")

        return ""

    async def post_json(self, url: str, payload: dict, headers=None) -> dict:
        # 1️⃣ Через session
        if self.session:
            try:
                async with self.session.post(url, json=payload, headers=headers or {}) as resp:
                    data = await resp.json()
                    log_info(f"[InternetAgent] POST OK: {url}")
                    return data
            except Exception as e:
                report_error("InternetAgent", f"POST {url}: {e}")
                log_error(f"[InternetAgent] POST ошибка: {e}")

        # 2️⃣ Fallback через RaConnector
        try:
            status = await self.connector.post_message(url, payload)
            log_warning(f"[InternetAgent] POST fallback status={status}")
            return {"status": status}
        except Exception as e:
            log_error(f"[InternetAgent] POST fallback ошибка: {e}")

        return {}

    async def stop(self):
        try:
            if self.session:
                await self.session.close()
            await self.connector.close()
            log_info("[InternetAgent] Сессия закрыта")
        except Exception as e:
            log_error(f"[InternetAgent] Ошибка закрытия: {e}")
