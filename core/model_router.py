# core/model_router.py

import random
import json
import os
import logging
from datetime import datetime, timedelta

log = logging.getLogger("ModelRouter")

class ModelRouter:
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
