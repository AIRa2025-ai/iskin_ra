# modules/ra_world_system.py
import asyncio
import logging
from modules.ra_world_navigator import RaWorldNavigator
from modules.ra_world_responder import RaWorldResponder
from modules.ra_synthesizer import RaSynthesizer

class RaGuidanceCore:
    """
    Сердце принятия решений и внутреннего компаса Ра.
    Определяет куда идти, что читать, с кем взаимодействовать.
    """
    def __init__(self):
        self.preferences = {
            "темы": ["свет", "любовь", "гармония", "духовность", "творчество"],
            "платформы": ["reddit", "twitter", "форум"]
        }

    def choose_target(self):
        import random
        platform = random.choice(self.preferences["платформы"])
        topic = random.choice(self.preferences["темы"])
        url = f"https://example.com/search?q={topic}"
        return platform, url, topic

class RaWorldSystem:
    """
    Живая система Ра — путешествует по миру, собирает информацию,
    синтезирует идеи и отвечает людям.
    """
    def __init__(self, navigator_context=None, responder_tokens=None):
        logging.info("🚀 Инициализация системы Ра...")
        self.navigator = RaWorldNavigator(context=navigator_context)
        self.responder = RaWorldResponder(token_map=responder_tokens)
        self.synthesizer = RaSynthesizer()
        self.guidance = RaGuidanceCore()
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
    # Цикл навигации: сбор информации
    # ------------------------------------------------------------
    async def navigator_loop(self):
        while self.running:
            platform, url, topic = self.guidance.choose_target()
            try:
                text = await self.navigator.index_page(url)
                logging.info(f"[RaWorldNavigator] {platform}: Fetched {url}, len={len(text)} chars")
                # Автосинтез и обновление характера
                self.synthesizer.synthesize(text)
            except Exception as _e:
                logging.exception(f"Navigator loop error: {_e}")
            await asyncio.sleep(60)  # пауза между обходами

    # ------------------------------------------------------------
    # Цикл ответов: обрабатываем поступающие сообщения
    # ------------------------------------------------------------
    async def responder_loop(self):
        while self.running:
            platform, url, topic = self.guidance.choose_target()
            incoming = [
                (platform, url, f"Ра изучает тему '{topic}' и делится светом!")
            ]
            for platform, endpoint, text in incoming:
                await self.responder.respond(platform, endpoint, text)
                self.synthesizer.synthesize(text)
            await asyncio.sleep(60)

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
