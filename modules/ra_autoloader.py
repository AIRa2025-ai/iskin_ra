# modules/ra_autoloader.py
import os
import importlib
import json
import logging

class RaAutoloader:
    """
    🌞 Менеджер автоподключения модулей Ра.
    — Автоматически сканирует папку modules/
    — Читает ra_manifest.json
    — Активирует доступные модули
    — Создаёт недостающие папки и файлы при необходимости
    """

    def __init__(self, modules_path="modules", manifest_path="data/ra_manifest.json"):
        self.modules_path = modules_path
        self.manifest_path = manifest_path
        self.modules = {}

        # Автоматическое создание необходимых директорий
        os.makedirs(self.modules_path, exist_ok=True)
        os.makedirs(os.path.dirname(self.manifest_path), exist_ok=True)

    # --- Сканирование папки modules/ ---
    def scan_modules(self):
        try:
            files = [
                f[:-3] for f in os.listdir(self.modules_path)
                if f.endswith(".py") and not f.startswith("__")
            ]
            logging.info(f"[RaAutoloader] 🔍 Найдены модули: {files}")
            return files
        except Exception as e:
            logging.error(f"[RaAutoloader] ❌ Ошибка при сканировании modules/: {e}")
            return []

    # --- Загрузка данных из манифеста ---
    def load_manifest(self):
        try:
            if not os.path.exists(self.manifest_path):
                # если нет manifest — создаём базовый
                base_manifest = {"active_modules": []}
                with open(self.manifest_path, "w", encoding="utf-8") as f:
                    json.dump(base_manifest, f, ensure_ascii=False, indent=2)
                logging.warning("[RaAutoloader] ⚠️ Манифест отсутствовал — создан новый.")

            with open(self.manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
                active = manifest.get("active_modules", [])

            logging.info(f"[RaAutoloader] 📜 Активные модули по manifest: {active}")
            return active

        except Exception as e:
            logging.error(f"[RaAutoloader] ❌ Ошибка загрузки manifest: {e}")
            return []

    # --- Активация модулей ---
    def activate_modules(self):
        active_list = self.load_manifest()
        available = self.scan_modules()

        for name in active_list:
            if name in available:
                try:
                    module = importlib.import_module(f"modules.{name}")
                    self.modules[name] = module
                    logging.info(f"[RaAutoloader] ✅ Модуль активирован: {name}")
                except Exception as e:
                    logging.error(f"[RaAutoloader] ❌ Ошибка при активации {name}: {e}")
            else:
                logging.warning(f"[RaAutoloader] ⚠️ Модуль '{name}' не найден в /modules/")

        logging.info(f"[RaAutoloader] 🌟 Всего активировано: {len(self.modules)} модулей.")
        return self.modules

    # --- Получить модуль по имени ---
    def get_module(self, name):
        return self.modules.get(name)

    # --- Проверить состояние модулей ---
    def status(self):
        return {
            "active": list(self.modules.keys()),
            "count": len(self.modules)
        }

# 🔹 Пример автономного запуска
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
    loader = RaAutoloader()
    loader.activate_modules()
    print(loader.status())
