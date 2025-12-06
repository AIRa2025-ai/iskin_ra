# core/gpt_module_pro.py — прокачанная версия GPT-модуля для Ра с умным приоритетом моделей
import os
import aiohttp
import logging
import asyncio
import json
from datetime import datetime, timedelta

# для будущего авто-коммита/PR
try:
    from github_commit import create_commit_push
except ImportError:
    create_commit_push = None

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
CACHE_FILE = "data/response_cache.json"
os.makedirs("data", exist_ok=True)

excluded_models: dict[str, datetime] = {}  # модель: до какого времени исключена
last_working_model: str | None = None
MODEL_COOLDOWN_HOURS = 2

# --- Приоритет моделей по скорости ---
MODEL_SPEED_FILE = "data/model_speed.json"
model_speed: dict[str, float] = {}  # модель: среднее время ответа (сек)

def load_model_speed():
    global model_speed
    if os.path.exists(MODEL_SPEED_FILE):
        with open(MODEL_SPEED_FILE, "r", encoding="utf-8") as f:
            model_speed = json.load(f)

def save_model_speed():
    with open(MODEL_SPEED_FILE, "w", encoding="utf-8") as f:
        json.dump(model_speed, f, ensure_ascii=False, indent=2)

load_model_speed()

# === Кэширование ===
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
    if user_id not in data:
        data[user_id] = {}
    data[user_id][text] = answer
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# === Один запрос к OpenRouter с замером скорости ===
async def ask_openrouter_single(session, user_id, messages, model):
    url = "https://openrouter.ai/api/v1/chat/completions"
    payload = {"model": model, "messages": messages, "temperature": 0.7}
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://iskin-ra.fly.dev",
        "X-Title": "iskin-ra",
    }

    start_time = datetime.now()
    async with session.post(url, headers=headers, json=payload) as resp:
        text_resp = await resp.text()
        if resp.status != 200:
            logging.error(f"❌ Ошибка API {resp.status}: {text_resp}")
            raise Exception(f"{resp.status}: {text_resp}")
        data = await resp.json()
        if "choices" not in data or not data["choices"]:
            raise Exception(f"Модель {model} не вернула choices")
        answer = data["choices"][0]["message"]["content"].strip()

    # обновление скорости модели
    elapsed = (datetime.now() - start_time).total_seconds()
    prev = model_speed.get(model, elapsed)
    model_speed[model] = (prev + elapsed) / 2  # простое скользящее среднее
    save_model_speed()

    return answer

# === Очистка истёкших исключений ===
def refresh_excluded_models():
    now = datetime.now()
    to_remove = [m for m, until in excluded_models.items() if until <= now]
    for m in to_remove:
        logging.info(f"♻️ Модель {m} снова доступна после cooldown")
        excluded_models.pop(m)

# === Безопасный запрос с кэшем и fallback и приоритетом скорости ===
async def safe_ask_openrouter(user_id: str, messages_payload: list[dict]):
    global last_working_model
    text_message = messages_payload[-1]["content"]
    cached = load_cache(user_id, text_message)
    if cached:
        logging.info("💾 Используем кэшированный ответ")
        return cached

    refresh_excluded_models()

    async with aiohttp.ClientSession() as session:
        usable_models = [m for m in MODELS if m not in excluded_models]

        # сортируем по скорости (меньшее время — выше)
        usable_models.sort(key=lambda m: model_speed.get(m, float('inf')))

        # сначала пробуем последнюю рабочую модель
        if last_working_model and last_working_model in usable_models:
            usable_models.remove(last_working_model)
            usable_models = [last_working_model] + usable_models

        if not usable_models:
            logging.error("⚠️ Все модели временно недоступны.")
            return "⚠️ Все модели временно недоступны, попробуй позже 🙏"

        for model in usable_models:
            try:
                logging.info(f"💡 Пробуем модель {model}")
                answer = await ask_openrouter_single(session, user_id, messages_payload, model)
                last_working_model = model
                save_cache(user_id, text_message, answer)
                break
            except Exception as e:
                logging.warning(f"⚠️ Модель {model} временно исключена: {e}")
                excluded_models[model] = datetime.now() + timedelta(hours=MODEL_COOLDOWN_HOURS)
        else:
            return "⚠️ Все модели временно недоступны, попробуй позже 🙏"

        async def background_cache(model):
            try:
                ans = await ask_openrouter_single(session, user_id, messages_payload, model)
                save_cache(user_id, text_message, ans)
            except Exception:
                excluded_models[model] = datetime.now() + timedelta(hours=MODEL_COOLDOWN_HOURS)

        for model in usable_models:
            if model != last_working_model:
                asyncio.create_task(background_cache(model))

        return answer

# === Заглушка для быстрого вызова ===
async def ask_openrouter_with_fallback(prompt: str):
    return f"[RaStub] Ответ на: {prompt[:50]}..."
