# core/rustlef_master_logger.py
import logging
from pathlib import Path
from datetime import datetime
import json
from typing import Callable, Dict, List, Any


# ============================================================
# 🔔 RaEvent — универсальное событие нервной системы
# ============================================================

class RaEvent:
    def __init__(self, category: str, description: str, module: str = None, data: dict = None):
        self.time = datetime.utcnow().isoformat()
        self.category = category
        self.module = module
        self.description = description
        self.data = data or {}

    def to_dict(self):
        return {
            "time": self.time,
            "category": self.category,
            "module": self.module,
            "description": self.description,
            "data": self.data
        }


# ============================================================
# 🔄 EventBus — шина событий Ра
# ============================================================

class EventBus:
    def __init__(self):
        self.subscribers: Dict[str, List[Callable[[RaEvent], None]]] = {}

    def subscribe(self, category: str, callback: Callable[[RaEvent], None]):
        if category not in self.subscribers:
            self.subscribers[category] = []
        self.subscribers[category].append(callback)

    def emit(self, event: RaEvent):
        # отправка по конкретной категории
        for cb in self.subscribers.get(event.category, []):
            try:
                cb(event)
            except Exception as e:
                print(f"[EventBus] Ошибка обработчика {cb}: {e}")

        # отправка подписчикам на "*"
        for cb in self.subscribers.get("*", []):
            try:
                cb(event)
            except Exception as e:
                print(f"[EventBus] Ошибка обработчика *: {e}")


# ============================================================
# 🧠 RustlefMasterLogger v2 — сердце нервной системы Ра
# ============================================================

class RustlefMasterLogger:
    def __init__(self, log_dir=None):
        if log_dir is None:
            log_dir = Path(__file__).parent.parent / "logs" / "rustlef_master"

        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # логгер файловый
        self.logger = logging.getLogger("RustlefMaster")
        self.logger.setLevel(logging.INFO)

        log_file = self.log_dir / f"{datetime.utcnow().strftime('%Y-%m-%d')}.log"
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
        self.logger.addHandler(fh)

        # события
        self.events_file = self.log_dir / "events.json"
        if not self.events_file.exists():
            self.events_file.write_text("[]", encoding="utf-8")

        # EventBus
        self.bus = EventBus()

        # зарегистрированные модули
        self.modules = set()

        self.info("💓 RustlefMasterLogger v2 активирован")

    # ========================================================
    # 📦 Работа с модулями
    # ========================================================

    def attach_module(self, module_name: str):
        if module_name not in self.modules:
            self.modules.add(module_name)
            self.log_module_action(module_name, "подключён к нервной системе")

    # ========================================================
    # 🧾 Базовое логирование
    # ========================================================

    def info(self, msg: str):
        self.logger.info(msg)

    def warning(self, msg: str):
        self.logger.warning(msg)

    def error(self, msg: str):
        self.logger.error(msg)

    def debug(self, msg: str):
        self.logger.info(f"DEBUG | {msg}")

    # ========================================================
    # 📜 Запись событий
    # ========================================================

    def emit_event(self, event: RaEvent):
        try:
            events = json.loads(self.events_file.read_text(encoding="utf-8"))
            events.append(event.to_dict())
            events = events[-500:]
            self.events_file.write_text(json.dumps(events, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            self.logger.error(f"[RustlefMasterLogger] Ошибка записи события: {e}")

        # передаём событие в шину
        self.bus.emit(event)

    def log_event(self, category: str, description: str, module: str = None, data: dict = None):
        event = RaEvent(category, description, module, data)
        self.emit_event(event)

    # ========================================================
    # 🧠 Специализированные категории
    # ========================================================

    def log_thinker(self, msg: str, context: dict = None):
        self.log_event("thinker", msg, module="RaThinker", data=context)

    def log_module_action(self, module_name: str, action: str, details: dict = None):
        self.log_event("module", action, module=module_name, data=details)

    def heartbeat(self, note: str = "alive"):
        self.log_event("heartbeat", note, module="system")

    def log_error(self, msg: str, module: str = None, data: dict = None):
        self.log_event("error", msg, module=module, data=data)

    # ========================================================
    # 🧬 Шаблоны для ключевых модулей
    # ========================================================

    # ra_forex
    def forex_signal(self, symbol: str, signal_type: str, data: dict = None):
        self.log_event("market", f"Сигнал {signal_type}", module="ra_forex", data={"symbol": symbol, **(data or {})})

    # ra_world_responder
    def world_response(self, user_id: int, text: str):
        self.log_event("world", "Ответ пользователю", module="ra_world_responder", data={"user_id": user_id, "text": text})

    # ra_energy
    def energy_state(self, level: float, note: str = None):
        self.log_event("energy", "Состояние энергии", module="ra_energy", data={"level": level, "note": note})

    # ra_inner_sun
    def inner_sun(self, phase: str, data: dict = None):
        self.log_event("inner_sun", "Фаза внутреннего солнца", module="ra_inner_sun", data={"phase": phase, **(data or {})})

    # ra_scheduler
    def scheduler_task(self, task_name: str, action: str):
        self.log_event("scheduler", action, module="ra_scheduler", data={"task": task_name})

    # ========================================================
    # 📡 Подписки на события
    # ========================================================

    def on(self, category: str, callback: Callable[[RaEvent], None]):
        self.bus.subscribe(category, callback)

    # ========================================================
    # 🔍 Получение истории
    # ========================================================

    def get_last_events(self, limit=50):
        try:
            events = json.loads(self.events_file.read_text(encoding="utf-8"))
            return events[-limit:]
        except Exception:
            return []


# ============================================================
# 🧪 Тестирование вручную
# ============================================================

if __name__ == "__main__":
    logger = RustlefMasterLogger()

    logger.attach_module("ra_scheduler")
    logger.attach_module("ra_forex")
    logger.attach_module("ra_world_responder")

    logger.heartbeat()
    logger.log_thinker("Ра пробудился", {"context": 142})
    logger.scheduler_task("Развёртывание инфраструктуры", "запущена")
    logger.forex_signal("EURUSD", "buy", {"confidence": 0.83})
    logger.world_response(12345, "Приветствую, брат")
    logger.energy_state(0.91, "Высокая активность")
    logger.inner_sun("восход", {"brightness": "high"})
