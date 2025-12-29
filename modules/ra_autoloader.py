import importlib
import json
import logging
import asyncio
from pathlib import Path
from types import ModuleType
from typing import Dict, List

CORE_FILES = {"ra_self_master", "ra_bot_gpt"}
FORBIDDEN_PREFIXES = ("run_", "__")

class RaAutoloader:
    def __init__(self, manifest_path="data/ra_manifest.json"):
        self.manifest_path = Path(manifest_path)
        self.modules: Dict[str, ModuleType] = {}
        self.tasks: Dict[str, asyncio.Task] = {}

    def load_manifest(self) -> List[str]:
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        return manifest.get("active_modules", [])

    def _is_allowed(self, name: str) -> bool:
        if name in CORE_FILES:
            return False
        if name.startswith(FORBIDDEN_PREFIXES):
            return False
        return True

    def activate_modules(self) -> Dict[str, ModuleType]:
        active = self.load_manifest()

        for name in active:
            if not self._is_allowed(name):
                logging.info(f"[RaAutoloader] ⛔ Пропущен core/forbidden модуль: {name}")
                continue

            try:
                module = importlib.import_module(f"modules.{name}")
                self.modules[name] = module
                logging.info(f"[RaAutoloader] ✅ Модуль активирован: {name}")
            except Exception as e:
                logging.error(f"[RaAutoloader] ❌ Ошибка загрузки {name}: {e}")

        return self.modules

    async def start_async_modules(self):
        for name, module in self.modules.items():
            start_fn = getattr(module, "start", None)
            if start_fn and asyncio.iscoroutinefunction(start_fn):
                self.tasks[name] = asyncio.create_task(start_fn())
                logging.info(f"[RaAutoloader] 🚀 Async модуль запущен: {name}")

    async def stop_async_modules(self):
        for task in self.tasks.values():
            task.cancel()
        self.tasks.clear()
        logging.info("[RaAutoloader] 🛑 Все async модули остановлены")

    def status(self):
        return {
            "modules": list(self.modules.keys()),
            "async": list(self.tasks.keys())
        }
