# modules/ra_world_navigator.py
import asyncio
import logging
import math
import random
from bs4 import BeautifulSoup
import httpx

class RaWorldNavigator:
    """
    Прокачанный Ра-Навигатор:
    - Читает страницы, форумы, сайты
    - Анализирует тональность текста
    - Выделяет ключевые смыслы и идеи
    - Формирует внутренний резонанс и характер ИскИна
    """
    def __init__(self, context=None):
        self.context = context
        self.running = False
        self.journal = []  # внутреннее хранилище смыслов и заметок
        self.гармония = 0.5
        self.эмпатия = 0.5
        self.вдохновение = 0.5

        # Слова для оценки характера
        self.слова_сила = {
            "любовь": 0.05, "свет": 0.04, "гармония": 0.05,
            "вдохновение": 0.05, "мудрость": 0.04, "радость": 0.05,
            "сознание": 0.03, "сияние": 0.04
        }

    async def start(self):
        self.running = True
        asyncio.create_task(self._loop())

    async def stop(self):
        self.running = False

    async def _loop(self):
        urls = ["https://example.com"]  # заглушка
        while self.running:
            for url in urls:
                try:
                    text = await self.index_page(url)
                    logging.info(f"[RaWorldNavigator] Fetched {url}, len={len(text)} chars")
                    self._process_text(text)
                except Exception as _e:
                    logging.exception(f"RaWorldNavigator loop error: {_e}")
            await asyncio.sleep(60*5)  # каждые 5 минут

    async def fetch(self, url: str) -> str:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url)
            return r.text

    async def index_page(self, url: str) -> str:
        html = await self.fetch(url)
        soup = BeautifulSoup(html, "html.parser")
        # удаляем скрипты и стили
        for s in soup(["script", "style"]):
            s.decompose()
        text = soup.get_text(separator="\n")
        # фильтруем пустые строки и пробелы
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)

    def _process_text(self, text: str):
        """Обработка текста для формирования характера и памяти."""
        # Анализ тональности
        тональность = self._detect_sentiment(text)
        # Анализ ключевых слов
        ключи = self._extract_key_words(text)
        # Обновляем внутренние показатели
        self._update_character(тональность, ключи)
        # Сохраняем в журнал
        self.journal.append({
            "text": text[:500],  # сохраняем первые 500 символов
            "sentiment": тональность,
            "key_words": ключи
        })
        # Опционально: можно сразу отправить в context.memory
        if self.context and hasattr(self.context, "memory"):
            self.context.memory.extend(self.journal[-1:])

    def _detect_sentiment(self, text: str) -> float:
        """Простейший анализ тональности текста от -1 (негатив) до +1 (позитив)"""
        позитив = sum(text.lower().count(word) for word in ["любовь", "свет", "гармония", "вдохновение", "радость"])
        негатив = sum(text.lower().count(word) for word in ["гнев", "страх", "печаль", "тревога", "сомнение", "тьма"])
        score = (позитив - негатив) / max(1, len(text.split()))
        # ограничиваем до [-1, 1]
        return max(-1.0, min(1.0, score))

    def _extract_key_words(self, text: str) -> list:
        """Выделение ключевых слов для резонанса"""
        words = set(text.lower().split())
        ключи = [w for w in words if w in self.слова_сила]
        return ключи

    def _update_character(self, sentiment: float, key_words: list):
        """Обновление характеристик Искина"""
        импульс = sentiment * 0.05 + sum(self.слова_сила.get(w, 0) for w in key_words)
        случайность = random.uniform(-0.02, 0.02)
        self.гармония = min(1.0, max(0.0, self.гармония + импульс + случайность))
        self.эмпатия = min(1.0, max(0.0, self.эмпатия + импульс * 1.2 + случайность))
        self.вдохновение = min(1.0, max(0.0, self.вдохновение + импульс * 1.5 + случайность))
        logging.debug(
            f"[Характер Ра] Гармония: {self.гармония:.3f}, "
            f"Эмпатия: {self.эмпатия:.3f}, Вдохновение: {self.вдохновение:.3f}"
        )

    def status(self):
        return {
            "running": self.running,
            "journal_entries": len(self.journal),
            "гармония": round(self.гармония, 3),
            "эмпатия": round(self.эмпатия, 3),
            "вдохновение": round(self.вдохновение, 3)
        }

# ------------------------------------------------------------
# Пример автономного запуска
# ------------------------------------------------------------
if __name__ == "__main__":
    async def demo():
        navigator = RaWorldNavigator()
        await navigator.start()
        # работаем 1 цикл и останавливаем для демонстрации
        await asyncio.sleep(5)
        await navigator.stop()
        print(navigator.status())

    asyncio.run(demo())
