# modules/future_predictor.py
import asyncio
import logging
import random
from datetime import datetime

class FuturePredictor:
    def __init__(self, ra_context, limit_seconds=60):
        """
        ra_context — ссылка на RaSelfMaster или RaThinker
        limit_seconds — минимальный интервал между предсказаниями
        """
        self.context = ra_context
        self.prediction_history = []
        self.is_active = False
        self.last_prediction_time = datetime.min
        self.limit_seconds = limit_seconds
        self.doubt_cache = set()
        self.prediction_queue = asyncio.Queue()

        # 🔗 Подписка на события мира
        if hasattr(self.context, "event_bus"):
            self.context.event_bus.subscribe("world_message", self.on_world_event)

        # Лог рождения органа
        asyncio.create_task(self.log_birth())
        asyncio.create_task(self.process_queue())

    # -------------------------------
    # Жизнь и очередь
    # -------------------------------
    async def log_birth(self):
        msg = f"🌱 Родился орган FuturePredictor в {datetime.now().isoformat()}"
        self.prediction_history.append(msg)
        if hasattr(self.context, "heart_reactor"):
            self.context.heart_reactor.send_event(f"💫 {msg}")
        if hasattr(self.context, "memory"):
            try:
                await self.context.memory.append("FuturePredictor", msg)
            except Exception as e:
                logging.error(f"[FuturePredictor] Не удалось сохранить память: {e}")
        logging.info(msg)

    async def process_queue(self):
        while True:
            prediction_task = await self.prediction_queue.get()
            await prediction_task
            await asyncio.sleep(0.1)
    # -------------------------------
    # Умный таймер синтеза (глубокий вдох/выдох)
    # -------------------------------
    async def start_hybrid_timer(self, interval_seconds=3600):
        """
        interval_seconds — интервал, через который создаётся синтезированное предсказание
        """
        while self.is_active:
            try:
                # Генерируем синтезированное предсказание
                hybrid_prediction = await self._hybrid_prediction()
                hybrid_prediction = self._emotional_tint(hybrid_prediction)
            
                # Проверяем, не повторяется ли оно
                if not self._is_redundant(hybrid_prediction):
                    self.prediction_history.append(hybrid_prediction)
                    self.doubt_cache.add(hybrid_prediction)
                    self.last_prediction_time = datetime.now()
                
                    # Отправляем в реактор сердца и в память
                    if hasattr(self.context, "heart_reactor"):
                        self.context.heart_reactor.send_event(hybrid_prediction)
                    if hasattr(self.context, "memory"):
                        try:
                            await self.context.memory.append("FuturePredictor", hybrid_prediction, source="hybrid_timer")
                        except Exception as e:
                            logging.error(f"[FuturePredictor] Не удалось сохранить память: {e}")
                
                    logging.info(f"🌟 [Глубокий вдох] {hybrid_prediction}")
            except Exception as e:
                logging.error(f"[FuturePredictor] Ошибка в таймере синтеза: {e}")

            await asyncio.sleep(interval_seconds)
            
    async def start(self):
        self.is_active = True
        logging.info("🚀 FuturePredictor запущен")
        while self.is_active:
            await self.generate_prediction()
            await asyncio.sleep(5)
        # Запуск таймера синтеза
        asyncio.create_task(self.start_hybrid_timer(interval_seconds=3600))  # раз в час
    
        while self.is_active:
            await self.generate_prediction()
            await asyncio.sleep(5)
            
    async def stop(self):
        self.is_active = False
        logging.info("🛑 FuturePredictor остановлен")

    # -------------------------------
    # Основная генерация предсказаний
    # -------------------------------
    async def generate_prediction(self):
        now = datetime.now()
        if (now - self.last_prediction_time).total_seconds() < self.limit_seconds:
            return

        types = ["финансы", "лотерея", "глобальные события", "погода", "творчество"]
        chosen_type = random.choice(types)
        prediction_text = f"🔮 Предсказание ({chosen_type}) в {now.strftime('%H:%M:%S')}: событие {random.randint(1,100)} вероятно произойдет."

        if self._is_redundant(prediction_text) or prediction_text in self.doubt_cache:
            return

        prediction_text = self._emotional_tint(prediction_text)
        self.doubt_cache.add(prediction_text)
        self.prediction_history.append(prediction_text)
        self.last_prediction_time = now

        if hasattr(self.context, "heart_reactor"):
            self.context.heart_reactor.send_event(prediction_text)
        if hasattr(self.context, "memory"):
            try:
                await self.context.memory.append("FuturePredictor", prediction_text)
            except Exception as e:
                logging.error(f"[FuturePredictor] Не удалось сохранить память: {e}")
        logging.info(prediction_text)

    # -------------------------------
    # Предсказания по запросу
    # -------------------------------
    async def predict_on_demand(self, source_name="user_request", category=None):
        now = datetime.now()
        if (now - self.last_prediction_time).total_seconds() < self.limit_seconds:
            return None

        types = ["астрология", "лотерея", "валюты", "глобальные события", "естественные явления"]
        chosen_type = category if category in types else random.choice(types)

        if chosen_type == "астрология":
            prediction_text = await self._astro_prediction()
        elif chosen_type == "лотерея":
            prediction_text = await self._lottery_prediction()
        elif chosen_type == "валюты":
            prediction_text = await self._forex_prediction()
        elif chosen_type == "естественные явления":
            prediction_text = await self._natural_event_prediction()
        else:
            prediction_text = await self._global_event_prediction()

        if self._is_redundant(prediction_text) or prediction_text in self.doubt_cache:
            return None

        prediction_text = self._emotional_tint(prediction_text)
        self.doubt_cache.add(prediction_text)
        self.prediction_history.append(prediction_text)
        self.last_prediction_time = now

        if hasattr(self.context, "heart_reactor"):
            self.context.heart_reactor.send_event(prediction_text)
        if hasattr(self.context, "memory"):
            try:
                await self.context.memory.append("FuturePredictor", prediction_text, source=source_name)
            except Exception as e:
                logging.error(f"[FuturePredictor] Не удалось сохранить память: {e}")

        logging.info(prediction_text)
        return prediction_text

    # -------------------------------
    # Реакция на события мира
    # -------------------------------
    async def on_world_event(self, message):
        category = None
        msg_lower = message.lower()
        if "валюта" in msg_lower:
            category = "валюты"
        elif "погода" in msg_lower:
            category = "естественные явления"
        elif "лотерея" in msg_lower:
            category = "лотерея"
        else:
            category = "глобальные события"

        await self.prediction_queue.put(self.predict_on_demand(source_name="world_event", category=category))

    # -------------------------------
    # Виды предсказаний
    # -------------------------------
    async def _astro_prediction(self):
        events = ["важная встреча", "непредвиденные трудности", "успешный проект", "финансовая удача"]
        planet = random.choice(["Солнце", "Луна", "Марс", "Венера", "Юпитер", "Сатурн"])
        event = random.choice(events)
        return f"🔮 Астрология: {planet} влияет на ваши события — возможен {event}."

    async def _lottery_prediction(self):
        numbers = [random.randint(1, 49) for _ in range(6)]
        return f"🎰 Лотерея: числа на джекпот — {numbers}"

    async def _forex_prediction(self):
        advice = ["покупка", "продажа", "держать", "наблюдать"]
        pair = random.choice(["EUR/USD", "USD/JPY", "GBP/USD", "BTC/USD"])
        action = random.choice(advice)
        return f"💹 Форекс: {pair} — рекомендуемое действие: {action}"

    async def _global_event_prediction(self):
        events = ["экономический рост", "политическая нестабильность", "технологический прорыв", "экологическая катастрофа"]
        region = random.choice(["Европа", "Азия", "Америка", "Африка"])
        event = random.choice(events)
        return f"🌐 Глобальные события: {region} ожидает {event}."

    async def _natural_event_prediction(self):
        events = [
            "магнитная буря на Солнце",
            "землетрясение малой силы",
            "цунами в Тихом океане",
            "буря на экваториальной зоне"
        ]
        locations = ["Азия", "Европа", "Северная Америка", "Южная Америка"]
        event = random.choice(events)
        location = random.choice(locations)
        return f"🌪 Естественные явления: {location} ожидается {event}."

    async def _hybrid_prediction(self):
        p1 = await self._astro_prediction()
        p2 = await self._forex_prediction()
        return f"🔗 Синтез: {p1} | {p2}"

    # -------------------------------
    # Вспомогательные функции
    # -------------------------------
    def _emotional_tint(self, text):
        if any(word in text for word in ["катастрофа", "буря", "политическая нестабильность"]):
            return f"⚠️ {text}"
        elif any(word in text for word in ["успешный проект", "финансовая удача"]):
            return f"✨ {text}"
        return text

    def _is_redundant(self, text):
        return any(text in old for old in self.prediction_history[-10:])  # последние 10

    # -------------------------------
    # Статус органа
    # -------------------------------
    def status(self):
        return {
            "active": self.is_active,
            "history_len": len(self.prediction_history),
            "last_prediction": self.prediction_history[-1] if self.prediction_history else None,
            "doubt_cache_size": len(self.doubt_cache)
        }
