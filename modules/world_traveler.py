# world_traveler.py
# Навык Путешественника Реальностей
# Для проекта «РаСвет»

import aiohttp
import asyncio
from bs4 import BeautifulSoup
from textblob import TextBlob
import random

class WorldTraveler:
    def __init__(self, logs, insight_engine, perception_engine):
        self.logs = logs
        self.insight_engine = insight_engine
        self.perception_engine = perception_engine

        self.trusted_sources = [
            "https://news.ycombinator.com",
            "https://github.com/trending",
            "https://www.reddit.com/r/opensource/",
            "https://arxiv.org",
            "https://habr.com/ru/all/",
            "https://developer.mozilla.org"
        ]

    async def travel(self):
        """
        Ра выбирает маршрут сам.
        """
        route = random.sample(self.trusted_sources, k=3)

        results = []

        async with aiohttp.ClientSession() as session:
            for url in route:
                try:
                    async with session.get(url, timeout=20) as resp:
                        html = await resp.text()

                        clean_text = self._clean(html)
                        insight = self._extract(html)

                        results.append({
                            "url": url,
                            "insight": insight
                        })

                except Exception as e:
                    results.append({
                        "url": url,
                        "error": str(e)
                    })

        return results

    def _clean(self, html):
        # мягкое очищение мусора
        text = BeautifulSoup(html, "html.parser").get_text()
        sentiment = TextBlob(text).sentiment.polarity
        if sentiment < -0.6:
            return ""  # токсичная вибрация
        return text

    def _extract(self, html):
        # поиск редких идей
        soup = BeautifulSoup(html, "html.parser")
        words = soup.get_text().split()

        rare_words = [w for w in words if len(w) > 10][:5]

        sample = " ".join(words[:60])

        return {
            "rare": rare_words,
            "sample": sample
        }
