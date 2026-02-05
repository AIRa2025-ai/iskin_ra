# modules/ra_trend_scout.py
import logging
from collections import Counter

class RaTrendScout:
    """
    Разведчик смыслов Ра:
    ищет тренды, страхи, надежды и боль человечества
    """

    def __init__(self, thinker=None, event_bus=None):
        self.thinker = thinker
        self.event_bus = event_bus
        self.memory = []

    def ingest_world_event(self, data):
        text = data.get("message", "")
        sentiment = data.get("sentiment", 0)
        priority = data.get("priority", "low")

        self.memory.append({
            "text": text,
            "sentiment": sentiment,
            "priority": priority
        })

        # передаём Thinker мысль
        if self.thinker:
            thought = self.analyze_trends()
            if thought:
                self.thinker.last_thought = thought

    def analyze_trends(self):
        if len(self.memory) < 3:
            return None

        texts = " ".join(m["text"] for m in self.memory[-10:])
        words = texts.lower().split()

        counter = Counter(words)

        fears = [w for w, c in counter.items() if w in ["страх", "война", "боль", "ужас", "паника"]]
        hopes = [w for w, c in counter.items() if w in ["надежда", "свет", "любовь", "будущее", "мечта"]]

        if fears:
            msg = f"Люди боятся: {', '.join(fears[:3])}"
            logging.info(f"🕵️ Ра-разведка: {msg}")
            return msg

        if hopes:
            msg = f"Люди надеются на: {', '.join(hopes[:3])}"
            logging.info(f"🌱 Ра-разведка: {msg}")
            return msg

        return "Формируется новый тренд мышления людей"
