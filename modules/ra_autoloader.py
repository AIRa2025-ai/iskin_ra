# modules/ra_autoloader.py
import os
import importlib
import json
import logging

class RaAutoloader:
    """
    Менеджер автоподключения модулей Ра.
    Сканирует папку modules/, сверяет с ra_manifest.json,
    и автоматически активирует нужные.
    """

    def __init__(self, modules_path="modules", manifest_path="data/ra_manifest.json"):
        self.modules_path = modules_path
        self.manifest_path = manifest_path
        self.modules = {}

    def scan_modules(self):
        files = [f[:-3] for f in os.listdir(self.modules_path) if f.endswith(".py")]
        logging.info(f"[RaAutoloader] Найдены модули: {files}")
        return files

    def load_manifest(self):
        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
                return manifest.get("active_modules", [])
        except Exception as e:
            logging.error(f"[RaAutoloader] Не удалось загрузить manifest: {e}")
            return []

    def activate_modules(self):
        active = self.load_manifest()
        available = self.scan_modules()
        for name in active:
            if name in available:
                try:
                    module = importlib.import_module(f"modules.{name}")
                    self.modules[name] = module
                    logging.info(f"[RaAutoloader] ✅ Активирован модуль: {name}")
                except Exception as e:
                    logging.error(f"[RaAutoloader] ❌ Ошибка активации {name}: {e}")
        return self.modules

    def get_module(self, name):
        return self.modules.get(name)
