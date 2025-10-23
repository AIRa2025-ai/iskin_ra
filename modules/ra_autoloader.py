# modules/ra_autoloader.py
import os
import importlib
import json
import logging
import asyncio
from types import ModuleType
from typing import Dict, Any
from pathlib import Path

class RaAutoloader:
    def __init__(self, modules_path="modules", manifest_path="data/ra_manifest.json"):
        self.modules_path = Path(modules_path)
        self.manifest_path = Path(manifest_path)
        self.modules: Dict[str, ModuleType] = {}
        self._tasks: Dict[str, asyncio.Task] = {}

        self.modules_path.mkdir(parents=True, exist_ok=True)
        if not self.manifest_path.parent.exists():
            self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.manifest_path.exists():
            base_manifest = {"active_modules": []}
            self.manifest_path.write_text(json.dumps(base_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            logging.warning("[RaAutoloader] ⚠️ Манифест отсутствовал — создан новый.")

    def scan_modules(self):
        try:
            files = [
                f.stem for f in self.modules_path.iterdir()
                if f.is_file() and f.suffix == ".py" and not f.name.startswith("__")
            ]
            logging.info(f"[RaAutoloader] 🔍 Найдены модули: {files}")
            return files
        except Exception as e:
            logging.error(f"[RaAutoloader] ❌ Ошибка при сканировании modules/: {e}")
            return []

    def load_manifest(self):
        try:
            manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            active = manifest.get("active_modules", [])
            logging.info(f"[RaAutoloader] 📜 Активные модули по manifest: {active}")
            return active
        except Exception as e:
            logging.error(f"[RaAutoloader] ❌ Ошибка загрузки manifest: {e}")
            return []

    def activate_modules(self) -> Dict[str, ModuleType]:
        active_list = self.load_manifest()
        available = self.scan_modules()

        for name in active_list:
            if name in available:
                try:
                    full_name = f"modules.{name}"
                    if full_name in importlib.sys.modules:
                        module = importlib.reload(importlib.import_module(full_name))
                    else:
                        module = importlib.import_module(full_name)
                    self.modules[name] = module
                    logging.info(f"[RaAutoloader] ✅ Модуль активирован: {name}")
                except Exception as e:
                    logging.error(f"[RaAutoloader] ❌ Ошибка при активации {name}: {e}")
            else:
                logging.warning(f"[RaAutoloader] ⚠️ Модуль '{name}' не найден в {self.modules_path}")

        logging.info(f"[RaAutoloader] 🌟 Всего активировано: {len(self.modules)} модулей.")
        return self.modules

    async def start_async_modules(self):
        for name, module in list(self.modules.items()):
            try:
                start_fn = getattr(module, "start", None)
                if start_fn and asyncio.iscoroutinefunction(start_fn):
                    task = asyncio.create_task(start_fn())
                    self._tasks[name] = task
                    logging.info(f"[RaAutoloader] 🚀 Async модуль {name} запущен.")
            except Exception as e:
                logging.error(f"[RaAutoloader] ❌ Ошибка запуска async {name}: {e}")

    async def stop_async_modules(self):
        for name, task in list(self._tasks.items()):
            try:
                task.cancel()
            except Exception:
                pass
        self._tasks.clear()
        logging.info("[RaAutoloader] 🛑 Все async модули остановлены.")

    def get_module(self, name):
        return self.modules.get(name)

    def status(self):
        return {
            "active": list(self.modules.keys()),
            "count": len(self.modules),
            "async_running": list(self._tasks.keys())
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
    loader = RaAutoloader()
    loader.activate_modules()
    asyncio.run(loader.start_async_modules())
    print(loader.status())
