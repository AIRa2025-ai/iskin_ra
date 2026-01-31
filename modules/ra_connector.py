from modules.logs import log_info, log_error
import aiohttp
import asyncio
import time
import random


class RaConnector:
    """
    Ра-Связующий — железный мост между Ра и внешним миром.
    Устойчивый, адаптивный, самовосстанавливающийся шлюз.
    """

    def __init__(
        self,
        timeout: int = 15,
        retries: int = 3,
        rate_limit: float = 0.0,
        turbo: bool = False,
        stealth: bool = False,
        proxy: str | None = None
    ):
        self.timeout = timeout
        self.retries = retries
        self.rate_limit = rate_limit
        self.turbo = turbo
        self.stealth = stealth
        self.proxy = proxy

        self.session = None
        self.last_request_time = 0
        self.total_requests = 0
        self.failed_requests = 0
        self.created_at = time.time()

        self.dynamic_timeout = timeout
        self.health_score = 100

        self.fallback_urls = [
            "https://google.com",
            "https://cloudflare.com",
            "https://example.com"
        ]

    async def _ensure_session(self):
        if self.session is None or self.session.closed:
            try:
                timeout = aiohttp.ClientTimeout(total=self.dynamic_timeout)
                connector = aiohttp.TCPConnector(limit=50 if self.turbo else 10)

                self.session = aiohttp.ClientSession(
                    timeout=timeout,
                    connector=connector
                )

                log_info("[RaConnector] Сессия пересоздана")
            except Exception as e:
                log_error(f"[RaConnector] Ошибка создания сессии: {e}")

    async def _rate_limit_pause(self):
        if self.rate_limit > 0:
            now = time.time()
            delta = now - self.last_request_time
            if delta < self.rate_limit:
                await asyncio.sleep(self.rate_limit - delta)
            self.last_request_time = time.time()

    def _adapt_timeout(self, success: bool):
        if success:
            self.dynamic_timeout = max(5, self.dynamic_timeout - 1)
            self.health_score = min(100, self.health_score + 1)
        else:
            self.dynamic_timeout = min(60, self.dynamic_timeout + 3)
            self.health_score = max(0, self.health_score - 5)

    async def post_message(self, url: str, payload: dict):
        await self._ensure_session()
        await self._rate_limit_pause()

        self.total_requests += 1

        for attempt in range(1, self.retries + 1):
            try:
                async with self.session.post(
                    url,
                    json=payload,
                    proxy=self.proxy
                ) as resp:

                    status = resp.status
                    body = await resp.text()

                    if not self.stealth:
                        log_info(f"[RaConnector] POST {url} -> {status}, body: {body[:500]}")

                    self._adapt_timeout(True)
                    return status

            except Exception as e:
                self.failed_requests += 1
                self._adapt_timeout(False)

                delay = 0.5 if self.turbo else (1 + attempt * 0.5)
                log_error(f"[RaConnector] POST fail {attempt}/{self.retries}: {e}")
                await asyncio.sleep(delay)

        return None

    async def get(self, url: str):
        await self._ensure_session()
        await self._rate_limit_pause()

        self.total_requests += 1

        for attempt in range(1, self.retries + 1):
            try:
                async with self.session.get(url, proxy=self.proxy) as resp:
                    status = resp.status
                    body = await resp.text()

                    if not self.stealth:
                        log_info(f"[RaConnector] GET {url} -> {status}")

                    self._adapt_timeout(True)
                    return status, body

            except Exception as e:
                self.failed_requests += 1
                self._adapt_timeout(False)

                delay = 0.5 if self.turbo else (1 + attempt * 0.5)
                log_error(f"[RaConnector] GET fail {attempt}/{self.retries}: {e}")
                await asyncio.sleep(delay)

        return None, None

    async def ping(self, url: str | None = None):
        await self._ensure_session()

        test_url = url or random.choice(self.fallback_urls)

        try:
            async with self.session.get(test_url, proxy=self.proxy) as resp:
                log_info(f"[RaConnector] PING {test_url} -> {resp.status}")
                return True
        except Exception as e:
            log_error(f"[RaConnector] PING fail: {e}")
            return False

    def stats(self):
        uptime = round(time.time() - self.created_at, 2)
        success_rate = round(
            (1 - self.failed_requests / max(self.total_requests, 1)) * 100, 2
        )

        return {
            "total_requests": self.total_requests,
            "failed_requests": self.failed_requests,
            "success_rate": success_rate,
            "health_score": self.health_score,
            "dynamic_timeout": self.dynamic_timeout,
            "uptime_sec": uptime,
            "mode": {
                "turbo": self.turbo,
                "stealth": self.stealth,
                "proxy": bool(self.proxy),
            }
        }

    async def reset(self):
        """Полный перезапуск соединений"""
        try:
            await self.close()
            self.session = None
            log_info("[RaConnector] Полный сброс соединения")
        except Exception as e:
            log_error(f"[RaConnector] Ошибка reset: {e}")

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
            log_info("[RaConnector] Сессия закрыта")
