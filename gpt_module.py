import os
import asyncio
import aiohttp
import logging

BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

async def ask_openrouter(user_id, user_input, MODEL, append_user_memory, _parse_openrouter_response):
    api_key = os.getenv("OPENROUTER_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}" if api_key else "",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://iskin-ra.fly.dev",
        "X-Title": "Ra Bot"
    }
    payload = {"model": MODEL, "messages": user_input, "max_tokens": 4000}
    retries = 5
    delay = 3
    timeout = aiohttp.ClientTimeout(total=60)

    for attempt in range(1, retries + 1):
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(BASE_URL, json=payload, headers=headers) as resp:
                    if resp.status == 401:
                        logging.error("❌ Unauthorized — проверь OPENROUTER_API_KEY")
                        return "⚠️ Ошибка авторизации, ключ некорректен."
                    resp.raise_for_status()
                    data = await resp.json(content_type=None)
                    reply = _parse_openrouter_response(data) if data else None
                    if not reply:
                        reply = "⚠️ Источник молчит."
                    append_user_memory(user_id, user_input, reply)
                    logging.info(f"✅ Ответ получен для пользователя {user_id}")
                    return reply
        except Exception as e:
            logging.warning(f"[{attempt}/{retries}] Ошибка: {e}")
            await asyncio.sleep(delay)
            delay *= 2
    return "⚠️ Ра устал, попробуй позже."
