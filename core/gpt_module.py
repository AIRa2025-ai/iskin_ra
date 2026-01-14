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
# КЛАСС GPT
# =========================

class GPTHandler:
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
    MODEL_COOLDOWN_HOURS = 2
    CACHE_FILE = "data/response_cache.json"
    MODEL_SPEED_FILE = "data/model_speed.json"

    def __init__(self, api_key: str | None = None):
        os.makedirs("data", exist_ok=True)
        self.OPENROUTER_API_KEY = api_key or os.getenv("OPENROUTER_API_KEY")
        self.GPT_ENABLED = bool(self.OPENROUTER_API_KEY)
        self.excluded_models: dict[str, datetime] = {}
        self.model_speed: dict[str, float] = {}
        self.last_working_model: str | None = None
        self.background_task: asyncio.Task | None = None

        if not self.GPT_ENABLED:
            log.warning("⚠️ GPT выключен — нет OPENROUTER_API_KEY")
        else:
            log.info("✅ GPT-модуль инициализирован")

        self.load_model_speed()

    # =========================
    # ЗАГРУЗКА / СОХРАНЕНИЕ
    # =========================
    def load_model_speed(self):
        if os.path.exists(self.MODEL_SPEED_FILE):
            with open(self.MODEL_SPEED_FILE, "r", encoding="utf-8") as f:
                self.model_speed = json.load(f)

    def save_model_speed(self):
        with open(self.MODEL_SPEED_FILE, "w", encoding="utf-8") as f:
            json.dump(self.model_speed, f, ensure_ascii=False, indent=2)

    def load_cache(self, user_id: str, text: str):
        if os.path.exists(self.CACHE_FILE):
            with open(self.CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get(user_id, {}).get(text)
        return None

    def save_cache(self, user_id: str, text: str, answer: str):
        data = {}
        if os.path.exists(self.CACHE_FILE):
            with open(self.CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        data.setdefault(user_id, {})[text] = answer
        with open(self.CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def refresh_excluded_models(self):
        now = datetime.now()
        for m in list(self.excluded_models):
            if self.excluded_models[m] <= now:
                self.excluded_models.pop(m)

    # =========================
    # ЗАПРОСЫ
    # =========================
    async def ask_openrouter_single(self, session, messages, model):
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.OPENROUTER_API_KEY}",
            "X-Title": "iskin-ra"
        }
        payload = {"model": model, "messages": messages, "temperature": 0.7}

        start = datetime.now()
        async with session.post(url, headers=headers, json=payload) as resp:
            data = await resp.json()
            answer = data["choices"][0]["message"]["content"].strip()

        elapsed = (datetime.now() - start).total_seconds()
        self.model_speed[model] = (self.model_speed.get(model, elapsed) + elapsed) / 2
        self.save_model_speed()
        return answer

    async def safe_ask(self, user_id: str, messages: list[dict]):
        if not self.GPT_ENABLED:
            return "⚠️ GPT временно недоступен"

        self.refresh_excluded_models()
        text = messages[-1]["content"]

        cached = self.load_cache(user_id, text)
        if cached:
            return cached

        async with aiohttp.ClientSession() as session:
            for model in self.MODELS:
                if model in self.excluded_models:
                    continue
                try:
                    answer = await self.ask_openrouter_single(session, messages, model)
                    self.save_cache(user_id, text, answer)
                    return answer
                except Exception:
                    self.excluded_models[model] = datetime.now() + timedelta(hours=self.MODEL_COOLDOWN_HOURS)

        return "⚠️ Все модели временно недоступны"

    # =========================
    # ФОНОВЫЙ МОНИТОР
    # =========================
    async def background_model_monitor(self):
        while True:
            if not self.GPT_ENABLED:
                await asyncio.sleep(10)
                continue
            try:
                async with aiohttp.ClientSession() as session:
                    for model in self.MODELS:
                        try:
                            await self.ask_openrouter_single(session, [{"role": "system", "content": "ping"}], model)
                        except Exception:
                            self.excluded_models[model] = datetime.now() + timedelta(hours=self.MODEL_COOLDOWN_HOURS)
            except Exception as e:
                log.warning(f"monitor error: {e}")
            await asyncio.sleep(300)
