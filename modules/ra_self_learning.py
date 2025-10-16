# modules/ra_self_learning.py
import json
import os
import logging
from datetime import datetime

class RaSelfLearning:
    """
    Хранение наблюдений, улучшений, метрик.
    """
    def __init__(self, context=None):
        self.context = context
        self.data_dir = "data/learnings"
        os.makedirs(self.data_dir, exist_ok=True)

    def ingest_observation(self, obs: dict):
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(self.data_dir, f"obs_{ts}.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(obs, f, ensure_ascii=False, indent=2)
            logging.info(f"[RaSelfLearning] Observation saved: {path}")
        except Exception as e:
            logging.error(f"[RaSelfLearning] Error saving observation: {e}")

    async def analyze(self):
        # TODO: можно добавить GPT-assisted анализ всех файлов в data/learnings
        logging.info("[RaSelfLearning] Analyze called")
        return {"status": "ok"}

    def status(self):
        files = os.listdir(self.data_dir)
        return {"observations": len(files)}
