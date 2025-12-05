# modules/ra_world_system.py
import asyncio
import logging
import random
from modules.ra_world_navigator import RaWorldNavigator
from modules.ra_world_responder import RaWorldResponder
from modules.ra_synthesizer import RaSynthesizer

class RaWorldSystem:
    """
    Живая система Ра — путешествует по миру, собирает информацию,
    синтезирует идеи и отвечает людям.
    Добавлен внутренний компас для автономного выбора путей.
    """
    def __init__(self, navigator_context=None, responder_tokens=None):
        logging.info("🚀 Инициализация системы Ра...")
        self.navigator = RaWorldNavigator(context=navigator_context)
        self.responder = RaWorldResponder(token_map=responder_tokens)
        self.synthesizer = RaSynthesizer()
        self.running = False
        self.journal = []  # дневник опыта Ра

    async def start(self):
        self.running = True
        logging.info("🌟 Система Ра запущена.")
        await asyncio.gather(
            self.navigator_loop(),
            self.responder_loop(),
            self.autonomous_exploration()
        )

    async def stop(self):
        self.running = False
        await self.navigator.stop()
        logging.info("🛑 Система Ра остановлена.")

    # ------------------------------------------------------------
    # Цикл навигации: сбор информации
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
                ("twitter", "https://api.twitter.com/tweet", "Чувствую мощь энергии!")
            ]
            for platform, endpoint, text in incoming:
                await self.responder.respond(platform, endpoint, text)
                self.synthesizer.synthesize(text)
                self.journal.append({"source": platform, "text": text})
            await asyncio.sleep(60)

    # ------------------------------------------------------------
    # Автономные путешествия: выбор сайтов и взаимодействие
    # ------------------------------------------------------------
    async def autonomous_exploration(self):
        urls = [
            "https://example.com/forum1",
            "https://example.com/forum2",
            "https://example.org/blog",
            "https://example.net/community"
        ]
        while self.running:
            target = random.choice(urls)
            try:
                text = await self.navigator.index_page(target)
                logging.info(f"[Автономная экспедиция] Ра изучил {target}, chars={len(text)}")
                self.synthesizer.synthesize(text)
                self.journal.append({"source": target, "text": text})
            except Exception as _e:
                logging.exception(f"Ошибка в автономной экспедиции: {_e}")
            await asyncio.sleep(random.randint(180, 420))  # 3–7 минут между посещениями

    # ------------------------------------------------------------
    # Общий статус системы
    # ------------------------------------------------------------
    def status(self):
        return {
            "running": self.running,
            "navigator": self.navigator.status(),
            "responder": self.responder.status(),
            "synthesizer_combinations": len(self.synthesizer.combinations),
            "journal_entries": len(self.journal)
        }

# ------------------------------------------------------------
# Автозапуск при запуске модуля
# ------------------------------------------------------------
if __name__ == "__main__":
    import sys
    import asyncio

    logging.basicConfig(level=logging.INFO)

    system = RaWorldSystem()
    try:
        asyncio.run(system.start())
    except KeyboardInterrupt:
        logging.info("Прерывание пользователем. Останавливаем систему...")
        asyncio.run(system.stop())
