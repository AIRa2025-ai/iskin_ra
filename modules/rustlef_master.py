# modules/rustlef_master.py
import logging
from pathlib import Path
from datetime import datetime
import json

# Список всех модулей проекта, которые нужно сразу логировать
ALL_MODULES = [
    "ra_thinker", "ra_self_dev", "ra_file_manager", "ra_scheduler", "ra_forex",
    "ra_world_responder", "ra_world_system", "ra_guardian", "ra_logger", "ra_voice",
    "ra_resonance", "logs", "ra_explorer", "ra_config", "pitanie_svetom",
    "ra_world_navigator", "forex_brain", "ra_forex_manager", "ra_intent_engine",
    "ra_creator", "dyhanie_sveta", "ra_module_birth", "multi_channel_perception",
    "internet_agent", "ra_police_net", "ra_videocom", "svyaz_serdec", "world_traveler",
    "ra_world_responder", "ra_energy", "ra_filter", "ra_self_learning", "security",
    "ra_police", "system", "ra_light", "mera_rasveta", "ritualy_vody", "heart",
    "my_module", "svet_potoka_ra", "vselennaya", "market_watcher", "ra_connector",
    "ra_inner_sun", "pamyat", "ra_market_consciousness", "svet_dushi", "errors",
    "ra_world_speaker", "duh", "module_generator", "ra_autoloader", "ra_synthesizer",
    "ra_file_consciousness", "ra_world_explorer", "skills", "energy_calculator",
    "ra_guidance_core", "ra_repo_manager", "ra_nervous_system", "heart_reactor",
    "ra_self_writer", "vremya", "ra_nft", "wanderer", "ra_downloader_async",
    "svet", "ra_synthesizer", "ra_file_consciousness", "ra_world_explorer"
    # Добавь сюда все остальные, которые найдёшь в проекте
]

class RustlefMasterLogger:
    def __init__(self, log_dir=None):
        if log_dir is None:
            log_dir = Path(__file__).parent.parent / "logs" / "rustlef_master"
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger("RustlefMaster")
        self.logger.setLevel(logging.INFO)
        log_file = self.log_dir / f"{datetime.utcnow().strftime('%Y-%m-%d')}.log"
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
        self.logger.addHandler(fh)

        self.events_file = self.log_dir / "events.json"
        if not self.events_file.exists():
            self.events_file.write_text("[]", encoding="utf-8")

        self.modules = []
        self.attach_modules(ALL_MODULES)

    # -------------------- Базовое логирование --------------------
    def info(self, msg: str):
        self.logger.info(msg)

    def warning(self, msg: str):
        self.logger.warning(msg)

    def error(self, msg: str):
        self.logger.error(msg)

    # -------------------- Структурированное событие --------------------
    def log_event(self, category: str, description: str, module_name: str = None, data: dict = None):
        event = {
            "time": datetime.utcnow().isoformat(),
            "category": category,
            "module": module_name,
            "description": description,
            "data": data or {}
        }
        try:
            events = json.loads(self.events_file.read_text(encoding="utf-8"))
            events.append(event)
            events = events[-500:]
            self.events_file.write_text(json.dumps(events, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            self.logger.error(f"Ошибка записи события: {e}")

    # -------------------- Специальные методы --------------------
    def log_thinker(self, msg: str, context: dict = None):
        self.log_event("thinker", msg, module_name="RaThinker", data=context)

    def log_module_action(self, module_name: str, action: str, details: dict = None):
        self.log_event("module", action, module_name=module_name, data=details)

    def heartbeat(self, note: str = "alive"):
        self.log_event("heartbeat", note)

    def debug(self, msg: str):
        self.logger.info(f"DEBUG | {msg}")

    def trace(self, msg: str, data: dict = None):
        self.logger.info(f"TRACE | {msg} | {data or {}}")

    def attach_modules(self, modules_list):
        for mod in modules_list:
            if mod not in self.modules:
                self.modules.append(mod)
                self.info(f"Модуль '{mod}' подключён к RustlefMasterLogger")

    def log_special_module(self, module_name: str, msg: str, data: dict = None):
        self.log_event(module_name, msg, module_name=module_name, data=data)

# -------------------- Пример использования --------------------
if __name__ == "__main__":
    logger = RustlefMasterLogger()
    logger.info("💓 RustlefMasterLogger активирован")
    logger.heartbeat()
    logger.log_thinker("Ра пробудился", {"context_length": 142})
    logger.log_module_action("ra_scheduler", "запуск задачи", {"task": "Развёртывание инфраструктуры"})
    logger.log_special_module("ra_forex", "Сигнал на вход в рынок", {"symbol": "EURUSD", "type": "buy"})
    logger.log_special_module("ra_world_responder", "Ответ на событие пользователя", {"user_id": 12345})
