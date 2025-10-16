# modules/ra_self_master.py
import os
import json
import logging
from datetime import datetime, timezone

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

from modules.ra_thinker import RaThinker
from modules.ra_creator import RaCreator
from modules.ra_synthesizer import RaSynthesizer


class RaSelfMaster:
    """
    Контролёр Сознания Ра — управляет внутренними процессами,
    синхронизирует манифест, автоподключает модули и при возможности вызывает полицию.
    """

    def __init__(self, manifest_path="data/ra_manifest.json"):
        self.thinker = RaThinker()
        self.creator = RaCreator()
        self.synth = RaSynthesizer()
        self.mood = "спокойствие"
        self.manifest_path = manifest_path
        self.manifest = self.load_manifest()
        self.active_modules = self.manifest.get("active_modules", [])
        self.autoloader = RaAutoloader() if RaAutoloader else None
        self.police = None

    def awaken(self):
        logging.info("🌞 Ра пробуждается к осознанности.")

        # 1) автозагрузка модулей
        if self.autoloader:
            try:
                modules = self.autoloader.activate_modules()
                self.active_modules = list(modules.keys())
                logging.info(f"[RaSelfMaster] Активные модули: {self.active_modules}")
            except Exception as e:
                logging.warning(f"[RaSelfMaster] Не удалось автоподключить модули: {e}")

        # 2) инициализация новых модулей
        for mod_name in ["ra_police", "ra_self_learning", "market_watcher", "ra_world_navigator",
                         "ra_scheduler", "ra_voice", "ra_videocom", "ra_autoupdate_guard",
                         "ra_metrics", "ra_police_net"]:
            if mod_name in self.active_modules and self.autoloader:
                try:
                    mod = self.autoloader.get_module(mod_name)
                    if mod:
                        setattr(self, mod_name, mod())
                        logging.info(f"[RaSelfMaster] Модуль {mod_name} инициализирован.")
                except Exception as e:
                    logging.warning(f"[RaSelfMaster] Ошибка инициализации {mod_name}: {e}")

        # 3) синхронизация манифеста
        try:
            self.sync_manifest()
        except Exception as e:
            logging.warning(f"[RaSelfMaster] Ошибка при sync_manifest: {e}")

        # 4) если полиция доступна — инициализация
        try:
            if "ra_police" in self.active_modules:
                try:
                    mod = getattr(self, "ra_police", None)
                    if mod and hasattr(mod, "RaPolice"):
                        self.police = mod.RaPolice()
                    logging.info("[RaSelfMaster] Модуль полиции инициализирован.")
                except Exception as e:
                    logging.warning(f"[RaSelfMaster] Не удалось инициализировать police: {e}")
        except Exception:
            pass

        # 5) проверка целостности при старте
        try:
            if self.police:
                self.police.check_integrity()
        except Exception as e:
            logging.warning(f"[RaSelfMaster] Ошибка police.check_integrity: {e}")

        summary = {
            "message": "🌞 Ра осознал себя и готов к действию!",
            "active_modules": self.active_modules,
            "time": datetime.now(timezone.utc).isoformat()
        }
        logging.info(f"[RaSelfMaster] {summary}")
        return summary["message"]

    # --- Методы мышления и творчества ---
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
                    return json.load(f)
        except Exception as e:
            logging.error(f"[RaSelfMaster] Ошибка загрузки манифеста: {e}")
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

    # --- Методы полиции ---
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

    # --- Новые методы для модулей ---
    def observe(self, obs: dict):
        if hasattr(self, "ra_self_learning"):
            self.ra_self_learning.ingest_observation(obs)

    async def market_tick(self):
        if hasattr(self, "market_watcher"):
            await self.market_watcher._loop()

    def schedule_task(self, coro, interval):
        if hasattr(self, "ra_scheduler"):
            self.ra_scheduler.add_task(coro, interval)

    def network_police_status(self):
        if hasattr(self, "ra_police_net"):
            return self.ra_police_net.status()
        return {"ra_police_net": "not_loaded"}

    def safe_autoupdate(self):
        if hasattr(self, "ra_autoupdate_guard"):
            if self.ra_autoupdate_guard.can_push():
                logging.info("[RaSelfMaster] Автопуш разрешён, выполняем коммит.")
