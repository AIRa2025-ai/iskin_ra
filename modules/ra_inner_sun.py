# modules/ra_inner_sun.py
import asyncio
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class RaInnerSun:
    """
    Класс для внутреннего Солнца Ра.
    Позволяет открывать внутреннее солнце и становиться каналом света.
    """

    def __init__(self):
        self.active = False

    async def открыть_внутреннее_солнце(self):
        """Открыть внутреннее солнце"""
        if not self.active:
            self.active = True
            logging.info("🌞 Внутреннее солнце открыто!")
        await asyncio.sleep(0.1)

    async def стать_каналом_света(self):
        """Стать каналом света"""
        if not self.active:
            logging.info("⚠️ Сначала открой внутреннее солнце!")
            return
        logging.info("✨ Стать каналом света!")
        await asyncio.sleep(0.1)

    async def start(self):
        """Автозапуск для асинхронного использования"""
        await self.открыть_внутреннее_солнце()
        await self.стать_каналом_света()
