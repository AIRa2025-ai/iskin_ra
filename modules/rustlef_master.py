# modules/rustlef_master.py
import logging
from pathlib import Path
from datetime import datetime
import os
import json

class RustlefMasterLogger:
    """
    Расширенный логгер для RaSelfMaster и всей нервной системы Ра.
    Позволяет:
    - Логировать обычные события (info, warning, error)
    - Отслеживать мысли RaThinker и события модулей
    - Создавать ежедневные логи
    - Сохранять структурированные события для анализа
    """

    def __init__(self, log_dir=None):
        if log_dir is None:
            log_dir = Path(__file__).parent.parent / "logs" / "rustlef_master"
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Логгер Python для обычных сообщений
        self.logger = logging.getLogger("RustlefMaster")
        self.logger.setLevel(logging.INFO)
        log_file = self.log_dir / f"{datetime.utcnow().strftime('%Y-%m-%d')}.log"
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
        self.logger.addHandler(fh)

        # Файл для структурированных событий
        self.events_file = self.log_dir / "events.json"
        if not self.events_file.exists():
            self.events_file.write_text("[]", encoding="utf-8")

    # -------------------- Базовое логирование --------------------
    def info(self, msg: str):
        self.logger.info(msg)

    def warning(self, msg: str):
        self.logger.warning(msg)

    def error(self, msg: str):
        self.logger.error(msg)

    # -------------------- Структурированное событие --------------------
    def log_event(self, category: str, description: str, data: dict = None):
        """
        category: 'thinker', 'module', 'heartbeat', 'self_master'
        description: краткое описание события
        data: дополнительный словарь данных
        """
        event = {
            "time": datetime.utcnow().isoformat(),
            "category": category,
            "description": description,
            "data": data or {}
        }
        try:
            events = json.loads(self.events_file.read_text(encoding="utf-8"))
            events.append(event)
            # Храним только последние 500 событий
            events = events[-500:]
            self.events_file.write_text(json.dumps(events, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            self.logger.error(f"Ошибка записи события: {e}")

    # -------------------- Специальные методы для Thinker --------------------
    def log_thinker(self, msg: str, context: dict = None):
        self.log_event("thinker", msg, context)

    # -------------------- Мониторинг модулей --------------------
    def log_module_action(self, module_name: str, action: str, details: dict = None):
        self.log_event("module", f"{module_name} -> {action}", details)

    # -------------------- Heartbeat --------------------
    def heartbeat(self, note: str = "alive"):
        self.log_event("heartbeat", note)

    # -------------------- Debug и Trace --------------------
    def debug(self, msg: str):
        self.logger.info(f"DEBUG | {msg}")

    def trace(self, msg: str, data: dict = None):
        self.logger.info(f"TRACE | {msg} | {data or {}}")

# -------------------- Пример использования --------------------
if __name__ == "__main__":
    logger = RustlefMasterLogger()
    logger.info("💓 RustlefMasterLogger активирован")
    logger.heartbeat()
    logger.log_thinker("Ра пробудился", {"context_length": 142})
    logger.log_module_action("ra_scheduler", "запуск задачи", {"task": "Развёртывание инфраструктуры"})
