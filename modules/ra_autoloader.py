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

class RaAutoloader:
    def __init__(self, manifest_path="data/ra_manifest.json"):
        self.manifest_path = Path(manifest_path)
        self.modules: Dict[str, ModuleType] = {}
        self.tasks: Dict[str, asyncio.Task] = {}
        self.active_modules: List[str] = []

    def load_manifest(self) -> List[str]:
        if not self.manifest_path.exists():
            logging.warning(f"[RaAutoloader] ❌ Манифест не найден: {self.manifest_path}")
            return []
        try:
            manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            return manifest.get("active_modules", [])
        except Exception as e:
            logging.error(f"[RaAutoloader] ❌ Ошибка чтения манифеста: {e}")
            return []

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

            # Отложенная загрузка ra_guardian
            if name == "ra_guardian":
                if "ra_repo_manager" in self.active_modules:
                    try:
                        module = importlib.import_module(f"modules.{name}")
                        self.modules[name] = module
                        self.active_modules.append(name)
                        logging.info(f"[RaAutoloader] ✅ Модуль активирован: {name}")
                    except Exception as e:
                        logging.error(f"[RaAutoloader] ❌ Ошибка загрузки {name}: {e}")
                else:
                    logging.warning("[RaAutoloader] ra_repo_manager ещё не загружен, отложим ra_guardian")
                continue

            try:
                module = importlib.import_module(f"modules.{name}")
                self.modules[name] = module
                self.active_modules.append(name)
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
        await asyncio.gather(*self.tasks.values(), return_exceptions=True)
        self.tasks.clear()
        logging.info("[RaAutoloader] 🛑 Все async модули остановлены")

    def status(self):
        return {
            "modules": list(self.modules.keys()),
            "async": list(self.tasks.keys())
        }
