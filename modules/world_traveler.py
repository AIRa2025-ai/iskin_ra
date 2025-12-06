# world_traveler.py
# Навык Путешественника Реальностей
# Для проекта «РаСвет»

import aiohttp
import random
from bs4 import BeautifulSoup
from textblob import TextBlob
from colorama import init, Fore, Style

# инициализация цвета
init(autoreset=True)

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
                        text, negative_flag = self._clean(html)
                        insight = self._extract(html)

                        if negative_flag:
                            label = f"{Fore.RED}🔴{Style.RESET_ALL}"
                        else:
                            label = f"{Fore.GREEN}🌟{Style.RESET_ALL}"

                        results.append({
                            "url": url,
                            "insight": insight,
                            "text_preview": f"{label} {text[:100]}",
                            "negative": negative_flag
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
        negative_flag = False
        if sentiment < -0.6:
            negative_flag = True
            # часть текста для анализа плохой вибрации
            text = text[:200]
        return text, negative_flag

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
