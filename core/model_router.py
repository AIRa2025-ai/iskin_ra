# core/model_router.py
import time
import json
import os
import random
import logging

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
        self.last_used = {}

    def get_model(self) -> str:
        return random.choice(self.MODELS)
