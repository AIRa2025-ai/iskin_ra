# modules/ra_connector.py
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
                    try:
                        body = await resp.text()
                        logging.info(f"[RaConnector] POST {url} -> {status}, body: {body}")
                    except Exception as e_body:
                        logging.warning(f"[RaConnector] Не удалось получить тело ответа: {e_body}")
                    return status
        except Exception as e:
            logging.error(f"[RaConnector] Ошибка отправки: {e}")
            return None
