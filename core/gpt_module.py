# core/gpt_module.py
import os
import aiohttp
import logging
import asyncio
from github_commit import create_commit_push

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise RuntimeError("❌ Не задан OPENROUTER_API_KEY")

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

logging.basicConfig(level=logging.INFO)


async def ask_openrouter_single(session, user_id, messages, model, append_user_memory=None):
    url = "https://openrouter.ai/api/v1/chat/completions"
    payload = {"model": model, "messages": messages, "temperature": 0.7}
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://iskin-ra.fly.dev",
        "X-Title": "iskin-ra",
    }

    async with session.post(url, headers=headers, json=payload) as resp:
        if resp.status != 200:
            text = await resp.text()
            logging.error(f"❌ Ошибка API {resp.status}: {text}")
            raise Exception(f"{resp.status}: {text}")

        data = await resp.json()

        if not data.get("choices") or not data["choices"][0].get("message"):
            raise Exception(f"Модель {model} не вернула choices")

        answer = data["choices"][0]["message"]["content"]

        # чистим токены вроде <｜begin▁of▁sentence｜>
        answer = answer.replace("<｜begin▁of▁sentence｜>", "").replace("<｜end▁of▁sentence｜>", "")

        if append_user_memory:
            append_user_memory(user_id, messages[-1]["content"], answer)

        return answer.strip()


async def ask_openrouter_with_fallback(user_id, messages_payload, append_user_memory=None):
    async with aiohttp.ClientSession() as session:
        errors = []
        for model in MODELS:
            try:
                logging.info(f"💡 Пробуем модель {model}")
                answer = await ask_openrouter_single(session, user_id, messages_payload, model, append_user_memory)
                return answer  # возвращаем сразу успешный ответ
            except Exception as e:
                err_str = str(e)
                logging.warning(f"⚠️ Ошибка при модели {model}: {err_str}")
                errors.append(f"{model}: {err_str}")
                continue  # пробуем следующую модель

    logging.error("⚠️ Все модели сейчас перегружены или не вернули ответ:\n" + "\n".join(errors))
    return "⚠️ Все модели сейчас перегружены или не смогли ответить. Попробуй позже 🙏"


# Совместимость со старым вызовом
safe_ask_openrouter = ask_openrouter_with_fallback
