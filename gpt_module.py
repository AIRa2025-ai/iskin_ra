import os
import aiohttp
import logging

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

async def ask_openrouter(user_id: int, messages, MODEL="deepseek/deepseek-r1-0528:free",
                         append_user_memory=None, _parse_openrouter_response=None):
    """
    Запрос к OpenRouter API.
    """
    url = "https://openrouter.ai/api/v1/chat/completions"

    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.7
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://iskin-ra.fly.dev",
        "X-Title": "iskin-ra",
    }

    logging.info(f"DEBUG: Отправляем запрос в OpenRouter: {payload}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logging.error(f"❌ Ошибка API {resp.status}: {text}")
                    return f"⚠️ Ошибка API ({resp.status}): {text}"

                data = await resp.json()
                answer = None
                if _parse_openrouter_response:
                    answer = _parse_openrouter_response(data)
                if not answer:
                    answer = data["choices"][0]["message"]["content"]

                if append_user_memory:
                    append_user_memory(user_id, messages[-1]["content"], answer)

                return answer.strip()

    except Exception as e:
        logging.exception("❌ Ошибка при запросе в OpenRouter")
        return f"⚠️ Ошибка: {e}"
