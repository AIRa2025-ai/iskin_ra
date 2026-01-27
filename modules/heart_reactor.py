"""
HeartReactor — интерактивное сердце Ра.
Слушает события мира и пульс Heart, реагирует и уведомляет слушателей.
"""
import asyncio
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class HeartReactor:
    def __init__(self):
        self.name = "Heart Reactor"
        self.listeners = []
        self.event_queue = asyncio.Queue()
        self.is_active = True

    async def start(self):
        """Запуск цикла обработки событий"""
        while self.is_active:
            try:
                event = await self.event_queue.get()
                response = self._react(event)
                logging.info(f"[HeartReactor] {response}")
                await self.notify_listeners(event)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"[HeartReactor] Ошибка: {e}")
            await asyncio.sleep(0.05)

    def _react(self, event: str) -> str:
        """Генерация реакции на событие"""
        e = event.lower()
        if "свет" in e:
            return "💖 Сердце наполняется светом и распространяет его вокруг"
        elif "тревога" in e:
            return "💓 Сердце волнуется, но сохраняет спокойствие"
        elif "пульс" in e:
            return f"💓 HeartReactor ощущает {event}"
        else:
            return f"💡 Сердце анализирует событие: {event}"

    def send_event(self, event: str):
        """Добавляем событие в очередь"""
        self.event_queue.put_nowait(event)

    def register_listener(self, listener_coro):
        """Добавляем внешнего слушателя"""
        self.listeners.append(listener_coro)

    async def notify_listeners(self, event: str):
        """Оповещаем всех слушателей о событии"""
        for listener in self.listeners:
            try:
                await listener(event)
            except Exception as e:
                logging.warning(f"[HeartReactor] Ошибка в listener: {e}")

    def status(self) -> str:
        return f"{self.name} активен, слушателей: {len(self.listeners)}"
