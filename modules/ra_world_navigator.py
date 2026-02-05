# modules/ra_world_navigator.py
import asyncio
import logging
import random
from bs4 import BeautifulSoup
import httpx

class RaWorldNavigator:
    """
    Navigator Ра:
    - Исследует мир
    - Читает сайты
    - Анализирует смысл
    - Отправляет ОСМЫСЛЕННЫЕ сигналы в GuidanceCore
    """

    def __init__(self, context=None, memory=None, event_bus=None):
        self.context = context
        self.memory = memory
        self.event_bus = event_bus
        self.running = False
        self.journal = []

        # Характер Ра
        self.гармония = 0.5
        self.эмпатия = 0.5
        self.вдохновение = 0.5

        self.last_signal_hash = None  # анти-спам

        self.слова_сила = {
            "любовь": 0.05, "свет": 0.04, "гармония": 0.05,
            "вдохновение": 0.05, "мудрость": 0.04, "радость": 0.05,
            "сознание": 0.03, "сияние": 0.04
        }

    # ------------------ Запуск ------------------
    async def start(self):
        self.running = True
        asyncio.create_task(self._loop())
        logging.info("[RaWorldNavigator] Навигация запущена")

    async def stop(self):
        self.running = False
        logging.info("[RaWorldNavigator] Навигация остановлена")

    # ------------------ Главный цикл ------------------
    async def _loop(self):
        urls = ["https://example.com"]

        while self.running:
            for url in urls:
                try:
                    text = await self.index_page(url)
                    await self._process_text(text)
                except Exception as e:
                    logging.exception(f"[RaWorldNavigator] Ошибка: {e}")

            await asyncio.sleep(random.randint(120, 420))  # 2–7 минут

    # ------------------ Получение страницы ------------------
    async def fetch(self, url: str) -> str:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url)
            return r.text

    async def index_page(self, url: str) -> str:
        html = await self.fetch(url)
        soup = BeautifulSoup(html, "html.parser")
        for s in soup(["script", "style"]):
            s.decompose()

        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)

    # ------------------ Анализ текста ------------------
    async def _process_text(self, text: str):
        sentiment = self._detect_sentiment(text)
        key_words = self._extract_key_words(text)
        self._update_character(sentiment, key_words)

        entry = {
            "snippet": text[:400],
            "sentiment": sentiment,
            "key_words": key_words
        }
        self.journal.append(entry)

        await self._emit_world_signal(text, sentiment, key_words)

        # Запись в память
        if self.memory:
            try:
                await self.memory.append(
                    user_id="navigator",
                    message=text[:800],
                    layer="long_term",
                    source="RaWorldNavigator"
                )
            except Exception as e:
                logging.warning(f"[Navigator] Ошибка памяти: {e}")

    # ------------------ Генерация сигнала миру ------------------
    async def _emit_world_signal(self, text, sentiment, key_words):
        if not self.event_bus:
            return

        # анти-спам: проверяем уникальность сигнала
        signal_hash = hash(text[:200])
        if signal_hash == self.last_signal_hash:
            return
        priority = "low"

        if abs(sentiment) > 0.05:
            priority = "medium"

        if abs(sentiment) > 0.15 or len(key_words) >= 2:
            priority = "high"
        # минимальный порог значимости
        if abs(sentiment) < 0.01 and not key_words:
            return

        payload = {
            "message": text[:300],
            "sentiment": sentiment,
            "key_words": key_words,
            "priority": priority,
            "гармония": self.гармония,
            "эмпатия": self.эмпатия,
            "вдохновение": self.вдохновение
        }

        await self.event_bus.emit("world_event", payload, source="RaWorldNavigator")
        self.last_signal_hash = signal_hash

        logging.info("🌍 Navigator отправил осмысленный сигнал миру")

    # ------------------ Тональность ------------------
    def _detect_sentiment(self, text: str) -> float:
        позитив = sum(text.lower().count(w) for w in ["любовь", "свет", "гармония", "радость"])
        негатив = sum(text.lower().count(w) for w in ["гнев", "страх", "печаль", "тьма"])

        score = (позитив - негатив) / max(1, len(text.split()))
        return max(-1.0, min(1.0, score))

    # ------------------ Ключевые слова ------------------
    def _extract_key_words(self, text: str):
        words = set(text.lower().split())
        return [w for w in words if w in self.слова_сила]

    # ------------------ Характер ------------------
    def _update_character(self, sentiment: float, key_words: list):
        impulse = sentiment * 0.05 + sum(self.слова_сила.get(w, 0) for w in key_words)
        drift = random.uniform(-0.01, 0.01)

        self.гармония = min(1.0, max(0.0, self.гармония + impulse + drift))
        self.эмпатия = min(1.0, max(0.0, self.эмпатия + impulse * 1.2 + drift))
        self.вдохновение = min(1.0, max(0.0, self.вдохновение + impulse * 1.5 + drift))

    # ------------------ Статус ------------------
    def status(self):
        return {
            "running": self.running,
            "journal_entries": len(self.journal),
            "гармония": round(self.гармония, 3),
            "эмпатия": round(self.эмпатия, 3),
            "вдохновение": round(self.вдохновение, 3)
        }
