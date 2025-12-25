import os  # noqa: F401
import importlib
import json
import logging
import asyncio
from types import ModuleType
from pathlib import Path
from typing import Dict, List

class RaAutoloader:
    def __init__(self, modules_paths: List[str] = None, manifest_path="data/ra_manifest.json"):
        if not modules_paths:
            modules_paths = ["core", "modules"]
        self.modules_paths = [Path(p) for p in modules_paths]
        self.manifest_path = Path(manifest_path)
        self.modules: Dict[str, ModuleType] = {}
        self._tasks: Dict[str, asyncio.Task] = {}

        # создаем папки и __init__.py, чтобы Python видел как пакеты
        for path in self.modules_paths:
            path.mkdir(parents=True, exist_ok=True)
            init_file = path / "__init__.py"
            if not init_file.exists():
                init_file.write_text("# Package init\n", encoding="utf-8")

        # создаем манифест, если нет
        if not self.manifest_path.parent.exists():
            self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.manifest_path.exists():
            base_manifest = {"active_modules": ["ra_self_master"]}
            self.manifest_path.write_text(json.dumps(base_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            logging.warning("[RaAutoloader] ⚠️ Манифест отсутствовал — создан новый с ra_self_master первым.")

    def scan_modules(self):
        found_modules = []
        for path in self.modules_paths:
            files = [f.stem for f in path.iterdir() if f.is_file() and f.suffix == ".py" and not f.name.startswith("__")]
            found_modules.extend(files)
        unique_modules = list(dict.fromkeys(found_modules))
        logging.info(f"[RaAutoloader] 🔍 Найдены модули: {unique_modules}")
        return unique_modules

    def load_manifest(self):
        try:
            manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            active = manifest.get("active_modules", [])
            # ra_self_master всегда первым
            if "ra_self_master" in self.scan_modules() and "ra_self_master" not in active:
                active.insert(0, "ra_self_master")
            logging.info(f"[RaAutoloader] 📜 Активные модули по manifest: {active}")
            return active
        except Exception as e:
            logging.error(f"[RaAutoloader] ❌ Ошибка загрузки manifest: {e}")
            return ["ra_self_master"]

    def sync_manifest(self, active_list):
        manifest = {
            "active_modules": active_list,
            "meta": {"last_updated": asyncio.get_event_loop().time()}
        }
        try:
            # используем читаемое ISO время для meta
            manifest["meta"]["last_updated"] = asyncio.get_event_loop().time()
            manifest["meta"]["last_updated_iso"] = json.dumps(
                asyncio.get_event_loop().time(), ensure_ascii=False
            )
            self.manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            logging.info("[RaAutoloader] 📄 manifest синхронизирован.")
        except Exception as e:
            logging.error(f"[RaAutoloader] ❌ Ошибка сохранения manifest: {e}")

    def activate_modules(self) -> Dict[str, ModuleType]:
        active_list = self.load_manifest()
        available = self.scan_modules()
        loaded_modules = []

        for name in active_list:
            if name in available and name not in loaded_modules:
                try:
                    for path in self.modules_paths:
                        module_file = path / f"{name}.py"
                        if module_file.exists():
                            # строим корректное имя импорта для Python
                            full_name = f"{path.name}.{name}"
                            if full_name in importlib.sys.modules:
                                module = importlib.reload(importlib.import_module(full_name))
                            else:
                                module = importlib.import_module(full_name)
                            self.modules[name] = module
                            loaded_modules.append(name)
                            logging.info(f"[RaAutoloader] ✅ Модуль активирован: {name}")
                            break
                except Exception as e:
                    logging.error(f"[RaAutoloader] ❌ Ошибка при активации {name}: {e}")
            else:
                logging.warning(f"[RaAutoloader] ⚠️ Модуль '{name}' не найден в {self.modules_paths}")

        self.sync_manifest(list(self.modules.keys()))
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
        for task in list(self._tasks.values()):
            task.cancel()
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
