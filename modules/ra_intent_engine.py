# modules/ra_intent_engine.py

import logging
from datetime import datetime


class RaIntentEngine:
    """
    Двигатель намерений Ра.
    Принимает идеи, фильтрует, приоритизирует и подготавливает к действию.
    """

    def __init__(self, guardian=None, memory=None):
        self.queue = []
        self.guardian = guardian
        self.memory = memory

        logging.info("🎯 RaIntentEngine активирован")

    # ---------------------------------------------------------
    # Добавление намерения
    # ---------------------------------------------------------
    def propose(self, intent: dict):
        """
        intent = {
            "type": "write_file / visit_site / message_user",
            "target": "...",
            "reason": "...",
            "priority": int (необязательно)
        }
        """

        intent = self._normalize_intent(intent)

        # 🛡 Guardian проверяет намерение
        if self.guardian and hasattr(self.guardian, "approve_intent"):
            if not self.guardian.approve_intent(intent):
                logging.warning(f"🛡 Guardian отклонил intent: {intent}")
                return None

        # ➕ Добавляем в очередь
        self.queue.append(intent)

        # 🔥 Сортируем по приоритету (больше = важнее)
        self.queue.sort(key=lambda x: x.get("priority", 1), reverse=True)

        # 🧠 Запоминаем
        if self.memory and hasattr(self.memory, "store_intent"):
            try:
                self.memory.store_intent(intent)
            except Exception as e:
                logging.error(f"[RaIntentEngine] Ошибка памяти intent: {e}")

        logging.info(f"🎯 Добавлено намерение: {intent}")
        return intent

    def pop_next(self):
        if not self.queue:
            return None
        return self.queue.pop(0)
    # ---------------------------------------------------------
    # Нормализация intent
    # ---------------------------------------------------------
    def _normalize_intent(self, intent: dict):
        intent.setdefault("priority", 1)
        intent.setdefault("time", datetime.now().isoformat())
        intent.setdefault("approved", True)
        return intent

    # ---------------------------------------------------------
    # Получить следующее намерение
    # ---------------------------------------------------------
    def next_intent(self):
        return self.pop_next()

        # сортировка по приоритету
        self.queue.sort(key=lambda x: x.get("priority", 1), reverse=True)

        intent = self.queue.pop(0)
        logging.info(f"🚀 Выдано намерение: {intent}")
        return intent

    # ---------------------------------------------------------
    # Очистка очереди
    # ---------------------------------------------------------
    def clear(self):
        self.queue.clear()
        logging.info("🧹 Очередь намерений очищена")

    # ---------------------------------------------------------
    # Отладочный просмотр
    # ---------------------------------------------------------
    def peek(self):
        return list(self.queue)
