# modules/ra_autoloader.py
import importlib
import json
import logging
import asyncio
from pathlib import Path
from types import ModuleType
from typing import Dict, List
import sys
from modules import errors

# Основные файлы core, которые не должны загружаться через автолоадер
CORE_FILES = {"ra_self_master", "ra_bot_gpt", "ra_identity"}
FORBIDDEN_PREFIXES = ("run_", "__")

# Модули по умолчанию
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
        self.failed_modules: Dict[str, str] = {}  # module_name -> reason

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
            errors.report_error("RaAutoloader", f"Ошибка чтения манифеста: {e}")
            return ACTIVE_DEFAULT

    # ---------- фильтр ----------
    def _is_allowed(self, name: str) -> bool:
        if name in CORE_FILES:
            return False
        if name.startswith(FORBIDDEN_PREFIXES):
            return False
        if name in self.modules:
            return False
        if name in self.failed_modules:
            return False
        return True

    # ---------- загрузка ----------
    def load_modules(self) -> Dict[str, ModuleType]:
        module_names = self.load_manifest()

        for name in module_names:
            if not self._is_allowed(name):
                logging.info(f"[RaAutoloader] Пропущен модуль: {name}")
                continue

            module = None
            try:
                if name in sys.modules:
                    module = sys.modules[name]
                else:
                    try:
                        module = importlib.import_module(f"core.{name}")
                    except ModuleNotFoundError:
                        module = importlib.import_module(f"modules.{name}")

                self.modules[name] = module
                logging.info(f"[RaAutoloader] Модуль загружен в память: {name}")

            except Exception as e:
                logging.error(f"[RaAutoloader] Ошибка загрузки {name}: {e}")
                errors.report_error("RaAutoloader", f"Ошибка загрузки {name}: {e}")
                self.failed_modules[name] = str(e)

        return self.modules

    # ---------- запуск async ----------
    async def activate_module(self, name: str):
        module = self.modules.get(name)
        if not module:
            logging.warning(f"[RaAutoloader] Модуль {name} не найден")
            return

        task = self.tasks.get(name)
        if task and not task.done():
            logging.info(f"[RaAutoloader] Модуль {name} уже активен")
            return

        start_fn = getattr(module, "start", None)
        if start_fn and asyncio.iscoroutinefunction(start_fn):
            try:
                task = asyncio.create_task(start_fn(), name=f"mod:{name}")
                self.tasks[name] = task
                logging.info(f"[RaAutoloader] Async модуль запущен: {name}")
            except Exception as e:
                logging.error(f"[RaAutoloader] Ошибка при запуске {name}: {e}")
                errors.report_error("RaAutoloader", f"Ошибка при запуске {name}: {e}")
        else:
            logging.info(f"[RaAutoloader] Модуль {name} не имеет async start, запуск пропущен")

    # ---------- стоп async ----------
    async def stop_async_modules(self):
        if not self.tasks:
            return
        for task in self.tasks.values():
            task.cancel()
        await asyncio.gather(*self.tasks.values(), return_exceptions=True)
        self.tasks.clear()
        logging.info("[RaAutoloader] Все async модули остановлены")

    # ---------- статус ----------
    def status(self):
        return {
            "modules": list(self.modules.keys()),
            "async_tasks": list(self.tasks.keys()),
            "failed_modules": list(self.failed_modules.keys())
        }

    # ---------- активация default ----------
    async def activate_default_modules(self):
        for name in ACTIVE_DEFAULT:
            await self.activate_module(name)
