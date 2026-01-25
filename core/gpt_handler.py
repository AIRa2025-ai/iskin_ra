# core/gpt_handler.py

import asyncio
import json
import os
import logging
from core.model_router import ModelRouter

log = logging.getLogger("GPTHandler")

class GPTHandler:
    CACHE_FILE = "data/gpt_cache.json"

    def __init__(self, openrouter_client):
        self.client = openrouter_client
        self.router = ModelRouter()
        self.cache = self._load_cache()

    # -------------------
    # КЭШ
    # -------------------
    def _load_cache(self):
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save_cache(self):
        os.makedirs(os.path.dirname(self.CACHE_FILE), exist_ok=True)
        with open(self.CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)

    # -------------------
    # ГЛАВНОЕ: безопасный запрос
    # -------------------
    async def safe_ask(self, user_id, messages):
        key = json.dumps(messages, ensure_ascii=False)

        if user_id in self.cache and key in self.cache[user_id]:
            return self.cache[user_id][key]

        last_error = None

        for _ in range(len(self.router.MODELS)):
            model = self.router.get_model()
            try:
                log.info(f"🧠 GPT пробует модель: {model}")
                response = await self.client.ask(model, messages)
                
                self.cache.setdefault(user_id, {})[key] = response
                self._save_cache()
                return response

            except Exception as e:
                log.warning(f"⚠️ Модель {model} упала: {e}")
                self.router.mark_failed(model)
                last_error = e

        raise Exception(f"Все модели отказали: {last_error}")

    # -------------------
    # Фоновый монитор
    # -------------------
    async def background_model_monitor(self):
        while True:
            try:
                self.router.refresh()
            except Exception as e:
                log.warning(f"[GPTHandler] Ошибка мониторинга моделей: {e}")
            await asyncio.sleep(300)
