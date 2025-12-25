# core/gpt_module.py
# GPT-модуль Ра — безопасная загрузка + ручная инициализация

import os
import aiohttp
import logging
import asyncio
import json
from datetime import datetime, timedelta

log = logging.getLogger("RaGPT")

# =========================
# ГЛОБАЛЬНОЕ СОСТОЯНИЕ
# =========================

GPT_ENABLED = False
OPENROUTER_API_KEY = None
background_task: asyncio.Task | None = None

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

CACHE_FILE = "data/response_cache.json"
MODEL_SPEED_FILE = "data/model_speed.json"
MODEL_COOLDOWN_HOURS = 2

excluded_models: dict[str, datetime] = {}
model_speed: dict[str, float] = {}
last_working_model: str | None = None

os.makedirs("data", exist_ok=True)

# =========================
# ЗАГРУЗКА ДАННЫХ (БЕЗ СЕТИ)
# =========================

def load_model_speed():
    global model_speed
    if os.path.exists(MODEL_SPEED_FILE):
        with open(MODEL_SPEED_FILE, "r", encoding="utf-8") as f:
            model_speed = json.load(f)

def save_model_speed():
    with open(MODEL_SPEED_FILE, "w", encoding="utf-8") as f:
        json.dump(model_speed, f, ensure_ascii=False, indent=2)

load_model_speed()

# =========================
# ИНИЦИАЛИЗАЦИЯ (ГЛАВНОЕ)
# =========================

def init(api_key: str | None = None):
    """
    Вызывается ПОСЛЕ старта бота и event loop
    """
    global GPT_ENABLED, OPENROUTER_API_KEY, background_task

    OPENROUTER_API_KEY = api_key or os.getenv("OPENROUTER_API_KEY")

    if not OPENROUTER_API_KEY:
        log.warning("⚠️ GPT выключен — нет OPENROUTER_API_KEY")
        GPT_ENABLED = False
        return False

    GPT_ENABLED = True
    log.info("✅ GPT-модуль инициализирован")

    return True

# =========================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =========================

def load_cache(user_id: str, text: str):
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get(user_id, {}).get(text)
    return None

def save_cache(user_id: str, text: str, answer: str):
    data = {}
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    data.setdefault(user_id, {})[text] = answer
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def refresh_excluded_models():
    now = datetime.now()
    for m in list(excluded_models):
        if excluded_models[m] <= now:
            excluded_models.pop(m)

# =========================
# ЗАПРОСЫ
# =========================

async def ask_openrouter_single(session, messages, model):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "X-Title": "iskin-ra"
    }
    payload = {"model": model, "messages": messages, "temperature": 0.7}

    start = datetime.now()
    async with session.post(url, headers=headers, json=payload) as resp:
        data = await resp.json()
        answer = data["choices"][0]["message"]["content"].strip()

    elapsed = (datetime.now() - start).total_seconds()
    model_speed[model] = (model_speed.get(model, elapsed) + elapsed) / 2
    save_model_speed()

    return answer

async def safe_ask(user_id: str, messages: list[dict]):
    if not GPT_ENABLED:
        return "⚠️ GPT временно недоступен"

    refresh_excluded_models()
    text = messages[-1]["content"]

    cached = load_cache(user_id, text)
    if cached:
        return cached

    async with aiohttp.ClientSession() as session:
        for model in MODELS:
            if model in excluded_models:
                continue
            try:
                answer = await ask_openrouter_single(session, messages, model)
                save_cache(user_id, text, answer)
                return answer
            except Exception:
                excluded_models[model] = datetime.now() + timedelta(hours=MODEL_COOLDOWN_HOURS)

    return "⚠️ Все модели временно недоступны"

# =========================
# ФОНОВЫЙ МОНИТОР
# =========================

async def background_model_monitor():
    while True:
        if not GPT_ENABLED:
            await asyncio.sleep(10)
            continue
        try:
            async with aiohttp.ClientSession() as session:
                for model in MODELS:
                    try:
                        await ask_openrouter_single(
                            session,
                            [{"role": "system", "content": "ping"}],
                            model
                        )
                    except Exception:
                        excluded_models[model] = datetime.now() + timedelta(hours=MODEL_COOLDOWN_HOURS)
        except Exception as e:
            log.warning(f"monitor error: {e}")
        await asyncio.sleep(300)
