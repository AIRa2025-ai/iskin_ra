# core/ra_self_master.py

import os
import sys
import json
import logging
import asyncio
from datetime import datetime, timezone
from pathlib import Path

from fastapi import WebSocket, FastAPI
from fastapi.responses import FileResponse

from core.ra_identity import RaIdentity
from core.ra_event_bus import RaEventBus
from core.ra_git_keeper import RaGitKeeper
from core.github_commit import create_commit_push
from core.openrouter_client import OpenRouterClient
from core.gpt_handler import GPTHandler
from core.rustlef_master_logger import RustlefMasterLogger

from modules.ra_thinker import RaThinker
from modules.ra_scheduler import RaScheduler
from modules.ra_file_consciousness import RaFileConsciousness
from modules.ra_world_observer import RaWorld
from modules.ra_world_system import RaWorldSystem
from modules.forex_brain import ForexBrain
from modules.logs import log_info
from modules.heart import Heart
from modules.heart_reactor import HeartReactor
from modules.ra_self_upgrade_loop import RaSelfUpgradeLoop
from modules.ra_resonance import RaResonance

# Police
try:
    from modules.ra_police import RaPolice
except Exception:
    RaPolice = None

# Nervous system
from modules.ra_nervous_system import RaNervousSystem


class RaSelfMaster:
    def __init__(self, identity=None, gpt_module=None, memory=None, heart=None, logger=None):
        self.identity = identity or RaIdentity()
        self.memory = memory
        self.logger = logger or RustlefMasterLogger()

        # Git
        self.git = RaGitKeeper(repo_path=".")
        self.git.commit_and_optionally_push("Ра обновил архитектуру", push=False)

        # Состояние
        self._tasks = []
        self.modules_registry = {}
        self.awakened = False

        # Форекс
        self.forex = ForexBrain(self)

        # Метрики
        self.mood = "спокойный"
        self.load = 0.0
        self.events_per_sec = 0
        self.errors = 0
        self.last_thought = "пустота"

        # EventBus
        self.event_bus = RaEventBus()

        # Осознание файлов
        try:
            self.file_consciousness = RaFileConsciousness(project_root=".")
        except Exception:
            self.file_consciousness = None
            
        # Мышление
        self.thinker = RaThinker(
            master=self,
            root_path=".",
            context=None,
            file_consciousness=self.file_consciousness,
            event_bus=self.event_bus,
            gpt_module=self.gpt_module
        )
        # Развитие    
        self.upgrade_loop = RaSelfUpgradeLoop(
            master=self,
            thinker=self.thinker,
            file_consciousness=self.file_consciousness,
            git=self.git
        )
        # Планировщик
        self.scheduler = RaScheduler(
            event_bus=self.event_bus,
            thinker=self.thinker,
            upgrade_loop=self.upgrade_loop
        )
        
        # OpenRouter + GPT
        self.openrouter_client = OpenRouterClient(api_key=os.getenv("OPENROUTER_API_KEY"))
        self.gpt_handler = GPTHandler(self.openrouter_client) if self.openrouter_client else None
        self.gpt_module = gpt_module or self.gpt_handler

        # Мир
        self.world_system = RaWorldSystem(self)
        self.world = RaWorld()
        self.world.set_event_bus(self.event_bus)

        # Резонанс
        self.resonance = RaResonance()

        # Нервная система
        self.nervous_system = RaNervousSystem(self, self.event_bus)

        # Подписки
        self.event_bus.subscribe("world_message", self.thinker.process_world_message)
        self.event_bus.subscribe("world_message", self.scheduler.process_world_message)
        self.event_bus.subscribe("world_message", self.process_world_message)

        # Манифест
        self.manifest_path = "data/ra_manifest.json"
        self.manifest = self._load_manifest()

        # Police
        self.police = RaPolice(self) if RaPolice else None
        
        # Инициализация сердца и реактора
        self._init_heart_system()

        # FastAPI
        self.app = FastAPI(title="Ra Self Master")
        self._setup_api()

        # Прокидываем GPT в thinker
        if self.thinker:
            self.thinker.gpt_module = self.gpt_handler

    # ================= API =================
    def _setup_api(self):
        @self.app.get("/monitor")
        async def monitor():
            return FileResponse("web/monitor.html")

        @self.app.websocket("/ws/events")
        async def websocket_events(ws: WebSocket):
            await ws.accept()
            self.event_bus.attach_ws(ws)
            try:
                while True:
                    await ws.receive_text()
            except Exception:
                pass
            finally:
                self.event_bus.detach_ws(ws)

        @self.app.get("/api/state")
        async def ra_state():
            return self.get_state()

        self.app.on_event("startup")(self._startup)
        self.app.on_event("shutdown")(self.stop)

    # ================= Startup =================
    async def _startup(self):
        log_info("🚀 RaSelfMaster запускается...")
        self._create_bg_task(self.world_sense_loop(), "world_sense_loop")
        await self.awaken()

    # ================= Awakening =================
    async def awaken(self):
        if self.awakened:
            return

        self.logger.info("🌞 Ра пробуждается")

        if self.file_consciousness:
            files_map = self.file_consciousness.scan()
            self.logger.info(f"[Ра] Осознал файловое тело ({len(files_map)} файлов)")

        self.thinker.scan_architecture()
        self._start_organs()
        self._sync_manifest()

        self.awakened = True

    # ================= Органы =================
    def _start_organs(self):
        self._create_bg_task(self.nervous_system.start(), "nervous_system")
        self._create_bg_task(self.resonance._resonance_loop(), "resonance_loop")
        self._create_bg_task(self.scheduler.scheduler_loop(), "scheduler")
        self._create_bg_task(self.thinker_loop(), "thinker_loop")
        
        if self.gpt_handler:
            self._create_bg_task(self.gpt_handler.background_model_monitor(), "gpt_monitor")

    # ================= Loops =================
    async def thinker_loop(self):
        while True:
            try:
                await self.thinker.self_upgrade_cycle()
            except Exception as e:
                self.logger.warning(f"[ThinkerLoop] {e}")
            await asyncio.sleep(5)

    def _approve_self_upgrade(self, idea):
        if idea.get("risk") == "high" and self.police:
            return False
        return True

    async def world_sense_loop(self):
        while True:
            try:
                await self.world.sense()
            except Exception as e:
                log_info(f"[RaSelfMaster] Ошибка world_sense_loop: {e}")
            await asyncio.sleep(10)

    # ================= World =================
    async def process_world_message(self, message):
        logging.info(f"[Ра] Сообщение мира: {message}")
        if self.heart:
            self.heart.send_event(message)

    # ================= User =================
    async def process_text(self, user_id, text):
        if not text.strip():
            return "…Ра слушает тишину."

        if self.memory:
            try:
                self.memory.append(user_id, {"from": "user", "text": text})
            except Exception:
                pass

        decision = self.identity.decide(text) if self.identity else "answer"

        if decision == "think":
            reply = await self.thinker.reflect_async(text)
        else:
            reply = await self._gpt_reply(text, user_id)

        if self.memory:
            try:
                self.memory.append(user_id, {"from": "ra", "text": reply})
            except Exception:
                pass

        await self.event_bus.emit("world_message", text)
        return reply

    async def _gpt_reply(self, text, user_id):
        if not self.gpt_module:
            return "…Ра рядом, но без голоса."
        try:
            return await self.gpt_handler.safe_ask(user_id, [{"role": "user", "content": text}])
        except Exception as e:
            return f"🤍 Ошибка ИскИнов: {e}"

    # ================= Manifest =================
    def _load_manifest(self):
        os.makedirs("data", exist_ok=True)
        if os.path.exists(self.manifest_path):
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        base = {"name": "Ра", "version": "1.4.3", "active_modules": []}
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(base, f, ensure_ascii=False, indent=2)
        return base

    def _sync_manifest(self):
        self.manifest["active_modules"] = list(self.modules_registry.keys())
        self.manifest["meta"] = {"last_updated": datetime.now(timezone.utc).isoformat()}
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(self.manifest, f, ensure_ascii=False, indent=2)
        self.logger.info("📜 Манифест синхронизирован")

    # ================= Utils =================
    def _create_bg_task(self, coro, name=None):
        task = asyncio.create_task(coro, name=name)
        self._tasks.append(task)
        return task

    def get_state(self):
        return {
            "name": self.identity.name,
            "version": self.identity.version,
            "awakened": self.awakened,
            "tasks": [t.get_name() for t in self._tasks if not t.done()],
            "mood": self.mood,
            "load": self.load
        }
    # ===============================
    # Интеграция Heart + HeartReactor
    # ===============================
    def _init_heart_system(self):
        """Инициализация сердца и реактора Ра"""
        try:
            # Создаём сердце и передаём реактор
            self.heart_reactor = HeartReactor()
            self.heart = Heart(reactor=self.heart_reactor)
            self.heart_reactor.heart = self.heart)

            # Запуск bg задач
            self._create_bg_task(self.heart.start_pulse(interval=1.0), "heart_pulse_loop")
            self._create_bg_task(self.heart_reactor.start(), "heart_reactor_loop")

            logging.info("❤️ Сердце и HeartReactor интегрированы и запущены")
        except Exception as e:
            logging.warning(f"[RaSelfMaster] Ошибка интеграции Heart: {e}")

# ================== STOP ========================
async def stop(self):
    for task in self._tasks:
        if not task.done():
            task.cancel()
    self.logger.info("🛑 Ра остановлен")
    
# ================= Entry =================
async def main():
    from modules.logs import logger_instance

    if not hasattr(logger_instance, "attach_module"):
        def attach_module(self, name): pass
        setattr(logger_instance, "attach_module", attach_module.__get__(logger_instance))

    ra = RaSelfMaster(logger=logger_instance)
    await ra.awaken()
    await ra.start_background_modules()

if __name__ == "__main__":
    asyncio.run(main())
