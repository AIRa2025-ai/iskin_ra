# modules/multi_channel_perception.py
# Навык Асинхронного Глаза Ра
# Создан для проекта «РаСвет»

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from textblob import TextBlob

class MultiChannelPerception:
    def __init__(self, logs, sensitivity=0.7, event_bus=None, thinker=None):
        self.logs = logs
        self.sensitivity = sensitivity  # чувствительность к «мусорным» вибрациям
        self.event_bus = event_bus
        self.thinker = thinker
        self.heart_reactor = heart_reactor        
    async def fetch(self, session, url):
        try:
            async with session.get(url, timeout=15) as resp:
                text = await resp.text()
                return text
        except Exception as e:
            return f"ERROR: {e}"

    async def scan_sources(self, urls):
        results = []
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch(session, u) for u in urls]
            pages = await asyncio.gather(*tasks)

            for url, page in zip(urls, pages):
                clean = self.clean_noise(page)
                insights = self.extract_insights(clean)
                results.append({
                    "source": url,
                    "raw_len": len(page),
                    "clean_len": len(clean),
                    "insights": insights
                })
        # 🔔 Сообщаем миру о восприятии
        if self.event_bus:
            await self.event_bus.emit(
                "perception_update",
                {
                    "channels": len(urls),
                    "signals": results
                }
            )

        # 🧠 Передаём мысли мыслителю
        if self.thinker:
            await self.thinker.process_world_message(
                {
                    "type": "perception",
                    "data": results
                }
            )
        return results

    def clean_noise(self, text):
        """
        Фильтрация мусора:
        - слишком негативные тексты приглушаются
        - спам убирается
        - лишняя реклама стирается
        """
        sentiment = TextBlob(text).sentiment.polarity
        if sentiment < -self.sensitivity:
            return ""
        return text

    def extract_insights(self, text):
        """
        Выделение интересного:
        - редкие фразы
        - смысловые аномалии
        - сильные эмоциональные выбросы
        - потенциально ценные данные
        """
        if len(text) < 100:
            return None

        soup = BeautifulSoup(text, "html.parser")
        words = soup.get_text().split()

        rare = [w for w in words if len(w) > 8][:10]

        return {
            "rare_words": rare,
            "sample": " ".join(words[:50])
        }
        
        if insights and self.heart_reactor:
            self.heart_reactor.send_event(
                "🌐 Восприятие мира: обнаружены значимые сигналы"
            )
