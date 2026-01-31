from modules.logs import log_info, log_error
import aiohttp
import asyncio


class RaConnector:
    """
    Ра-Связующий — единый мост между Ра и внешним миром.
    Отвечает за отправку, получение, проверку соединений и устойчивость связи.
    """

    def __init__(self, timeout: int = 15, retries: int = 3):
        self.timeout = timeout
        self.retries = retries
        self.session = None

    async def _ensure_session(self):
        """Гарантирует, что сессия существует"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
            log_info("[RaConnector] Создана новая сессия соединения")

    async def post_message(self, url: str, payload: dict):
        """Отправка POST-запроса с защитой и повторами"""
        await self._ensure_session()

        for attempt in range(1, self.retries + 1):
            try:
                async with self.session.post(url, json=payload) as resp:
                    status = resp.status
                    try:
                        body = await resp.text()
                        log_info(f"[RaConnector] POST {url} -> {status}, body: {body}")
                    except Exception as e_body:
                        log_error(f"[RaConnector] Ошибка чтения тела ответа: {e_body}")

                    return status

            except Exception as e:
                log_error(f"[RaConnector] POST попытка {attempt}/{self.retries} провалилась: {e}")
                await asyncio.sleep(1)

        return None

    async def get(self, url: str):
        """Получение данных (GET)"""
        await self._ensure_session()

        for attempt in range(1, self.retries + 1):
            try:
                async with self.session.get(url) as resp:
                    status = resp.status
                    body = await resp.text()
                    log_info(f"[RaConnector] GET {url} -> {status}")
                    return status, body

            except Exception as e:
                log_error(f"[RaConnector] GET попытка {attempt}/{self.retries} провалилась: {e}")
                await asyncio.sleep(1)

        return None, None

    async def ping(self, url: str):
        """Проверка доступности внешнего мира"""
        await self._ensure_session()

        try:
            async with self.session.get(url) as resp:
                log_info(f"[RaConnector] PING {url} -> {resp.status}")
                return True
        except Exception as e:
            log_error(f"[RaConnector] PING ошибка: {e}")
            return False

    async def close(self):
        """Корректное закрытие соединений"""
        if self.session and not self.session.closed:
            await self.session.close()
            log_info("[RaConnector] Сессия закрыта")
