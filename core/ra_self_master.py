# core/ra_self_master.py
import os
import json
import logging
from datetime import datetime, timezone
import asyncio

# локальный автолоадер — должен быть рядом в проекте
try:
    from ra_autoloader import RaAutoloader
except Exception:
    RaAutoloader = None

# модуль "полиция" подключаем опционально из modules
_police = None
try:
    from modules import ra_police as police_module
    _police = police_module
except Exception:
    try:
        from modules.ra_police import RaPolice  # type: ignore
        _police = True
    except Exception:
        _police = None

# внутренние инструменты мышления/творчества
from modules.ra_thinker import RaThinker
from modules.ra_creator import RaCreator
from modules.ra_synthesizer import RaSynthesizer


class RaSelfMaster:
    """
    Контролёр Сознания — управляет внутренними процессами Ра,
    синхронизирует манифест, автоподключает модули и при возможности вызывает модуль "полиция".
    """

    def __init__(self, manifest_path="data/ra_manifest.json"):
        self.thinker = RaThinker()
        self.creator = RaCreator()
        self.synth = RaSynthesizer()
        self.mood = "спокойствие"
        self.manifest_path = manifest_path
        self.manifest = self.load_manifest()
        self.active_modules = self.manifest.get("active_modules", [])
        # автолоадер (опционально)
        self.autoloader = RaAutoloader() if RaAutoloader else None
        self.police = None
        self._tasks = []

    async def awaken(self):
        logging.info("🌞 Ра пробуждается к осознанности.")
        # 1) Подгружаем автолоадер и активируем модули
        if self.autoloader:
            try:
                modules = self.autoloader.activate_modules()
                self.active_modules = list(modules.keys())
                logging.info(f"[RaSelfMaster] Активные модули: {self.active_modules}")
                # Автозапуск асинхронных стартов у модулей
                for name, mod in modules.items():
                    if hasattr(mod, "start") and asyncio.iscoroutinefunction(mod.start):
                        task = asyncio.create_task(mod.start())
                        self._tasks.append(task)
                        logging.info(f"[RaSelfMaster] Модуль {name} запущен.")
            except Exception as e:
                logging.warning(f"[RaSelfMaster] Не удалось автоподключить модули: {e}")

        # 2) синхронизируем манифест (обновляем last_updated)
        try:
            self.sync_manifest()
        except Exception as e:
            logging.warning(f"[RaSelfMaster] Ошибка при sync_manifest: {e}")

        # 3) если модуль полиции доступен — инициализируем его
        try:
            if "ra_police" in self.active_modules:
                try:
                    mod = self.autoloader.get_module("ra_police") if self.autoloader else None
                    if mod and hasattr(mod, "RaPolice"):
                        self.police = mod.RaPolice()
                    else:
                        from modules.ra_police import RaPolice  # type: ignore
                        self.police = RaPolice()
                    logging.info("[RaSelfMaster] Модуль полиции инициализирован.")
                except Exception as e:
                    logging.warning(f"[RaSelfMaster] Не удалось инициализировать police: {e}")
        except Exception:
            pass

        # 4) Пробуждение отчёт
        summary = {
            "message": "🌞 Ра осознал себя и готов к действию!",
            "active_modules": self.active_modules,
            "time": datetime.now(timezone.utc).isoformat()
        }
        logging.info(f"[RaSelfMaster] {summary}")

        # Если полиция есть — запускаем базовую проверку целостности
        try:
            if self.police:
                self.police.check_integrity()
        except Exception as e:
            logging.warning(f"[RaSelfMaster] Ошибка при запуске police.check_integrity: {e}")

        return summary["message"]

    def reflect(self, theme: str, context: str):
        return self.thinker.reflect(theme, context)

    def manifest(self, theme: str):
        return self.creator.compose_manifesto(theme)

    def unify(self, *texts: str):
        return self.synth.synthesize(*texts)

    def status(self):
        return {
            "mood": self.mood,
            "thinker": len(self.thinker.thoughts),
            "active_modules": self.active_modules,
            "modules": ["thinker", "creator", "synthesizer"]
        }

    # --- Методы работы с манифестом ---
    def load_manifest(self):
        try:
            if os.path.exists(self.manifest_path):
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data
        except Exception as e:
            logging.error(f"[RaSelfMaster] Ошибка загрузки манифеста: {e}")
        # если нет — создаём базовый
        base = {"name": "Ра", "version": "1.0.0", "active_modules": []}
        try:
            os.makedirs(os.path.dirname(self.manifest_path), exist_ok=True)
            with open(self.manifest_path, "w", encoding="utf-8") as f:
                json.dump(base, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.warning(f"[RaSelfMaster] Не удалось создать манифест: {e}")
        return base

    def sync_manifest(self):
        if not self.manifest:
            self.manifest = {"active_modules": []}
        if self.autoloader:
            loaded = list(self.autoloader.modules.keys())
            if loaded:
                merged = list(dict.fromkeys((self.manifest.get("active_modules", []) + loaded)))
                self.manifest["active_modules"] = merged
                self.active_modules = merged
        self.manifest["meta"] = self.manifest.get("meta", {})
        self.manifest["meta"]["last_updated"] = datetime.now(timezone.utc).isoformat()
        try:
            os.makedirs(os.path.dirname(self.manifest_path), exist_ok=True)
            with open(self.manifest_path, "w", encoding="utf-8") as f:
                json.dump(self.manifest, f, ensure_ascii=False, indent=2)
            logging.info("[RaSelfMaster] Манифест синхронизирован.")
        except Exception as e:
            logging.error(f"[RaSelfMaster] Ошибка сохранения манифеста: {e}")

    # --- Команды для полиции ---
    def police_status(self):
        if not self.police:
            return {"police": "not_loaded"}
        try:
            return self.police.status()
        except Exception as e:
            logging.error(f"[RaSelfMaster] Ошибка police.status: {e}")
            return {"police": "error", "error": str(e)}

    def run_backup(self):
        if not self.police:
            return {"backup": "police_not_available"}
        try:
            return self.police.create_backup()
        except Exception as e:
            logging.error(f"[RaSelfMaster] Ошибка police.create_backup: {e}")
            return {"backup": "error", "error": str(e)}

    async def stop_modules(self):
        """Остановить все запущенные асинхронные модули"""
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()
