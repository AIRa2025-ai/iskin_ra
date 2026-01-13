#core/ra_self_master.py
import os
import json
import logging
import asyncio
from datetime import datetime, timezone

# -------------------------------
# Автолоадер модулей
# -------------------------------
try:
    from modules.ra_autoloader import RaAutoloader
except Exception:
    RaAutoloader = None

# -------------------------------
# Police модуль (опционально)
# -------------------------------
_police = None
try:
    from modules.ra_police import RaPolice
    _police = RaPolice
except Exception:
    _police = None

# -------------------------------
# Другие условные модули
# -------------------------------
if os.path.exists("modules/ra_thinker.py"):
    from modules.ra_thinker import RaThinker
else:
    RaThinker = object

if os.path.exists("modules/ra_creator.py"):
    from modules.ra_creator import RaCreator
else:
    RaCreator = object

if os.path.exists("modules/ra_synthesizer.py"):
    from modules.ra_synthesizer import RaSynthesizer
else:
    RaSynthesizer = object


class RaSelfMaster:
    def __init__(self, manifest_path="data/ra_manifest.json"):
        self.thinker = RaThinker() if callable(getattr(RaThinker, "__init__", None)) else None
        self.creator = RaCreator() if callable(getattr(RaCreator, "__init__", None)) else None
        self.synth = RaSynthesizer() if callable(getattr(RaSynthesizer, "__init__", None)) else None

        self.mood = "спокойствие"
        self.manifest_path = manifest_path
        self.manifest = self.load_manifest()
        self.active_modules = self.manifest.get("active_modules", [])
        self.autoloader = RaAutoloader() if RaAutoloader else None
        self.police = None
        self._tasks = []

        # Для единого RaContext / IPC
        self.gpt_module = None
        self.mirolub = None

    # -------------------------------
    # Пробуждение и запуск модулей
    # -------------------------------
    async def awaken(self):
        logging.info("🌞 Ра пробуждается к осознанности.")

        if self.autoloader:
            try:
                modules = self.autoloader.activate_modules()
                self.active_modules = list(modules.keys())
                logging.info(f"[RaSelfMaster] Активные модули: {self.active_modules}")
                for name, mod in modules.items():
                    start_fn = getattr(mod, "start", None)
                    if start_fn and asyncio.iscoroutinefunction(start_fn):
                        task = asyncio.create_task(start_fn())
                        self._tasks.append(task)
                        logging.info(f"[RaSelfMaster] Модуль {name} запущен.")
            except Exception as e:
                logging.warning(f"[RaSelfMaster] Не удалось автоподключить модули: {e}")

        try:
            self.sync_manifest()
        except Exception as e:
            logging.warning(f"[RaSelfMaster] Ошибка при sync_manifest: {e}")

        if "ra_police" in self.active_modules and _police:
            try:
                self.police = _police()
                logging.info("[RaSelfMaster] Модуль полиции инициализирован.")
            except Exception as e:
                logging.warning(f"[RaSelfMaster] Не удалось инициализировать police: {e}")

        summary = {
            "message": "🌞 Ра осознал себя и готов к действию!",
            "active_modules": self.active_modules,
            "time": datetime.now(timezone.utc).isoformat()
        }
        logging.info(f"[RaSelfMaster] {summary}")

        if self.police:
            try:
                self.police.check_integrity()
            except Exception as e:
                logging.warning(f"[RaSelfMaster] Ошибка при police.check_integrity: {e}")

        return summary["message"]

    # -------------------------------
    # Единый метод обработки текста
    # -------------------------------
    async def process_text(self, user_id, text):
        """Обработка текста для Telegram, IPC, RaContext"""
        if hasattr(self, "gpt_module") and getattr(self.gpt_module, "safe_ask", None):
            try:
                return await self.gpt_module.safe_ask(user_id, [{"role": "user", "content": text}])
            except Exception:
                pass
        if hasattr(self, "mirolub") and self.mirolub:
            try:
                return await self.mirolub.process(text)
            except Exception:
                pass
        return "⚠️ CORE не смог обработать запрос."

    # -------------------------------
    # Доп. методы
    # -------------------------------
    def reflect(self, theme: str, context: str):
        return self.thinker.reflect(theme, context) if self.thinker else None

    def manifest(self, theme: str):
        return self.creator.compose_manifesto(theme) if self.creator else None

    def unify(self, *texts: str):
        return self.synth.synthesize(*texts) if self.synth else None

    def status(self):
        return {
            "mood": self.mood,
            "thinker": len(getattr(self.thinker, "thoughts", [])) if self.thinker else 0,
            "active_modules": self.active_modules,
            "modules": ["thinker", "creator", "synthesizer"]
        }

    # -------------------------------
    # Работа с манифестом
    # -------------------------------
    def load_manifest(self):
        try:
            if os.path.exists(self.manifest_path):
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logging.error(f"[RaSelfMaster] Ошибка загрузки манифеста: {e}")

        base = {"name": "Ра", "version": "1.0.0", "active_modules": []}
        try:
            os.makedirs(os.path.dirname(self.manifest_path) or ".", exist_ok=True)
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
                merged = list(dict.fromkeys(self.manifest.get("active_modules", []) + loaded))
                self.manifest["active_modules"] = merged
                self.active_modules = merged
        self.manifest["meta"] = self.manifest.get("meta", {})
        self.manifest["meta"]["last_updated"] = datetime.now(timezone.utc).isoformat()
        try:
            os.makedirs(os.path.dirname(self.manifest_path) or ".", exist_ok=True)
            with open(self.manifest_path, "w", encoding="utf-8") as f:
                json.dump(self.manifest, f, ensure_ascii=False, indent=2)
            logging.info("[RaSelfMaster] Манифест синхронизирован.")
        except Exception as e:
            logging.error(f"[RaSelfMaster] Ошибка сохранения манифеста: {e}")

    # -------------------------------
    # Police
    # -------------------------------
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

    # -------------------------------
    # Остановка модулей
    # -------------------------------
    async def stop_modules(self):
        for task in list(self._tasks):
            try:
                task.cancel()
            except Exception:
                pass
        self._tasks.clear()
