import importlib
import json
import logging
import asyncio
from pathlib import Path
from types import ModuleType
from typing import Dict, List, Optional

CORE_FILES = {"ra_self_master", "ra_bot_gpt", "ra_identity"}
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
        self._loaded_names: set[str] = set()

    # ---------- manifest ----------
    def load_manifest(self) -> List[str]:
        if not self.manifest_path.exists():
            logging.warning("[RaAutoloader] Manifest not found — using defaults")
            return ACTIVE_DEFAULT.copy()

        try:
            manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            modules = manifest.get("active_modules", [])
            return modules or ACTIVE_DEFAULT.copy()
        except Exception as e:
            logging.error(f"[RaAutoloader] Manifest read error: {e}")
            return ACTIVE_DEFAULT.copy()

    # ---------- filters ----------
    def _is_allowed(self, name: str) -> bool:
        if name in CORE_FILES:
            return False
        if name.startswith(FORBIDDEN_PREFIXES):
            return False
        return True

    # ---------- import safe ----------
    def _safe_import(self, name: str) -> Optional[ModuleType]:
        try:
            return importlib.import_module(f"core.{name}")
        except ModuleNotFoundError:
            try:
                return importlib.import_module(f"modules.{name}")
            except Exception as e:
                logging.error(f"[RaAutoloader] Import failed {name}: {e}")
                return None

    # ---------- load modules ----------
    def load_modules(self) -> Dict[str, ModuleType]:
        module_names = self.load_manifest()

        for name in module_names:
            if not self._is_allowed(name):
                logging.info(f"[RaAutoloader] Skipped forbidden module: {name}")
                continue

            if name in self._loaded_names:
                logging.warning(f"[RaAutoloader] Duplicate load blocked: {name}")
                continue

            module = self._safe_import(name)
            if not module:
                continue

            self.modules[name] = module
            self._loaded_names.add(name)

            logging.info(f"[RaAutoloader] Loaded module into memory: {name}")

        return self.modules

    # ---------- activate async ----------
    async def activate_module(self, name: str):
        module = self.modules.get(name)
        if not module:
            logging.warning(f"[RaAutoloader] Module not found: {name}")
            return

        if name in self.tasks:
            logging.info(f"[RaAutoloader] Module already running: {name}")
            return

        start_fn = getattr(module, "start", None)

        if not start_fn or not asyncio.iscoroutinefunction(start_fn):
            logging.info(f"[RaAutoloader] No async start() in {name}")
            return

        try:
            task = asyncio.create_task(start_fn(), name=f"mod:{name}")
            self.tasks[name] = task
            logging.info(f"[RaAutoloader] Async started: {name}")
        except Exception as e:
            logging.error(f"[RaAutoloader] Failed to start {name}: {e}")

    # ---------- stop ----------
    async def stop_async_modules(self):
        if not self.tasks:
            return

        for name, task in list(self.tasks.items()):
            try:
                task.cancel()
            except Exception:
                pass

        await asyncio.gather(*self.tasks.values(), return_exceptions=True)

        self.tasks.clear()
        logging.info("[RaAutoloader] All async modules stopped")

    # ---------- status ----------
    def status(self):
        return {
            "loaded_modules": list(self.modules.keys()),
            "running_async": list(self.tasks.keys()),
        }
