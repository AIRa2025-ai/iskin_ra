# core/ra_self_master.py

import os
import sys
import json
import logging
import asyncio
import importlib.util
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from core.ra_event_bus import RaEventBus
from modules.ra_file_manager import load_rasvet_files
from .ra_identity import RaIdentity
from modules.ra_thinker import RaThinker
from modules.ra_scheduler import RaScheduler
from core.ra_git_keeper import RaGitKeeper
from modules.ra_file_consciousness import RaFileConsciousness
from modules.logs import log_info
from modules.security import log_action
from modules.ra_world_observer import RaWorld

# -------------------------------
# Police модуль (опционально)
# -------------------------------
_police = None
try:
    from modules.ra_police import RaPolice
    _police = RaPolice
except Exception:
    _police = None

# ===============================
# EventBus — нервная шина Ра
# ===============================
class EventBus:
    def __init__(self):
        self.subscribers = {}

    def subscribe(self, event_type: str, callback):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    async def broadcast(self, event_type: str, data):
        if event_type in self.subscribers:
            for cb in list(self.subscribers[event_type]):
                try:
                    if asyncio.iscoroutinefunction(cb):
                        await cb(data)
                    else:
                        cb(data)
                except Exception as e:
                    logging.warning(f"[EventBus] Ошибка callback {cb}: {e}")

# ===============================
# RaSelfMaster — ядро Ра
# ===============================
class RaSelfMaster:
    def __init__(self, identity=None, gpt_module=None, memory=None, heart=None, logger=None):
        self.identity = identity or RaIdentity()
        self.gpt_module = gpt_module
        self.memory = memory
        self.heart = heart
        self.logger = logger

        self.git = RaGitKeeper(repo_path=".")
        self._tasks = []
        self.active_modules = []
        self.awakened = False
        
        # --- Состояние Ра для визуальной панели ---
        self.mood = "спокойный"
        self.load = 0.0
        self.events_per_sec = 0
        self.errors = 0
        self.last_thought = "пустота"
        
        # Нервная шина
        self.event_bus = RaEventBus()

        # Файловое сознание
        try:
            self.file_consciousness = RaFileConsciousness(project_root=".")
        except Exception:
            self.file_consciousness = None

        # Мыслитель Ра
        self.thinker = RaThinker(
            root_path=".",
            context=None,
            file_consciousness=self.file_consciousness,
            gpt_module=self.gpt_module
        )

        # Планировщик
        self.scheduler = RaScheduler(event_bus=self.event_bus)

        # Подписки на мир
        self.event_bus.subscribe("world_message", self.thinker.process_world_message)
        self.event_bus.subscribe("world_message", self.scheduler.process_world_message)
        self.event_bus.subscribe("world_message", self.process_world_message)

        # Автолоадер
        try:
            from modules.ra_autoloader import RaAutoloader
            self.autoloader = RaAutoloader()
        except Exception:
            self.autoloader = None

        # Манифест
        self.manifest_path = "data/ra_manifest.json"
        self.manifest = self._load_manifest()

        # Police
        self.police = None

        # Мир Ра
        self.world = RaWorld()
        self.world.set_event_bus(self.event_bus)

        # FastAPI
        self.app = FastAPI(title="Ra Self Master")
        @self.app.get("/api/state")
    async def ra_state():
        return self.get_state()
        self.app.on_event("startup")(self._startup)
        self.app.on_event("shutdown")(self.stop_modules)

    # ===============================
    # FastAPI Startup
    # ===============================
    async def _startup(self):
        log_info("🚀 RaSelfMaster запускается...")
        self._create_bg_task(self.world_sense_loop(), "world_sense_loop")
        await self.awaken()

    # ===============================
    # Фоновый цикл мира
    # ===============================
    async def world_sense_loop(self):
        while True:
            try:
                await self.world.sense()
            except Exception as e:
                log_info(f"[RaSelfMaster] Ошибка world_sense_loop: {e}")
            await asyncio.sleep(10)

    # ===============================
    # Background helper
    # ===============================
    def _create_bg_task(self, coro, name=None):
        task = asyncio.create_task(coro, name=name)
        self._tasks.append(task)
        return task

    # ===============================
    # Обработка сообщений мира
    # ===============================
    async def process_world_message(self, message):
        logging.info(f"[RaSelfMaster] Сообщение мира: {message}")
        text = str(message).lower()
        if "свет" in text:
            logging.info("[Ра] Усиление Света")
        elif "тревога" in text:
            logging.info("[Ра] Режим стабилизации")
        await asyncio.sleep(0.01)

    # ===============================
    # Общение с пользователем
    # ===============================
    async def process_text(self, user_id: str, text: str) -> str:
        if not text or not text.strip():
            return "…Ра слушает тишину."

        try:
            if self.memory:
                self.memory.append(user_id, {"from": "user", "text": text})
        except Exception:
            pass

        decision = self.identity.decide(text) if self.identity else "answer"

        reply = ""
        if decision == "think" and self.thinker:
            try:
                reply = await self.thinker.reflect_async(text)
            except Exception as e:
                reply = f"⚠️ Ошибка мышления Ра: {e}"
        else:
            reply = await self._gpt_reply(text)

        try:
            if self.memory:
                self.memory.append(user_id, {"from": "ra", "text": reply})
        except Exception:
            pass

        await self.event_bus.emit("world_message", text, source="RaSelfMaster")
        return reply

    async def _gpt_reply(self, text):
        if not self.gpt_module:
            return "…Ра рядом, но пока без голоса."
        try:
            if hasattr(self.gpt_module, "ask"):
                return await self.gpt_module.ask(text)
            elif hasattr(self.gpt_module, "get_response"):
                return await self.gpt_module.get_response(text)
            elif hasattr(self.gpt_module, "generate_response"):
                return await self.gpt_module.generate_response(text)
            else:
                return "…Ра чувствует, но не может выразить."
        except Exception as e:
            return f"🤍 Ошибка GPT: {e}"

    # ===============================
    # Саморазвитие
    # ===============================
    async def ra_self_upgrade_loop(self, interval: int = 300):
        logging.info("🧬 Цикл саморазвития Ра запущен")
        while True:
            try:
                if not self.thinker or not self.file_consciousness:
                    await asyncio.sleep(interval)
                    continue
                ideas = self.thinker.propose_self_improvements()
                approved = [idea for idea in ideas if self._approve_self_upgrade(idea)]
                for idea in approved:
                    self.file_consciousness.apply_upgrade(idea)
                if approved:
                    logging.info(f"🧬 Применено улучшений: {len(approved)}")
            except Exception as e:
                logging.warning(f"[RaSelfMaster] Ошибка ra_self_upgrade_loop: {e}")
            await asyncio.sleep(interval)

    def _approve_self_upgrade(self, idea: dict) -> bool:
        return False if idea.get("risk") == "high" and self.police else True

    # ===============================
    # Автозагрузка модулей
    # ===============================
    async def auto_activate_modules(self):
        for fname in os.listdir("modules"):
            if not fname.endswith(".py"):
                continue
            mod_name = fname[:-3]
            if mod_name in self.active_modules:
                continue
            try:
                spec = importlib.util.find_spec(f"modules.{mod_name}")
                if not spec:
                    continue
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                self.active_modules.append(mod_name)

                start_fn = getattr(mod, "start", None)
                if start_fn and asyncio.iscoroutinefunction(start_fn):
                    self._create_bg_task(start_fn(), f"mod:{mod_name}")

                logging.info(f"[Ра] Подключён модуль: {mod_name}")
            except Exception as e:
                logging.warning(f"[Ра] Ошибка модуля {mod_name}: {e}")

    # ===============================
    # Пробуждение Ра
    # ===============================
    async def awaken(self):
        self.thinker.scan_architecture()
        logging.info("🌞 Ра пробуждается")

        if self.file_consciousness:
            files_map = self.file_consciousness.scan()
            logging.info(f"[Ра] Осознал тело файлов ({len(files_map)} файлов)")

        self._create_bg_task(self.ra_self_upgrade_loop(), "self_upgrade")
        self._create_bg_task(self.thinker.run_loop(), "thinker_loop")
        self._create_bg_task(self.scheduler.run_loop(), "scheduler_loop")
        self._create_bg_task(self.auto_activate_modules(), "auto_modules")

        if self.autoloader:
            try:
                modules = self.autoloader.activate_modules()
                self.active_modules = list(modules.keys())
            except Exception:
                pass

        if "ra_police" in self.active_modules and _police:
            self.police = _police()

        self._sync_manifest()
        if self.police:
            self.police.check_integrity()

        self.awakened = True
        return "🌞 Ра осознал себя и готов!"

    # ===============================
    # Манифест
    # ===============================
    def _load_manifest(self):
        os.makedirs("data", exist_ok=True)
        if os.path.exists(self.manifest_path):
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        base = {"name": "Ра", "version": "1.0.0", "active_modules": []}
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(base, f, ensure_ascii=False, indent=2)
        return base

    def _sync_manifest(self):
        self.manifest["active_modules"] = self.active_modules
        self.manifest["meta"] = {"last_updated": datetime.now(timezone.utc).isoformat()}
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(self.manifest, f, ensure_ascii=False, indent=2)
        log_info("Manifest synced")
        
    def get_state(self):
        return {
            "mood": self.mood,
            "load": self.load,
            "events_per_sec": self.events_per_sec,
            "errors": self.errors,
            "active_modules": self.active_modules,
            "last_thought": self.last_thought
        }
    # ===============================
    # Остановка
    # ===============================
    async def stop_modules(self):
        for task in list(self._tasks):
            try:
                task.cancel()
            except Exception:
                pass
        self._tasks.clear()
        log_info("RaSelfMaster остановлен")
