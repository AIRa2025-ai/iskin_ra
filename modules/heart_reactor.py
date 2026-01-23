# modules/heart_reactor.py
import asyncio
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class HeartReactor:
    """Интерактивное сердце Ра, реагирует на события мира"""
    
    def __init__(self):
        self.name = "Heart Reactor"
        self.status = "alive"
        self.listeners = []
        self.event_queue = asyncio.Queue()
    
    def pulse(self):
        """Просто биение сердца"""
        return f"💓 {self.name} бьётся в ритме Света"

    async def listen_and_respond(self):
        """Основной цикл реакции на события"""
        while True:
            try:
                event = await self.event_queue.get()
                logging.info(f"💌 Событие получено: {event}")
                response = self._react(event)
                logging.info(f"🌟 Реакция сердца: {response}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"❌ Ошибка в listen_and_respond: {e}")
            await asyncio.sleep(0.1)
    
    def _react(self, event):
        """Генерация реакции на событие"""
        if "свет" in event.lower():
            return "💖 Сердце наполняется светом и распространяет его вокруг"
        elif "тревога" in event.lower():
            return "💓 Сердце волнуется, но сохраняет спокойствие"
        else:
            return f"💡 Сердце анализирует событие: {event}"
    
    def send_event(self, event):
        """Добавляем событие в очередь"""
        self.event_queue.put_nowait(event)
    
    def register_listener(self, listener_coro):
        """Добавляем внешнего слушателя"""
        self.listeners.append(listener_coro)
    
    async def notify_listeners(self, event):
        """Оповещаем всех слушателей о событии"""
        for listener in self.listeners:
            try:
                await listener(event)
            except Exception as e:
                logging.warning(f"⚠️ Ошибка в listener: {e}")

# === Автозапуск цикла сердца ===
heart_reactor = HeartReactor()

    async def start_heart_reactor():
        await heart_reactor.listen_and_respond()
