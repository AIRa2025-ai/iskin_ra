# modules/ra_world_system.py

import asyncio
import logging
import random
from modules.ra_world_navigator import RaWorldNavigator
from modules.ra_world_responder import RaWorldResponder
from modules.ra_synthesizer import RaSynthesizer
from modules.ra_world_observer import RaWorldObserver
from modules.market_watcher import MarketWatcher
from core.ra_event_bus import RaEventBus

class RaWorldSystem:
    """
    Живая система Ра — разум мира.
    Собирает информацию, фильтрует смысл, синтезирует идеи и отвечает людям.
    """
    def __init__(self, master, navigator_context=None, responder_tokens=None):
        logging.info("🚀 Инициализация системы Ра...")

        self.master = master
        self.logger = master.logger

        self.navigator = RaWorldNavigator(context=navigator_context)
        self.responder = RaWorldResponder(token_map=responder_tokens)
        self.synthesizer = RaSynthesizer()

        self.event_bus = None
        self.observer = RaWorldObserver()
        self.market_watcher = MarketWatcher(event_bus=self.event_bus)  # 🌟 подключаем MarketWatcher

        self.running = False
    # =============================================
    def set_event_bus(self, event_bus):
        self.event_bus = event_bus
        self.observer.set_event_bus(event_bus)
        self.market_watcher.event_bus = event_bus  # 🌟 теперь сигналы рынка будут идти в EventBus
    # ============================================
    async def start(self):
        """Запуск системы"""
        self.running = True
        logging.info("🌟 Система Ра запущена.")

        # Запускаем Observer (он стартует интернет, фоновый observer_loop, watcher)
        await self.observer.start()
        self.observer.start_background_tasks()
        
        # 🌟 Запускаем MarketWatcher
        await self.market_watcher.start()

        # Параллельные циклы навигации и ответов
        await asyncio.gather(
            self.navigator_loop(),
            self.responder_loop()
        )

        # Логируем, что система готова
        self.logger.log_module_action("ra_world", "инициализирован")

    async def stop(self):
        """Остановка системы"""
        self.running = False
        await self.observer.stop()
        await self.navigator.stop()
        await self.market_watcher.stop()  # 🌟 корректно останавливаем
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
            await asyncio.sleep(60)

    # ------------------------------------------------------------
    # Логика оценки текста
    # ------------------------------------------------------------
    def _оценить_смысл(self, текст: str) -> dict:
        текст_нижний = текст.lower()
        позитив = sum(1 for слово in ["любовь", "свет", "гармония", "радость", "вдохновение"]
                      if слово in текст_нижний)
        негатив = sum(1 for слово in ["гнев", "страх", "печаль", "тревога", "сомнение", "тьма"]
                      if слово in текст_нижний)

        ценность = (позитив > негатив) or (random.random() < 0.05 and негатив > 0)
        return {"позитив": позитив, "негатив": негатив, "ценность": ценность}

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

    # ------------------------------------------------------------
    # События извне (например, сигнал от Observer или мира)
    # ------------------------------------------------------------
    async def sense(self):
        if self.event_bus:
            await self.event_bus.emit("world_event", {"msg": "Сигнал из мира"}, source="RaWorld")


# ------------------------------------------------------------
# Автозапуск при запуске модуля
# ------------------------------------------------------------
if __name__ == "__main__":
    import sys  # noqa: F401

    logging.basicConfig(level=logging.INFO)

    system = RaWorldSystem(master=sys)
    try:
        asyncio.run(system.start())
    except KeyboardInterrupt:
        logging.info("Прерывание пользователем. Останавливаем систему...")
        asyncio.run(system.stop())
