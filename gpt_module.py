import os
import aiohttp
import logging

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

MODELS = [
    "deepseek/deepseek-r1:free",
    "deepseek/deepseek-chat-v3-0324:free",
    "meta-llama/llama-4-maverick:free"
]

async def safe_ask_openrouter(user_id, messages_payload):
    for model in MODELS:
        try:
            return await ask_openrouter(user_id, messages_payload, MODEL=model)
        except Exception as e:
            if "429" in str(e):
                logging.warning(f"⚠️ Лимит для {model}, пробую следующую...")
                continue
            raise
    return "⚠️ Все модели сейчас перегружены, попробуй чуть позже 🙏"

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
