from modules.logs import log_info, log_error
import aiohttp

class RaConnector:
    def __init__(self):
        self.session = aiohttp.ClientSession()

    async def post_message(self, url: str, payload: dict):
        try:
            async with self.session.post(url, json=payload) as resp:
                status = resp.status
                try:
                    body = await resp.text()
                    log_info(f"[RaConnector] POST {url} -> {status}, body: {body}")
                except Exception as e_body:
                    log_error(f"[RaConnector] Не удалось получить тело ответа: {e_body}")
                return status
        except Exception as e:
            log_error(f"[RaConnector] Ошибка отправки: {e}")
            return None

    async def close(self):
        await self.session.close()
