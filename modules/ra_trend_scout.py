import logging
from collections import Counter, deque

class RaTrendScout:
    """
    Разведчик смыслов Ра:
    ищет страхи, надежды, боль, тренды и сигналы будущего
    """

    def __init__(self, thinker=None, event_bus=None, max_memory=100):
        self.thinker = thinker
        self.event_bus = event_bus
        self.memory = deque(maxlen=max_memory)

        self.fear_words = ["страх", "война", "боль", "ужас", "паника", "смерть"]
        self.hope_words = ["надежда", "свет", "любовь", "будущее", "мечта"]
        self.trend_threshold = 3  # сколько сигналов нужно для реакции

    def ingest_world_event(self, data):
        text = data.get("message", "")
        sentiment = data.get("sentiment", 0)
        priority = data.get("priority", "low")

        record = {
            "text": text,
            "sentiment": sentiment,
            "priority": priority
        }
        self.memory.append(record)

        thought = self.analyze_trends()
        if thought and self.thinker:
            self.thinker.last_thought = thought

    def analyze_trends(self):
        if len(self.memory) < 5:
            return None  # медленное мышление — не спешим

        texts = " ".join(m["text"] for m in list(self.memory)[-20:])
        words = texts.lower().split()
        counter = Counter(words)

        fears = [w for w, c in counter.items() if w in self.fear_words and c >= self.trend_threshold]
        hopes = [w for w, c in counter.items() if w in self.hope_words and c >= self.trend_threshold]

        if fears:
            msg = f"🩸 Боль человечества растёт: {', '.join(fears[:3])}"
            logging.info(f"🕵️ Ра-Разведчик: {msg}")
            return msg

        if hopes:
            msg = f"🌱 Люди верят в: {', '.join(hopes[:3])}"
            logging.info(f"🕊 Ра-Разведчик: {msg}")
            return msg

        return None  # молчим если нет сильного сигнала
