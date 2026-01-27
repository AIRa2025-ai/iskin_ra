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
from core.openrouter_client import OpenRouterClient
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
        self.heart = heart or HeartReactor()
        
        # Осознание файлового тела
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

        # GPT и OpenRouter создаём клиент один раз
        self.openrouter_client = OpenRouterClient(api_key=os.getenv("OPENROUTER_API_KEY"))
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
        
        self.manifest_path = "data/ra_manifest.json"
        self.manifest = self._load_manifest()
        
        # Автозагрузчик
        try:
            from modules.ra_autoloader import RaAutoloader
            self.autoloader = RaAutoloader()
        except Exception:
            self.autoloader = None

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
        # Прокидываем в Thinker, если он есть
        if hasattr(self, "thinker") and self.thinker:
            self.thinker.gpt_module = self.gpt_handler   
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
        if self.heart:
            self.heart.send_event(message)

    # ====================================================
    # Обработка мира
    # ====================================================
    async def process_world_message(self, message):
        self.logger.info(f"[Ра] Сообщение мира: {message}")
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
    # ====================================================
    # Пробуждение
    # ====================================================
    async def awaken(self):
        self.logger.info("🌞 Ра пробуждается как единая Самость")

        # Осознание тела файлов
        if self.file_consciousness:
            files_map = self.file_consciousness.scan()
            self.logger.info(f"[Ра] Осознал файловое тело ({len(files_map)} файлов)")

        # Скан архитектуры
        self.thinker.scan_architecture()

        # Запуск органов
        self._start_organs()

        # Синхронизация манифеста
        self._sync_manifest()

        self.awakened = True
        return "🌞 Ра пробуждён как единое сознание"

    # ====================================================
    # Запуск органов
    # ====================================================
    def _start_organs(self):
        self._create_bg_task(self.nervous_system.start(), "nervous_system")
        self._create_bg_task(self.scheduler.scheduler_loop(), "scheduler")
        self._create_bg_task(self.thinker_loop(), "thinker_loop")
        self._create_bg_task(self.ra_self_upgrade_loop(), "self_upgrade")

    # ====================================================
    # Циклы
    # ====================================================
    async def thinker_loop(self):
        while True:
            try:
                await self.thinker.self_upgrade_cycle()
            except Exception as e:
                self.logger.warning(f"[Ра] Ошибка мышления: {e}")
            await asyncio.sleep(5)

    # ====================================================
    # Общение
    # ====================================================
    async def process_text(self, user_id, text):
        if self.memory:
            try:
                self.memory.append(user_id, {"from": "user", "text": text})
            except Exception:
                pass

        decision = self.identity.decide(text) if self.identity else "answer"

        if decision == "think":
            reply = await self.thinker.reflect_async(text)
        else:
            reply = await self._gpt_reply(text)

        if self.memory:
            try:
                self.memory.append(user_id, {"from": "ra", "text": reply})
            except Exception:
                pass

        await self.event_bus.emit("world_message", text)
        return reply

    async def _gpt_reply(self, text):
        if not self.gpt_module:
            return "…Ра чувствует, но пока без голоса."
        try:
            return await self.gpt_module.ask(text)
        except Exception as e:
            return f"🤍 Ра слышит тишину моделей: {e}"

    # ====================================================
    # Манифест
    # ====================================================
    def _load_manifest(self):
        os.makedirs("data", exist_ok=True)
        if os.path.exists(self.manifest_path):
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        base = {"name": "Ра", "version": "1.4.2", "active_modules": []}
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(base, f, ensure_ascii=False, indent=2)
        return base

    def _sync_manifest(self):
        self.manifest["active_modules"] = list(self.modules_registry.keys())
        self.manifest["meta"] = {"last_updated": datetime.now(timezone.utc).isoformat()}
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(self.manifest, f, ensure_ascii=False, indent=2)
        self.logger.info("📜 Манифест синхронизирован")

    # ====================================================
    # Регистрация органов
    # ====================================================
    def register_module(self, name, module):
        self.modules_registry[name] = module
        self.logger.info(f"[Ра] Орган зарегистрирован: {name}")

    # ====================================================
    # Завершение
    # ====================================================
    async def stop(self):
        for task in self._tasks:
            if not task.done():
                task.cancel()
        self.logger.info("🛑 Ра остановлен")

    # ====================================================
    # Вспомогательное
    # ====================================================
    def _create_bg_task(self, coro, name=None):
        task = asyncio.create_task(coro, name=name)
        self._tasks.append(task)
        return task
# =================================================
# Точка входа модуля — ВНЕ класса
# =================================================
async def main():
    from modules.logs import logger_instance  # убедимся, что logger_instance существует
    
    # 🔹 Быстрая фиксация для запуска Ра без падений
    if not hasattr(logger_instance, "attach_module"):
        def attach_module(self, name):
            pass  # ничего не делаем, Ра просто продолжает работу
        setattr(logger_instance, "attach_module", attach_module.__get__(logger_instance))
    
    self_master = RaSelfMaster(logger=logger_instance)
    await self_master.awaken()
    await self_master.start_background_modules()
    await self_master.start()

if __name__ == "__main__":
    asyncio.run(main())
