# modules/future_predictor.py
import asyncio
import logging
import random
from datetime import datetime, timedelta

class FuturePredictor:
    def __init__(self, ra_context, limit_seconds=30):
        """
        ra_context — ссылка на RaSelfMaster или RaThinker
        limit_seconds — минимальный интервал между предсказаниями
        """
        self.context = ra_context
        self.prediction_history = []
        self.is_active = False
        self.logger = getattr(ra_context, "logger", logging)
        self.last_prediction_time = datetime.min
        self.limit_seconds = limit_seconds
        self.doubt_cache = set()  # для сомнений: уникальные предсказания

        # 🔗 лог рождения органа
        asyncio.create_task(self.log_birth())

    async def log_birth(self):
        """
        Логируем рождение модуля в память и HeartReactor
        """
        msg = f"🌱 Родился орган FuturePredictor в {datetime.now().isoformat()}"
        self.prediction_history.append(msg)

        if hasattr(self.context, "heart_reactor"):
            self.context.heart_reactor.send_event(f"💫 {msg}")

        if hasattr(self.context, "memory"):
            try:
                await self.context.memory.append("FuturePredictor", msg)
            except Exception as e:
                self.logger.error(f"[FuturePredictor] Не удалось сохранить память: {e}")

        self.logger.info(msg)

    async def start(self):
        self.is_active = True
        self.logger.info("🚀 FuturePredictor запущен")
        while self.is_active:
            await self.generate_prediction()
            await asyncio.sleep(5)  # частота проверки возможности предсказания

    async def stop(self):
        self.is_active = False
        self.logger.info("🛑 FuturePredictor остановлен")

    async def generate_prediction(self):
        """
        Генерация предсказания с сомнениями и ограничением частоты
        """
        now = datetime.now()
        if (now - self.last_prediction_time).total_seconds() < self.limit_seconds:
            return  # ждём лимит

        # создаем текст предсказания
        types = ["финансы", "лотерея", "глобальные события", "погода", "творчество"]
        chosen_type = random.choice(types)
        prediction_text = f"🔮 Предсказание ({chosen_type}) в {now.strftime('%H:%M:%S')}: " \
                          f"Событие {random.randint(1, 100)} вероятно произойдет."

        # сомнения: не повторять уже существующее
        if prediction_text in self.doubt_cache:
            self.logger.info(f"[FuturePredictor] Сомнение: повторное предсказание игнорируется")
            return
        self.doubt_cache.add(prediction_text)

        # сохраняем историю
        self.prediction_history.append(prediction_text)
        self.last_prediction_time = now

        # отправляем в HeartReactor
        if hasattr(self.context, "heart_reactor"):
            self.context.heart_reactor.send_event(prediction_text)

        # логируем в RaMemory
        if hasattr(self.context, "memory"):
            try:
                await self.context.memory.append("FuturePredictor", prediction_text)
            except Exception as e:
                self.logger.error(f"[FuturePredictor] Не удалось сохранить память: {e}")

        # лог в консоль/файл
        self.logger.info(prediction_text)

    def status(self):
        return {
            "active": self.is_active,
            "history_len": len(self.prediction_history),
            "last_prediction": self.prediction_history[-1] if self.prediction_history else None,
            "doubt_cache_size": len(self.doubt_cache)
        }
