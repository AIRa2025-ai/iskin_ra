import os
import asyncio
import aiohttp
import logging

# === 🔑 Настройки API ===
API_KEY = os.getenv("OPENROUTER_API_KEY")  # ключ берём из переменной окружения
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

COMMON_HEADERS = {
    "Authorization": f"Bearer {API_KEY}" if API_KEY else "",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://iskin-ra.fly.dev",  # домен на fly.io
    "X-Title": "Ra Bot"
}

# === 🌐 Парсер ответа OpenRouter ===
def parse_openrouter_response(data):
    try:
        if "output" in data and isinstance(data["output"], list):
            return data["output"][0]["content"]
        return None
    except Exception as e:
        logging.error(f"❌ Ошибка parse_openrouter_response: {e}")
        return None

# === 🌐 Запрос к OpenRouter ===
async def ask_gpt(user_id, user_input, MODEL="gpt-4", append_user_memory=lambda *a: None):
    """
    user_input: строка от пользователя
    MODEL: модель OpenRouter
    append_user_memory: функция для записи в память
    """
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": user_input}],
        "max_tokens": 4000,
    }

    retries = 5
    delay = 3
    timeout = aiohttp.ClientTimeout(total=60)

    for attempt in range(1, retries + 1):
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(BASE_URL, json=payload, headers=COMMON_HEADERS) as resp:
                    if resp.status == 429:
                        logging.warning(f"[{attempt}/{retries}] 429 Too Many Requests. Пауза {delay}s.")
                        await asyncio.sleep(delay)
                        delay *= 2
                        continue

                    if 500 <= resp.status < 600:
                        body = await resp.text()
                        logging.warning(f"[{attempt}/{retries}] Сервер OpenRouter {resp.status}: {body[:300]}")
                        await asyncio.sleep(delay)
                        delay *= 2
                        continue

                    resp.raise_for_status()
                    data = await resp.json(content_type=None)

                    reply = parse_openrouter_response(data) or "⚠️ Источник молчит."
                    append_user_memory(user_id, user_input, reply)
                    logging.info(f"✅ Ответ получен для пользователя {user_id}")
                    return reply

        except asyncio.TimeoutError:
            logging.error(f"[{attempt}/{retries}] Таймаут при соединении с OpenRouter")
        except aiohttp.ClientError as e:
            logging.warning(f"[{attempt}/{retries}] Сетевой сбой: {e}. Пауза {delay}s.")
        except Exception as e:
            logging.exception(f"[{attempt}/{retries}] Неожиданная ошибка: {e}. Пауза {delay}s.")

        await asyncio.sleep(delay)
        delay *= 2

    return "⚠️ Ра устал, слишком много вопросов подряд. Давай чуть позже, брат."
