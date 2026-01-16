# modules/ra_autoloader.py
import importlib
import json
import logging
import asyncio
from pathlib import Path
from types import ModuleType
from typing import Dict, List

CORE_FILES = {"ra_self_master", "ra_bot_gpt"}
FORBIDDEN_PREFIXES = ("run_", "__")

ACTIVE_DEFAULT = [
    "ra_thinker",
    "ra_self_dev",
    "ra_file_manager",
]

class RaAutoloader:
    def __init__(self, manifest_path="data/ra_manifest.json"):
        self.manifest_path = Path(manifest_path)
        self.modules: Dict[str, ModuleType] = {}
        self.tasks: Dict[str, asyncio.Task] = {}

    # ---------- manifest ----------

    def load_manifest(self) -> List[str]:
        if not self.manifest_path.exists():
            logging.warning("[RaAutoloader] Манифест не найден — используем ACTIVE_DEFAULT")
            return ACTIVE_DEFAULT

        try:
            manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            modules = manifest.get("active_modules", [])
            return modules or ACTIVE_DEFAULT
        except Exception as e:
            logging.error(f"[RaAutoloader] Ошибка чтения манифеста: {e}")
            return ACTIVE_DEFAULT

    # ---------- filtering ----------

    def _is_allowed(self, name: str) -> bool:
        if name in CORE_FILES:
            return False
        if name.startswith(FORBIDDEN_PREFIXES):
            return False
        return True

    # ---------- loading ----------

    def activate_modules(self) -> Dict[str, ModuleType]:
        module_names = self.load_manifest()

        for name in module_names:
            if not self._is_allowed(name):
                logging.info(f"[RaAutoloader] Пропущен модуль: {name}")
                continue

            try:
                module = importlib.import_module(f"modules.{name}")
                self.modules[name] = module
                logging.info(f"[RaAutoloader] Модуль активирован: {name}")
            except Exception as e:
                logging.error(f"[RaAutoloader] Ошибка загрузки {name}: {e}")

        return self.modules

    # ---------- async lifecycle ----------

    async def start_async_modules(self):
        for name, module in self.modules.items():
            start_fn = getattr(module, "start", None)
            if start_fn and asyncio.iscoroutinefunction(start_fn):
                self.tasks[name] = asyncio.create_task(start_fn())
                logging.info(f"[RaAutoloader] Async модуль запущен: {name}")

    async def stop_async_modules(self):
        for task in self.tasks.values():
            task.cancel()
        await asyncio.gather(*self.tasks.values(), return_exceptions=True)
        self.tasks.clear()
        logging.info("[RaAutoloader] Все async модули остановлены")

    # ---------- status ----------

    def status(self):
        return {
            "modules": list(self.modules.keys()),
            "async": list(self.tasks.keys()),
        }
