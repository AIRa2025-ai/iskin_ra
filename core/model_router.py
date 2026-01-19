# core/model_router.py

import random
import json
import os
import logging
from datetime import datetime, timedelta

log = logging.getLogger("ModelRouter")

class ModelRouter:
    MODELS = [
        "allenai/molmo-2-8b:free",
        "xiaomi/mimo-v2-flash:free",
        "nvidia/nemotron-3-nano-30b-a3b:free",
        "mistralai/devstral-2512:free",
        "arcee-ai/trinity-mini:free",
        "tngtech/tng-r1t-chimera:free",
        "nvidia/nemotron-nano-12b-v2-vl:free",
        "qwen/qwen3-next-80b-a3b-instruct:free",
        "nvidia/nemotron-nano-9b-v2:free",
        "openai/gpt-oss-120b:free",
        "openai/gpt-oss-20b:free",
        "z-ai/glm-4.5-air:free",
        "qwen/qwen3-coder:free",
        "moonshotai/kimi-k2:free",
        "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
        "google/gemma-3n-e2b-it:free",
        "tngtech/deepseek-r1t2-chimera:free",
        "deepseek/deepseek-r1-0528:free",
        "google/gemma-3n-e4b-it:free",
        "tngtech/deepseek-r1t-chimera:free",
        "mistralai/mistral-small-3.1-24b-instruct:free",
        "google/gemma-3-4b-it:free",
        "google/gemma-3-12b-it:free",
        "google/gemma-3-27b-it:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "meta-llama/llama-3.2-3b-instruct:free",
        "qwen/qwen-2.5-vl-7b-instruct:free",
        "nousresearch/hermes-3-llama-3.1-405b:free",
        "meta-llama/llama-3.1-405b-instruct:free"
    ]
    MODEL_COOLDOWN_HOURS = 2
    MODEL_SPEED_FILE = "data/model_speed.json"

    def __init__(self):
        self.excluded = {}
        self.model_speed = self._load_speed()

    def _load_speed(self):
        if os.path.exists(self.MODEL_SPEED_FILE):
            try:
                with open(self.MODEL_SPEED_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_speed(self):
        os.makedirs(os.path.dirname(self.MODEL_SPEED_FILE), exist_ok=True)
        with open(self.MODEL_SPEED_FILE, "w", encoding="utf-8") as f:
            json.dump(self.model_speed, f, ensure_ascii=False, indent=2)

    def mark_failed(self, model: str):
        self.excluded[model] = datetime.utcnow() + timedelta(hours=self.MODEL_COOLDOWN_HOURS)

    def refresh(self):
        now = datetime.utcnow()
        self.excluded = {m: t for m, t in self.excluded.items() if t > now}

    def get_model(self) -> str:
        self.refresh()
        available = [m for m in self.MODELS if m not in self.excluded]
        if not available:
            log.warning("⚠️ Все модели на кулдауне")
            return random.choice(self.MODELS)
        return random.choice(available)
