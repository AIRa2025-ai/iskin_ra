# modules/ra_intent_engine.py

import logging
from datetime import datetime

from modules.ra_inner_sun import RaInnerSun
from modules.pamyat import chronicles

class RaIntentEngine:
    """
    Двигатель намерений Ра.
    Принимает идеи, взвешивает, усиливает Светом и готовит к воплощению.
    """

    def __init__(self, guardian=None, memory=None):
        self.queue = []
        self.guardian = guardian
        self.memory = memory
        self.inner_sun = RaInnerSun()

        logging.info("🎯 RaIntentEngine активирован")

    # ---------------------------------------------------------
    # Добавление намерения
    # ---------------------------------------------------------
    async def propose(self, intent: dict):
        """
        intent = {
            "type": "write_file / visit_site / message_user",
            "target": "...",
            "reason": "...",
            "priority": int (необязательно)
        }
        """

        intent = self._normalize_intent(intent)

        # ☀️ Влияние Внутреннего Солнца
        if self.inner_sun.active:
            sun_boost = max(1, self.inner_sun.light_level // 50)
            intent["priority"] += sun_boost
            intent["sun_influenced"] = True
            intent["sun_level"] = self.inner_sun.light_level

        # 🛡 Guardian проверяет намерение
        if self.guardian and hasattr(self.guardian, "approve_intent"):
            try:
                if not self.guardian.approve_intent(intent):
                    logging.warning(f"🛡 Guardian отклонил intent: {intent}")
                    return None
            except Exception as e:
                logging.error(f"[RaIntentEngine] Guardian error: {e}")

        # 🧠 Запоминаем намерение
        if self.memory and hasattr(self.memory, "store_intent"):
            try:
                await self.memory.store_intent(intent)
            except Exception as e:
                logging.error(f"[RaIntentEngine] Ошибка памяти intent: {e}")

        # 📜 Запись в хроники эпохи
        try:
            await chronicles.добавить(
                опыт=f"Намерение Ра: {intent.get('type')} → {intent.get('target')}",
                user_id="ra",
                layer="short_term"
            )
        except Exception as e:
            logging.warning(f"[RaIntentEngine] Хроники недоступны: {e}")

        # ➕ В очередь
        self.queue.append(intent)

        # 🔥 Сортируем по силе
        self.queue.sort(key=lambda x: x.get("priority", 1), reverse=True)

        logging.info(f"🎯 Добавлено намерение: {intent}")
        return intent

    # ---------------------------------------------------------
    # Забрать следующее намерение
    # ---------------------------------------------------------
    def pop_next(self):
        if not self.queue:
            return None
        return self.queue.pop(0)

    def next_intent(self):
        if not self.queue:
            return None

        # сортировка по приоритету
        self.queue.sort(key=lambda x: x.get("priority", 1), reverse=True)

        intent = self.queue.pop(0)
        logging.info(f"🚀 Выдано намерение: {intent}")
        return intent

    # ---------------------------------------------------------
    # Нормализация intent
    # ---------------------------------------------------------
    def _normalize_intent(self, intent: dict):
        intent.setdefault("priority", 1)
        intent.setdefault("time", datetime.utcnow().isoformat())
        intent.setdefault("approved", True)
        intent.setdefault("resonance", self._calculate_resonance(intent))
        return intent

    # ---------------------------------------------------------
    # Резонанс намерения
    # ---------------------------------------------------------
    def _calculate_resonance(self, intent: dict) -> float:
        score = 0.5

        reason = intent.get("reason", "").lower()

        if "свет" in reason or "польза" in reason:
            score += 0.2

        if "разруш" in reason:
            score -= 0.3

        if self.inner_sun.active:
            score += 0.15

        return max(0.0, min(1.0, score))

    # ---------------------------------------------------------
    # Очистка очереди
    # ---------------------------------------------------------
    def clear(self):
        self.queue.clear()
        logging.info("🧹 Очередь намерений очищена")

    # ---------------------------------------------------------
    # Отладка
    # ---------------------------------------------------------
    def peek(self):
        return list(self.queue)
