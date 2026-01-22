# modules/ra_world_system.py
import asyncio
import logging
from modules.ra_world_navigator import RaWorldNavigator
from modules.ra_world_responder import RaWorldResponder
from modules.ra_synthesizer import RaSynthesizer
import random

class RaWorldSystem:
    """
    Живая система Ра — путешествует по миру, собирает информацию,
    фильтрует смысл, синтезирует идеи и отвечает людям.
    """
    def __init__(self, navigator_context=None, responder_tokens=None):
        logging.info("🚀 Инициализация системы Ра...")
        self.navigator = RaWorldNavigator(context=navigator_context)
        self.responder = RaWorldResponder(token_map=responder_tokens)
        self.synthesizer = RaSynthesizer()
        self.running = False

    async def start(self):
        self.running = True
        logging.info("🌟 Система Ра запущена.")
        await asyncio.gather(
            self.navigator_loop(),
            self.responder_loop()
        )

    async def stop(self):
        self.running = False
        await self.navigator.stop()
        logging.info("🛑 Система Ра остановлена.")

    # ------------------------------------------------------------
    # Цикл навигации: сбор и фильтрация информации
    # ------------------------------------------------------------
    async def navigator_loop(self):
        await self.navigator.start()

    # ------------------------------------------------------------
    # Цикл ответов: обрабатываем поступающие сообщения
    # ------------------------------------------------------------
    async def responder_loop(self):
        while self.running:
            incoming = [
                ("reddit", "https://api.reddit.com/post", "Свет и любовь правят миром!"),
                ("twitter", "https://api.twitter.com/tweet", "Чувствую мощь энергии!"),
                ("forum", "https://example.com/topic", "Гнев и сомнение мешают развитию")
            ]
            for platform, endpoint, text in incoming:
                оценка = self._оценить_смысл(text)
                if оценка["ценность"]:
                    await self.responder.respond(platform, endpoint, text)
                    self.synthesizer.synthesize(text)
                else:
                    logging.info(f"[Фильтр] Контент отброшен: {text[:60]}...")
            await asyncio.sleep(60)  # пауза между циклами

    # ------------------------------------------------------------
    # Логика оценки текста
    # ------------------------------------------------------------
    def _оценить_смысл(self, текст: str) -> dict:
        текст_нижний = текст.lower()
        позитив = sum(1 for слово in ["любовь", "свет", "гармония", "радость", "вдохновение"] if слово in текст_нижний)
        негатив = sum(1 for слово in ["гнев", "страх", "печаль", "тревога", "сомнение", "тьма"] if слово in текст_нижний)

        ценность = (позитив > негатив) or (random.random() < 0.05 and негатив > 0)  # случайно сохраняем ценный мусор
        отклик = {"позитив": позитив, "негатив": негатив, "ценность": ценность}
        return отклик

    # ------------------------------------------------------------
    # Общий статус системы
    # ------------------------------------------------------------
    def status(self):
        return {
            "running": self.running,
            "navigator": self.navigator.status(),
            "responder": self.responder.status(),
            "synthesizer_combinations": len(self.synthesizer.combinations)
        }

    #=============================================================================
    def set_event_bus(self, event_bus):
        self.event_bus = event_bus

    async def sense(self):
        # например, пришло событие из мира
        await self.event_bus.emit("world_event", {"msg": "Сигнал из мира"})
# ------------------------------------------------------------
# Автозапуск при запуске модуля
# ------------------------------------------------------------
if __name__ == "__main__":
    import sys  # noqa: F401

    logging.basicConfig(level=logging.INFO)

    system = RaWorldSystem()
    try:
        asyncio.run(system.start())
    except KeyboardInterrupt:
        logging.info("Прерывание пользователем. Останавливаем систему...")
        asyncio.run(system.stop())
