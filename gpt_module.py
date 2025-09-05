import os
import aiohttp
import logging

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Список моделей для перебора при 429
MODELS = [
    "deepseek/deepseek-r1-0528:free",
    "dolphin/dolphin-3.0-mistral-24b:free",
    "meta-llama/llama-3.2-11b-vision-instruct:free",
    "qwen/qwen-3-14B:free",
    "mistral/mistral-small-3.2-24b:free",
    "mistral/mistral-nemo:free",
    "google/gemini-2.0-flash-experimental:free"
]

async def ask_openrouter(user_id, messages, model="deepseek/deepseek-r1-0528:free",
                         append_user_memory=None, _parse_openrouter_response=None):
    """
    Делает запрос к OpenRouter API. Можно передать функции:
    - append_user_memory(user_id, user_input, reply)
    - _parse_openrouter_response(data)
    """
    url = "https://openrouter.ai/api/v1/chat/completions"

    payload = {
        "model": model,
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

                # Разбор ответа через переданную функцию
                answer = None
                if _parse_openrouter_response:
                    answer = _parse_openrouter_response(data)

                # Если функция не вернула ответ — берём стандартно
                if not answer:
                    answer = data.get("choices", [{}])[0].get("message", {}).get("content", "⚠️ Пустой ответ")

                # Сохраняем память, если передана функция
                if append_user_memory:
                    append_user_memory(user_id, messages[-1]["content"], answer)

                return answer.strip()

    except Exception as e:
        logging.exception("❌ Ошибка при запросе в OpenRouter")
        return f"⚠️ Ошибка: {e}"


async def safe_ask_openrouter(user_id, messages_payload,
                              append_user_memory=None, _parse_openrouter_response=None):
    """
    Перебирает модели, если возник лимит 429, и возвращает первый успешный ответ
    """
    for model in MODELS:
        try:
            return await ask_openrouter(
                user_id, messages_payload, model=model,
                append_user_memory=append_user_memory,
                _parse_openrouter_response=_parse_openrouter_response
            )
        except Exception as e:
            if "429" in str(e):
                logging.warning(f"⚠️ Лимит для {model}, пробую следующую модель...")
                continue
            logging.exception(f"❌ Ошибка при запросе к модели {model}")
            return f"⚠️ Ошибка: {e}"

    return "⚠️ Все модели сейчас перегружены, попробуй чуть позже 🙏"
