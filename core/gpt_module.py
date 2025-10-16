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

# --- Функция одного запроса к OpenRouter ---
async def ask_openrouter_single(session, user_id, messages, model, append_user_memory=None, _parse_openrouter_response=None):
    url = "https://openrouter.ai/api/v1/chat/completions"
    payload = {"model": model, "messages": messages, "temperature": 0.7}
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://iskin-ra.fly.dev",
        "X-Title": "iskin-ra",
    }

    async with session.post(url, headers=headers, json=payload) as resp:
        data = await resp.json()
        choices = data.get("choices")
        if not choices or not isinstance(choices, list):
            raise ValueError(f"Модель {model} не вернула choices")
        answer = choices[0]["message"]["content"]
        # очищаем служебные токены
        answer = answer.replace("<｜begin▁of▁sentence｜>", "").strip()

        if _parse_openrouter_response:
            answer = _parse_openrouter_response(data)
        if append_user_memory:
            append_user_memory(user_id, messages[-1]["content"], answer)
        return answer

# --- Обёртка с перебором моделей ---
async def ask_openrouter_with_fallback(user_id, messages_payload, append_user_memory=None, _parse_openrouter_response=None):
    async with aiohttp.ClientSession() as session:
        errors = []
        for model in MODELS:
            try:
                logging.info(f"💡 Пробуем модель {model}")
                return await ask_openrouter_single(
                    session, user_id, messages_payload, model,
                    append_user_memory, _parse_openrouter_response
                )
            except Exception as e:
                err_str = str(e)
                if "429" in err_str:
                    logging.warning(f"⚠️ Лимит для {model}, пробую следующую модель...")
                    errors.append(f"{model}: {err_str}")
                    continue
                logging.error(f"❌ Ошибка при запросе к {model}: {err_str}")
                return f"⚠️ Ошибка: {err_str}"

    logging.error("⚠️ Все модели сейчас перегружены:\n" + "\n".join(errors))
    return "⚠️ Все модели сейчас перегружены, попробуй позже 🙏"
# --- Совместимость со старыми вызовами ---
safe_ask_openrouter = ask_openrouter_with_fallback

# --- Главная функция ---
async def main():
    user_id = "user123"
    messages_payload = [{"role": "user", "content": "Привет, Ра!"}]

    # Получаем ответ от OpenRouter
    answer = await ask_openrouter_with_fallback(user_id, messages_payload)
    logging.info(f"💬 Ответ от Ra: {answer}")
    
# --- Запуск ---
if __name__ == "__main__":
    asyncio.run(main())
