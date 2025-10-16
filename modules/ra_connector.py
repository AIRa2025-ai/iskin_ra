import aiohttp
import logging

class RaConnector:
    """
    Ра-Связующий — соединяет Ра с внешними источниками (API, RSS, чаты).
    """

    async def post_message(self, url: str, payload: dict):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    status = resp.status
                    logging.info(f"[RaConnector] POST {url} -> {status}")
                    return status
        except Exception as e:
            logging.error(f"[RaConnector] Ошибка отправки: {e}")
            return None
