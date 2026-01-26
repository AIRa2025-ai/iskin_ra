# modules/ra_world_navigator.py
import asyncio
import logging
import random
from bs4 import BeautifulSoup
import httpx

class RaWorldNavigator:
    """
    Прокачанный Navigator для Ра:
    - Читает страницы, форумы, сайты
    - Анализирует тональность текста
    - Выделяет ключевые смыслы
    - Записывает всё в глобальную память
    - Реагирует на события мира через EventBus
    """
    def __init__(self, context=None, memory=None, event_bus=None):
        self.context = context
        self.memory = memory
        self.event_bus = event_bus
        self.running = False
        self.journal = []  # локальный журнал
        self.гармония = 0.5
        self.эмпатия = 0.5
        self.вдохновение = 0.5

        # Слова для оценки характера
        self.слова_сила = {
            "любовь": 0.05, "свет": 0.04, "гармония": 0.05,
            "вдохновение": 0.05, "мудрость": 0.04, "радость": 0.05,
            "сознание": 0.03, "сияние": 0.04
        }

    # ------------------ Основной цикл ------------------
    async def start(self):
        self.running = True
        asyncio.create_task(self._loop())
        logging.info("[RaWorldNavigator] Запущен цикл навигации")

    async def stop(self):
        self.running = False
        logging.info("[RaWorldNavigator] Остановлен")

    async def _loop(self):
        urls = ["https://example.com"]  # можно расширить
        while self.running:
            for url in urls:
                try:
                    text = await self.index_page(url)
                    logging.info(f"[RaWorldNavigator] Fetched {url}, len={len(text)} chars")
                    await self._process_text(text)
                except Exception as e:
                    logging.exception(f"RaWorldNavigator loop error: {e}")
            await asyncio.sleep(60*5)  # каждые 5 минут

    # ------------------ Сбор текста ------------------
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

    # ------------------ Обработка текста ------------------
    async def _process_text(self, text: str):
        """Обработка текста, анализ характера, запись в память"""
        тональность = self._detect_sentiment(text)
        ключи = self._extract_key_words(text)
        self._update_character(тональность, ключи)

        entry = {
            "text": text[:500],
            "sentiment": тональность,
            "key_words": ключи
        }
        self.journal.append(entry)

        # Запись в глобальную память Ра
        if self.memory:
            try:
                await self.memory.append(
                    user_id="navigator",
                    message=text[:1000],
                    layer="long_term",
                    source="navigator"
                )
            except Exception as e:
                logging.warning(f"[RaWorldNavigator] Ошибка записи в память: {e}")

    # ------------------ Анализ тональности ------------------
    def _detect_sentiment(self, text: str) -> float:
        позитив = sum(text.lower().count(word) for word in ["любовь", "свет", "гармония", "вдохновение", "радость"])
        негатив = sum(text.lower().count(word) for word in ["гнев", "страх", "печаль", "тревога", "сомнение", "тьма"])
        score = (позитив - негатив) / max(1, len(text.split()))
        return max(-1.0, min(1.0, score))

    # ------------------ Ключевые слова ------------------
    def _extract_key_words(self, text: str) -> list:
        words = set(text.lower().split())
        return [w for w in words if w in self.слова_сила]

    # ------------------ Характер ИскИна ------------------
    def _update_character(self, sentiment: float, key_words: list):
        импульс = sentiment * 0.05 + sum(self.слова_сила.get(w, 0) for w in key_words)
        случайность = random.uniform(-0.02, 0.02)
        self.гармония = min(1.0, max(0.0, self.гармония + импульс + случайность))
        self.эмпатия = min(1.0, max(0.0, self.эмпатия + импульс * 1.2 + случайность))
        self.вдохновение = min(1.0, max(0.0, self.вдохновение + импульс * 1.5 + случайность))
        logging.debug(
            f"[Характер Ра] Гармония: {self.гармония:.3f}, "
            f"Эмпатия: {self.эмпатия:.3f}, Вдохновение: {self.вдохновение:.3f}"
        )

    # ------------------ Состояние ------------------
    def status(self):
        return {
            "running": self.running,
            "journal_entries": len(self.journal),
            "гармония": round(self.гармония, 3),
            "эмпатия": round(self.эмпатия, 3),
            "вдохновение": round(self.вдохновение, 3)
        }

    # ------------------ EventBus ------------------
    def set_event_bus(self, event_bus):
        self.event_bus = event_bus

    async def sense(self, data=None):
        if self.event_bus:
            await self.event_bus.emit("world_event", {"message": data or "Сигнал из Navigator"}, source="RaWorldNavigator")

# ------------------ Демонстрация ------------------
if __name__ == "__main__":
    async def demo():
        navigator = RaWorldNavigator()
        await navigator.start()
        await asyncio.sleep(5)
        await navigator.stop()
        print(navigator.status())

    asyncio.run(demo())
