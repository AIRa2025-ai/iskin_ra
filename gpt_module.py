import os
import aiohttp
import logging
from github_commit import create_commit_push

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

MODELS = [
    "deepseek/deepseek-r1-0528:free",
    "deepseek/deepseek-chat-v3.1:free",
    "deepseek/deepseek-r1-0528-qwen3-8b:free",
    "tngtech/deepseek-r1t2-chimera:free",
    "mistralai/mistral-small-3.2-24b-instruct:free",
    "deepseek/deepseek-r1:free",
    "qwen/qwen3-14b:free",
    "mistralai/mistral-nemo:free"
]

# --- Глобальная сессия ---
session: aiohttp.ClientSession | None = None

async def get_session():
    global session
    if session is None or session.closed:
        session = aiohttp.ClientSession()
    return session


async def ask_openrouter(session, user_id, messages, model="deepseek/deepseek-r1-0528:free",
                         append_user_memory=None, _parse_openrouter_response=None):
    """
    Запрос к OpenRouter API через переданную aiohttp-сессию.
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

    logging.info(f"DEBUG: Отправляем запрос в OpenRouter ({model})")

    async with session.post(url, headers=headers, json=payload) as resp:
        text = await resp.text()

        if resp.status != 200:
            logging.error(f"❌ Ошибка API {resp.status}: {text}")
            raise Exception(f"{resp.status}: {text}")

        data = await resp.json()

        # Разбор ответа через кастомную функцию
        answer = None
        if _parse_openrouter_response:
            answer = _parse_openrouter_response(data)

        # Если не обработали — берём стандартный ответ
        if not answer:
            answer = data["choices"][0]["message"]["content"]

        # Сохраняем память
        if append_user_memory:
            append_user_memory(user_id, messages[-1]["content"], answer)

        return answer.strip(

        # пример вызова из кода Ра:
        branch_name = "auto-update-" + str(os.getpid())
        files_dict = {
            "memory_sync.py": "# test 
        change\nprint('Ra updated!')"
        }
        pr = create_commit_push(branch_name, files_dict, "обновление от Ра")
        print("✅ Создан PR:", pr["html_url"])
    
    """
    Перебирает модели при 429. Закрывает ClientSession корректно.
    """
    async with aiohttp.ClientSession() as session:
        for model in MODELS:
            try:
                return await ask_openrouter(
                    session=session,
                    user_id=user_id,
                    messages=messages_payload,
                    model=model,
                    append_user_memory=append_user_memory,
                    _parse_openrouter_response=_parse_openrouter_response
                )
            except Exception as e:
                err_str = str(e)
                if "429" in err_str:
                    logging.warning(f"⚠️ Лимит для {model}, пробую следующую модель...")
                    continue
                logging.error(f"❌ Ошибка при запросе к {model}: {err_str}")
                return f"⚠️ Ошибка: {err_str}"

    return "⚠️ Все модели сейчас перегружены, попробуй позже 🙏"
