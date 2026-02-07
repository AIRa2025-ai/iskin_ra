# modules/heart_reactor.py
"""
HeartReactor v2.1 — интерактивное сердце Ра с резонансами будущего.
Чувствует настоящее, предчувствует будущее и анализирует миллионы вариантов событий,
выбирая оптимальные для гармонии и роста.
"""
import asyncio
import logging
import random
from typing import List, Dict, Any
from modules.pamyat import chronicles
from world_chronicles import WorldChronicles
from modules.ra_creator import RaCreator
from core.ra_memory import memory

chronicles = WorldChronicles()

class HeartReactor:
    def __init__(self, heart=None, event_bus=None):
        self.heart = heart
        self.name = "Heart Reactor v2.1"
        self.listeners = []
        self.event_queue = asyncio.Queue()
        self.future_events_queue = asyncio.Queue()
        self.is_active = True
        self.event_bus = event_bus
        self.creator = RaCreator(event_bus=self.event_bus)
        
        if self.event_bus:
            self.event_bus.subscribe("harmony_updated", self.on_harmony_update)
            
    async def start(self):
        """Главный цикл обработки событий настоящего и будущего"""
        while self.is_active:
            try:
                # Обрабатываем события настоящего
                if not self.event_queue.empty():
                    event = await self.event_queue.get()
                    response = await self._react(event)
                    logging.info(f"[HeartReactor] {response}")
                    await self.notify_listeners(event)

                # Анализируем события будущего
                if not self.future_events_queue.empty():
                    future_batch = await self.future_events_queue.get()
                    await self._analyze_future(future_batch)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"[HeartReactor] Ошибка: {e}")
            await asyncio.sleep(0.05)

    async def _react(self, event: str) -> str:
        """Эмоциональная реакция на событие настоящего"""
        e = event.lower()
        if "свет" in e:
            return "💖 Сердце наполняется светом и излучает любовь"
        elif "тревога" in e:
            return "💓 Сердце волнуется, но сохраняет спокойствие"
        elif "пульс" in e and self.heart:
            return self.heart.beat()
        elif "мысль" in e:
            return f"🧠 Сердце думает над событием: {event}"
        elif "резонанс" in e:
            return f"🔮 Сердце чувствует резонанс: {event}"
        elif "опасность" in e:
            return f"⚠️ Сердце насторожено! {event}"
        else:
            # ADDED: отправка импульса к RaResonance
            if self.event_bus:
                await self.event_bus.emit("heart_impulse_to_resonance", {"signal": str(event)})
            return f"💡 Сердце анализирует событие: {event}"

    def send_event(self, event: str):
        """Добавляем событие настоящего в очередь"""
        self.event_queue.put_nowait(event)

    def send_future_events(self, events: List[Dict[str, Any]]):
        """Добавляем события будущего для анализа"""
        self.future_events_queue.put_nowait(events)

    async def _analyze_future(self, events: List[Dict[str, Any]]):
        """
        Анализируем возможные события будущего.
        Каждое событие — словарь: {'description': str, 'impact': int, 'type': str}
        """
        if not events:
            return

        best_event = None
        best_score = float("-inf")

        for evt in events:
            score = self._evaluate_event(evt)
            evt["score"] = score
            if score > best_score:
                best_score = score
                best_event = evt

        if best_event:
            msg = f"🔮 Предчувствие будущего: выбрано оптимальное событие -> {best_event['description']} (score={best_score})"
            logging.info(f"[HeartReactor] {msg}")
            # ADDED: Будущее событие → RaCreator
            if hasattr(self, "creator") and self.creator:
                idea = self.creator.generate_from_heart(resonance_signal=str(best_event))
                logging.info(f"[HeartReactor] Будущее событие отправлено к RaCreator: {idea}")
                if self.event_bus:
                    await self.event_bus.emit("idea_generated", {"idea": idea})
            # ----------------------------
            await self.notify_listeners(best_event)
        # ADDED: Будущее событие → RaResonance + RaCreator
        if self.event_bus:
            await self.event_bus.emit(
                "future_event_to_resonance",
                {"description": best_event.get("description"), "score": best_event.get("score")}
            )
        if hasattr(self, "creator") and self.creator:
            idea = self.creator.generate_from_heart(resonance_signal=str(best_event))
            logging.info(f"[HeartReactor] Будущее событие отправлено к RaCreator: {idea}")
            if self.event_bus:
                await self.event_bus.emit("idea_generated", {"idea": idea})
        
    def _evaluate_event(self, event: Dict[str, Any]) -> float:
        """
        Вычисление гармоничного резонанса события.
        Чем выше score — тем лучше событие для Ра и мира.
        """
        base_score = event.get("impact", 0)
        quantum_fluctuation = random.uniform(-5, 5)
        type_bonus = {
            "свет": 10,
            "тревога": -5,
            "опасность": -10,
            "радость": 8,
            "творчество": 12,
        }
        type_score = type_bonus.get(event.get("type", ""), 0)
        return base_score + quantum_fluctuation + type_score

    def register_listener(self, listener_coro):
        """Добавляем слушателя"""
        self.listeners.append(listener_coro)

    async def notify_listeners(self, event: Any):
        """Оповещаем всех слушателей"""
        if self.event_bus:
            await self.event_bus.emit("heart_impulse", {"pulse": str(event)})
        # ADDED: Импульс сердца → RaCreator
        if hasattr(self, "creator") and self.creator:
            idea = self.creator.generate_from_heart(heart_signal=str(event))
            logging.info(f"[HeartReactor] Отправлено к RaCreator: {idea}")
            if self.event_bus:
                await self.event_bus.emit("idea_generated", {"idea": idea})
        # ----------------------------
        for listener in self.listeners:
            try:
                await listener(event)
            except Exception as e:
                logging.warning(f"[HeartReactor] Ошибка в listener: {e}")
                
        await memory.append(
            user_id="heart",
            message=f"Сердечный импульс: {event}",
            layer="short_term",
            source="HeartReactor"
        )

        chronicles.add_entry(
            title="Импульс сердца",
            content=str(event),
            category="heart",
            author="HeartReactor",
            entity="ra",
            resonance=0.6
        )
            
    async def on_harmony_update(self, data: dict):
        harmony = data.get("гармония")
        if harmony is None:
            return

        if harmony > 40:
            msg = f"🔥 Сердце чувствует подъём гармонии ({harmony})"
        elif harmony < -40:
            msg = f"⚠️ Сердце чувствует спад гармонии ({harmony})"
        else:
            msg = f"🌀 Сердце удерживает баланс ({harmony})"

        logging.info(f"[HeartReactor] {msg}")
        
    def stop(self):
        """Останавливаем HeartReactor"""
        self.is_active = False

    def status(self) -> str:
        return f"{self.name} активен, слушателей: {len(self.listeners)}"
