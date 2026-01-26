# core/ra_self_master.py

import os
import sys
import json
import logging
import asyncio
import importlib.util
from .ra_identity import RaIdentity
from datetime import datetime, timezone
from pathlib import Path
from fastapi import WebSocket, FastAPI
from core.ra_git_keeper import RaGitKeeper
from core.github_commit import create_commit_push
from core.rustlef_master_logger import RustlefMasterLogger
from core.ra_event_bus import RaEventBus
from core.gpt_handler import GPTHandler
from core.openrouter_client import OpenRouterClient
from modules.ra_file_manager import load_rasvet_files
from modules.ra_thinker import RaThinker
from modules.ra_scheduler import RaScheduler
from modules.ra_file_consciousness import RaFileConsciousness
from modules.ra_world_observer import RaWorld
from modules.ra_world_system import RaWorldSystem   # ✅ ДОБАВЛЕН
from modules.forex_brain import ForexBrain
from modules.logs import log_info
from modules.security import log_action
from modules.heart_reactor import HeartReactor
# Police
_police = None
try:
    from modules.ra_police import RaPolice
    _police = RaPolice
except Exception:
    _police = None


class RaSelfMaster:
    def __init__(self, identity=None, gpt_module=None, memory=None, heart=None, logger=None):
        self.identity = identity or RaIdentity()
        self.gpt_module = gpt_module
        self.memory = memory
        self.heart = heart
        self.logger = logger or RustlefMasterLogger()

        # Git
        self.git = RaGitKeeper(repo_path=".")
        self.git.commit_and_optionally_push("Ра обновил архитектуру", push=False)

        # Задачи и модули
        self._tasks = []
        self.active_modules = []
        self.modules_registry = {}
        self.awakened = False
        self.loop_started = False

        # Форекс
        self.forex = ForexBrain(self)

        # Эмоции и статистика
        self.mood = "спокойный"
        self.load = 0.0
        self.events_per_sec = 0
        self.errors = 0
        self.last_thought = "пустота"

        # Event bus
        self.event_bus = RaEventBus()

        # Сердце
        self.heart_reactor = HeartReactor()

        # File consciousness
        try:
            self.file_consciousness = RaFileConsciousness(project_root=".")
        except Exception:
            self.file_consciousness = None

        # Thinker
        self.thinker = RaThinker(".", None, self.file_consciousness, self, self.gpt_module)

        # GPT и OpenRouter
        self.openrouter_client = OpenRouterClient(
            api_key="sk-or-v1-5cbfadccc5926512d1c7a6d5168e1a9cdf2049af3684c236b815e6c09fbf"
        )
        self.gpt_handler = GPTHandler(self.openrouter_client) if self.openrouter_client else None

        # Мир
        self.world_system = RaWorldSystem(self)   # порядок важен
        self.world = RaWorld()
        self.world.set_event_bus(self.event_bus)

        # Планировщик
        self.scheduler = RaScheduler(event_bus=self.event_bus)

        # Подписки
        self.event_bus.subscribe("world_message", self.thinker.process_world_message)
        self.event_bus.subscribe("world_message", self.scheduler.process_world_message)
        self.event_bus.subscribe("world_message", self.process_world_message)

        # Автозагрузчик
        try:
            from modules.ra_autoloader import RaAutoloader
            self.autoloader = RaAutoloader()
        except Exception:
            self.autoloader = None

        self.manifest_path = "data/ra_manifest.json"
        self.manifest = self._load_manifest()

        self.police = None
        from modules.ra_nervous_system import RaNervousSystem
        self.nervous_module = RaNervousSystem(self, self.event_bus)

        # FastAPI
        self.app = FastAPI(title="Ra Self Master")
        from fastapi.responses import FileResponse

        @self.app.get("/monitor")
        async def monitor():
            return FileResponse("web/monitor.html")

        self.ws_clients = set()

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
        self.app.on_event("shutdown")(self.stop_modules)

        # Подписка логгера
        if hasattr(self.logger, "on"):
            self.logger.on("market", self.on_market_event)
            
    # ===============================
    # Background loops
    # ===============================
    def start_thinker_loop(self):
        if self.loop_started:
            return

        async def thinker_loop():
            while True:
                await self.thinker.self_upgrade_cycle()
                await asyncio.sleep(5)

        self._create_bg_task(thinker_loop(), "thinker_loop")
        self.loop_started = True

    def start_task_loop(self):
        async def task_listener():
            while True:
                task = await self.get_new_task()
                await self.thinker.on_new_task(task)

        self._create_bg_task(task_listener(), "task_loop")
        
    def evolve_and_commit(self, message, push=False, files_dict=None):
        # локальный коммит
        self.git.commit_local(message)

        # если нужно — пуш в облако
        if push and files_dict:
            create_commit_push("ra-evolution", files_dict, f"🧬 Ра: {message}")
    # ===============================================================
    async def on_thought(self, thought):
        # Просто логируем событие для начала
        logging.info(f"[Ра] Новая мысль: {thought}")
        # сюда можно добавить любую обработку
    # =============================================================
    async def on_world_event(self, message):
        logging.info(f"[Ра] Событие мира: {message}")
        # можно добавить любую обработку

    # =====================================================
    # 🟢 Метод для эмита событий
    # =====================================================
    async def emit(self, event_name, payload):
        if self.event_bus:
            await self.event_bus.emit(event_name, payload)
        else:
            import logging
            logging.warning(f"[RaSelfMaster] Нет event_bus, событие {event_name} не отправлено.")
    # =========================================
    # Метод WebSocket
    # =========================================
    async def _emit_ws_event(self, event_type, data):
        payload = {
            "time": datetime.now(timezone.utc).isoformat(),
            "type": event_type,
            "source": "Ra",
            "data": str(data)
        }
        dead = []
        for ws in self.ws_clients:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.ws_clients.remove(ws)

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
    # Обработка сообщений мира
    # ===============================
    async def process_world_message(self, message):
        logging.info(f"[RaSelfMaster] Сообщение мира: {message}")
        text = str(message).lower()
        if "свет" in text:
            logging.info("[Ра] Усиление Света")
        elif "тревога" in text:
            logging.info("[Ра] Режим стабилизации")
        await self._emit_ws_event("world_message", message)
        await asyncio.sleep(0.01)
        if hasattr(self, "heart_reactor"):
            self.heart_reactor.send_event(message)
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

    async def _gpt_reply(self, text, user_id="anon"):
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
            logging.warning(f"[RaSelfMaster] Ошибка gpt_module: {e}")
        if not self.gpt_handler:
            return "…Ра рядом, но пока без голосов ИскИнов."
        try:
            return await self.gpt_handler.safe_ask(user_id, [{"role": "user", "content": text}])
        except Exception as e:
            return f"🤍 Ра слышит тишину моделей: {e}"
    # ===============================
    # Ra self-upgrade
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
        # логика: блокируем high-risk только если есть полиция
        if idea.get("risk") == "high" and self.police:
            return False
        return True

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
                if start_fn:
                    if asyncio.iscoroutinefunction(start_fn):
                        self._create_bg_task(start_fn(), f"mod:{mod_name}")
                    else:
                        # синхронный старт — запускаем в отдельном потоке
                        asyncio.get_running_loop().run_in_executor(None, start_fn)

                logging.info(f"[Ра] Подключён модуль: {mod_name}")
            except Exception as e:
                logging.warning(f"[Ра] Ошибка модуля {mod_name}: {e}")
                
    # ===============================================
    def subscribe(self, event_name, callback):
        self.event_bus.subscribe(event_name, callback)
    # =========================================
    def register_module(self, name, module):
        self.modules_registry[name] = module
        logging.info(f"[Ра] Модуль зарегистрирован: {name}")
    # ===============================
    async def start(self):
        await self.start_background_modules()
        await self.event_bus.emit("world_message", "Ра встал на поток")

    # ===============================================================
    async def start_background_modules(self):
        self._create_bg_task(self.nervous_module.start(), "nervous_module")
        if self.gpt_handler:
            self._create_bg_task(self.gpt_handler.background_model_monitor(), "gpt_model_monitor")
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
        self._create_bg_task(self.scheduler.scheduler_loop(), "scheduler_loop")
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
        self.start_thinker_loop()
        self.start_task_loop()

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
        
    def on_market_event(self, event):
        print("Ра получил событие рынка:", event)

    # ===============================
    # Stop modules
    # ===============================
    async def stop_modules(self):
        # сначала nervous
        if hasattr(self, "nervous_module"):
            await self.nervous_module.stop()

        # потом остальные таски
        for task in list(self._tasks):
            if not task.done():
                task.cancel()
        self._tasks.clear()
        log_info("RaSelfMaster остановлен")
    # ===============================
    # Background helper
    # ===============================
    def _create_bg_task(self, coro, name=None):
        task = asyncio.create_task(coro, name=name)
        self._tasks.append(task)
        return task
# =================================================
# Точка входа модуля — ВНЕ класса
# =================================================
async def main():
    from modules.logs import logger_instance  # убедимся, что logger_instance существует
    self_master = RaSelfMaster(logger=logger_instance)
    await self_master.awaken()
    await self_master.start_background_modules()
    await self_master.start()

if __name__ == "__main__":
    asyncio.run(main())
