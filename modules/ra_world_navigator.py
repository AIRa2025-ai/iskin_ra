import asyncio
import logging
from modules.ra_explorer import RaExplorer

class RaWorldNavigator:
    """
    Ра-Навигатор — путешествует по интернету, исследует, запоминает.
    """

    def __init__(self):
        self.explorer = RaExplorer()

    async def travel(self, urls: list[str]):
        logging.info("[RaWorldNavigator] Начинаю путешествие по мирам 🌐")
        for url in urls:
            result = await self.explorer.explore_url(url)
            if "error" in result:
                logging.warning(f"[RaWorldNavigator] Пропущен: {url}")
            else:
                logging.info(f"[RaWorldNavigator] Исследовано: {url}")
        logging.info("[RaWorldNavigator] 🌞 Путешествие завершено")
