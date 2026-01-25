# core/openrouter_client.py
import aiohttp
import asyncio
import logging

log = logging.getLogger("OpenRouterClient")

class OpenRouterClient:
    """
    Простой клиент для общения с OpenRouter.
    Используется вместе с GPTHandler.
    """

    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def ask(self, model: str, messages: list[dict]):
        """
        Асинхронный запрос к модели OpenRouter.
        messages — список словарей с role/content.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-Title": "iskin-ra"
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.6
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.BASE_URL, json=payload, headers=headers) as resp:
                    data = await resp.json()
                    if "choices" not in data or not data["choices"]:
                        raise ValueError("Нет ответа от модели OpenRouter")
                    answer = data["choices"][0]["message"]["content"].strip()
                    return answer
            except Exception as e:
                log.warning(f"[OpenRouterClient] Ошибка запроса модели {model}: {e}")
                raise
