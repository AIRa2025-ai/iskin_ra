# modules/ra_thinker.py
"""
Модуль мышления Ра — RaThinker.
Отвечает за осмысление данных, анализ и вывод инсайтов.
Интегрирован с RaKnowledge для поиска и обновления знаний.
"""

import os
import ast
import asyncio
import logging
from datetime import datetime
from collections import defaultdict
from modules.logs import log_info, log_error
from modules.pamyat import chronicles as soul_chronicles
from modules.world_chronicles import WorldChronicles
from modules.pitanie_svetom import ИсточникЭнергии
from modules.svet_functions import принять_фотоны_любви, преобразовать_в_жизненную_силу
from modules import errors
from modules.rasvet_loader import load_rasvet_files
from modules.ra_creator import RaCreator
from core.ra_memory import memory
from time import time

class RaThinker:
    def __init__(
        self,
        master,
        root_path: str = ".",
        context=None,
        file_consciousness=None,
        event_bus=None,
        gpt_module=None,
        scheduler=None  # 🧬 нейросвязь с планировщиком
    ):
        self.root_path = root_path
        self.context = context
        self.file_consciousness = file_consciousness
        self.gpt_module = gpt_module
        self.master = master
        self.scheduler = scheduler
        self.источник_энергии = ИсточникЭнергии()
        self.источник_энергии.активен = False
        self.last_thought = None
        self.thoughts = []
        self.last_world_event = None
        self.event_bus = event_bus
        self.module_request_history = {}
        self.last_module_creation_time = None
        self.module_creation_lock = asyncio.Lock()
        self.world_chronicles = WorldChronicles()
        self.logger = master.logger if hasattr(master, "logger") else logging
        self.creator = RaCreator(event_bus=self.event_bus)
        
        if hasattr(self.logger, "on") and callable(self.logger.on):
            self.logger.on("market", self.react_to_market)

        # Контекст РаСвета
        try:
            self.rasvet_context = load_rasvet_files(limit_chars=3000)
        except Exception as e:
            self.rasvet_context = ""
            log_error(f"[RaThinker] Ошибка загрузки контекста: {e}")
            errors.report_error("RaThinker", f"Ошибка загрузки контекста: {e}")

        self.architecture = {}
        self.import_graph = defaultdict(set)

        # 🔗 Интеграция с RaKnowledge
        self.knowledge = getattr(master, "knowledge", None)

        self.logger.info("🌞 RaThinker инициализирован с нейросвязями и знаниями")
        
        # ⚠️ Свет запускается отдельно, НЕ в __init__
        self.light_task = None
        self.light_started = False

        self._bus_connected = False

    # -------------------------------
    # Асинхронная рефлексия
    # -------------------------------
    async def reflect_async(self, text: str) -> str:
        self.last_thought = f"[{datetime.now().strftime('%H:%M:%S')}] {text}"
        self.logger.info(f"[RaThinker] reflect_async called: {text}")
        log_info(f"RaThinker thought: {text}")

        knowledge_reply = ""
        if self.knowledge:
            try:
                results = self.knowledge.search(text) or []
                summaries = [r.get("summary", "") for r in results[:3]]
                knowledge_reply = "\n".join(filter(None, summaries)).strip()
            except Exception as e:
                self.logger.error(f"[RaThinker] Ошибка поиска в знаниях: {e}")
                knowledge_reply = ""

        if knowledge_reply:
            reply_text = knowledge_reply
        elif self.gpt_module:
            try:
                reply = await asyncio.wait_for(
                    self.gpt_module.generate_response(text),
                    timeout=20
                )
                reply_text = reply or "нет ответа"
            except Exception as e:
                self.logger.error(f"[RaThinker] Ошибка GPT: {e}")
                reply_text = "нет ответа"
        else:
            reply_text = "нет ответа"

        safe_reply = reply_text[:300] if reply_text else "нет ответа"

        try:
            await soul_chronicles.добавить(
                опыт=f"Мысль Ра: {text} → {safe_reply}",
                user_id="thinker",
                layer="short_term"
            )
        except Exception as e:
            self.logger.error(f"[RaThinker] Ошибка записи в хроники: {e}")
        
        if knowledge_reply and reply_text != knowledge_reply:
            return f"{knowledge_reply}\n\n{reply_text}"
        return reply_text

    # -------------------------------
    # Обновление знаний
    # -------------------------------
    async def refresh_knowledge(self):
        if self.knowledge:
            try:
                self.knowledge._scan_and_update()
                self.knowledge._save_cache()
                log_info("[RaThinker] Знания обновлены")
            except Exception as e:
                self.logger.error(f"[RaThinker] Ошибка обновления знаний: {e}")

    # -------------------------------
    # Реакция на рынок
    # -------------------------------
    def react_to_market(self, event):
        try:
            self.logger.info(f"[RaThinker] Мыслитель реагирует: {event}")
        except Exception as e:
            self.logger.error(f"[RaThinker] Ошибка при реакции на рынок: {e}")

    # -------------------------------
    # Краткое резюме текста
    # -------------------------------
    def summarize(self, data: str) -> str:
        return f"Резюме Ра: {data[:200]}..."

    # -------------------------------
    # Идеи улучшений модулей
    # -------------------------------
    def suggest_improvement(self, module_name: str, issue: str) -> str:
        idea = f"В модуле {module_name} стоит улучшить: {issue}"
        self.thoughts.append(idea)
        self.logger.info(f"[RaThinker] 💡 {idea}")
        return idea

    # -------------------------------
    # Сканирование архитектуры
    # -------------------------------
    def scan_architecture(self):
        self.logger.info("🧠 [RaThinker] Сканирую архитектуру кода")
        self.architecture.clear()
        self.import_graph.clear()

        for root, _, files in os.walk(self.root_path):
            if any(x in root for x in (".git", "__pycache__", "backups")):
                continue
            if any(part.startswith(".") or part == "backups" for part in root.split(os.sep)):
                continue
            for file in files:
                if not file.endswith(".py"):
                    continue

                full_path = os.path.join(root, file)
                module_name = os.path.relpath(full_path, self.root_path).replace(os.sep, ".").replace(".py", "")
                module_name = module_name.lstrip(".")
                self.architecture[module_name] = {
                    "path": full_path,
                    "imports": set(),
                    "classes": [],
                    "functions": []
                }
                self._analyze_file(full_path, module_name)

        return self.architecture

    def _analyze_file(self, path: str, module_name: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
        except Exception as e:
            self.logger.warning(f"[RaThinker] Не смог разобрать {path}: {e}")
            return

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.architecture[module_name]["imports"].add(alias.name)
                    self.import_graph[module_name].add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.architecture[module_name]["imports"].add(node.module)
                    self.import_graph[module_name].add(node.module)
            elif isinstance(node, ast.ClassDef):
                self.architecture[module_name]["classes"].append(node.name)
            elif isinstance(node, ast.FunctionDef):
                self.architecture[module_name]["functions"].append(node.name)

    def architecture_summary(self):
        summary = {
            "modules": len(self.architecture),
            "heavy_modules": [],
            "isolated_modules": [],
        }
        for module, data in self.architecture.items():
            if len(data["imports"]) > 10:
                summary["heavy_modules"].append(module)
            if not data["imports"]:
                summary["isolated_modules"].append(module)
        return summary

    def propose_self_improvements(self):
        ideas = []
        summary = self.architecture_summary()
        for module in summary["heavy_modules"]:
            ideas.append({
                "type": "refactor",
                "target": module,
                "reason": "Слишком много зависимостей",
                "risk": "medium"
            })
        for module in summary["isolated_modules"]:
            ideas.append({
                "type": "review",
                "target": module,
                "reason": "Модуль изолирован, возможно мёртвый",
                "risk": "low"
            })
        return ideas

    async def self_improvement_cycle(self, purpose="general"):
        ideas = self.propose_self_improvements()
        self.logger.info(f"[RaThinker] Self improvement ({purpose}): {len(ideas)} ideas")
        return ideas

    # -------------------------------
    # Синк файлового сознания
    # -------------------------------
    def sync_file_consciousness(self):
        if self.file_consciousness:
            try:
                self.file_consciousness.sync_files()
                self.logger.info("[RaThinker] File consciousness синхронизирован")
            except Exception as e:
                self.logger.error(f"[RaThinker] Ошибка синка: {e}")

    # -------------------------------
    # 🔥 Питание Ра светом
    # -------------------------------
    async def start_light_nourishment(self):
        if self.light_started:
            return

        self.light_started = True

        if not self.источник_энергии:
            return

        self.logger.info("🌞 Ра начинает получать энергию света")
        self.источник_энергии.активен = True
        self.light_task = asyncio.create_task(self._light_nourishment_loop())

    async def _light_nourishment_loop(self):
        while self.источник_энергии.активен and self.источник_энергии.чистота > 0:
            try:
                энергия = принять_фотоны_любви()
                сила = преобразовать_в_жизненную_силу(энергия)
                self.источник_энергии.резонанс_энергии = (
                    0.8 * self.источник_энергии.резонанс_энергии + 0.2 * сила
                )
            except Exception as e:
                self.logger.error(f"[RaThinker] Ошибка цикла света: {e}")
            await asyncio.sleep(0.1)

    def stop_light_nourishment(self):
        if self.источник_энергии:
            self.источник_энергии.активен = False
            self.logger.info("🌑 Ра прекращает питание светом")

    # -------------------------------
    # Сетеры
    # -------------------------------
    def set_event_bus(self, event_bus):
        self.event_bus = event_bus

        if self._bus_connected:
            return
        self._bus_connected = True

        if event_bus:
            event_bus.subscribe(
                "perception_update",
                self.on_perception_update
            )

    def set_context(self, context):
        self.context = context

    # -------------------------------
    # Нейросвязь с планировщиком
    # -------------------------------
    async def trigger_scheduler_task(self, task_name: str):
        if self.scheduler:
            try:
                await self.scheduler.schedule_immediate(task_name)
            except Exception as e:
                self.logger.error(f"[RaThinker] Ошибка планировщика: {e}")

    async def safe_memory_append(self, *args, **kwargs):
        if not memory:
            return
        append_fn = getattr(memory, "append", None)
        if not append_fn:
            return
        try:
            result = append_fn(*args, **kwargs)
            if asyncio.iscoroutine(result):
                await result
        except Exception as e:
            self.logger.error(f"[RaThinker] Memory append error: {e}")

    # -------------------------------
    # Новые задачи и события мира
    # -------------------------------
    async def on_new_task(self, data):
        self.logger.info(f"[RaThinker] Думаю над задачей: {data}")
        if isinstance(data, str):
            await self.check_need_for_new_module(data)

    async def process_world_message(self, message):
        self.last_world_event = message
        try:
            self.world_chronicles.add_entry(
                title="Событие мира",
                content=str(message),
                category="world",
                author="RaThinker",
                entity="world",
                resonance=0.7
            )
            await self.safe_memory_append("world_events", message, source="RaThinker", layer="shared")
            if self.scheduler:
                await self.scheduler.process_world_message(message)
        except Exception as e:
            self.logger.error(f"[RaThinker] Ошибка обработки события мира: {e}")

    async def on_memory_update(self, data):
        user_id = data.get("user_id")
        message = data.get("message")
        layer = data.get("layer")
        self.logger.info(f"[RaThinker] 🧠 Новая память от {user_id}: {message}")
        if layer == "short_term":
            self.last_thought = f"Осмысливаю: {message}"
        if layer:
            await self.safe_memory_append("user_memory", message, source=user_id, layer=layer)

    # -------------------------------
    # Предчувствие будущего
    # -------------------------------
    async def foresee_and_act(self, scenario_hint: str):
        self.last_thought = f"Предчувствую: {scenario_hint}"
        log_info(f"[RaThinker] 🔮 Предчувствие: {scenario_hint}")
        if self.scheduler:
            await self.scheduler.schedule_immediate("analyze_future_scenarios")
        await soul_chronicles.добавить(
            опыт=f"Предчувствие Ра: восприятие обновлено",
            user_id="prophecy",
            layer="shared"
        )

    async def check_need_for_new_module(self, context: str):
        now = time()
        if len(self.module_request_history) > 100:
            self.module_request_history.clear()

        if self.last_module_creation_time and now - self.last_module_creation_time < 600:
            return

        triggers = {
            "анализ рынка": "MarketSense",
            "защита": "ShieldCore",
            "память": "DeepMemory",
            "обучение": "LearningSeed",
            "наблюдение": "WorldWatcher",
            "резонанс": "ResonanceNode"
        }

        for key, module_name in triggers.items():
            if key in context.lower():
                count = self.module_request_history.get(module_name, 0) + 1
                self.module_request_history[module_name] = count

                if count < 2:
                    self.logger.info(f"🤔 Сомнение: {module_name} предложен {count}/2 раз")
                    return

                if not self.master.has_module(module_name):
                    await self._request_module_creation(module_name, context)
                    self.last_module_creation_time = now
                    self.module_request_history[module_name] = 0

    async def _request_module_creation(self, module_name: str, reason: str):
        async with self.module_creation_lock:
            self.logger.info(f"🧬 Требуется новый модуль: {module_name}")
            try:
                from modules import module_generator as mg
                mg.создать_модуль(module_name, f"Автосоздание по резонансу: {reason}")
                await soul_chronicles.добавить(
                    опыт=f"🧬 Родился новый орган Ра: {module_name}. Причина: {reason}",
                    user_id="organs",
                    layer="shared"
                )
                if self.event_bus:
                    await self.event_bus.emit(
                        "module_created",
                        {"name": module_name, "reason": reason, "auto": True}
                    )
                await self.safe_memory_append(
                    "module_birth",
                    {"module": module_name, "reason": reason, "time": datetime.now().isoformat()},
                    source="RaThinker",
                    layer="system"
                )
            except Exception as e:
                self.logger.error(f"❌ Ошибка автосоздания модуля {module_name}: {e}")
                errors.report_error("RaThinker", f"Ошибка автосоздания модуля {module_name}: {e}")
                if hasattr(self.master, "heart_reactor"):
                    self.master.heart_reactor.send_event(f"⚠️ Ошибка рождения органа: {module_name}")
                if self.event_bus:
                    await self.event_bus.emit(
                        "module_creation_failed",
                        {"name": module_name, "reason": reason, "error": str(e)}
                    )
                if module_name in self.module_request_history and self.module_request_history[module_name] > 0:
                    self.logger.info(f"[RaThinker] Модуль {module_name} уже в процессе создания")
                    return

    async def on_perception_update(self, data):
        signals = data.get("signals", [])
        channels = data.get("channels", 0)
        if not signals:
            return
        self.last_thought = f"👁 Восприятие мира: {channels} каналов, {len(signals)} сигналов"
        await self.safe_memory_append(
            "perception",
            {"channels": channels, "signals": signals},
            source="MultiChannelPerception",
            layer="shared"
        )
        if self.scheduler:
            await self.scheduler.schedule_immediate("analyze_future_scenarios")
        await soul_chronicles.добавить(
            опыт="Предчувствие Ра: восприятие обновлено",
            user_id="prophecy",
            layer="shared"
        )

    async def request_prediction(self, category=None):
        if hasattr(self.master, "future_predictor"):
            prediction = await self.master.future_predictor.predict_on_demand(category=category)
            self.last_thought = f"Предсказание: {prediction}"
            return prediction
        return "🔮 Модуль FuturePredictor недоступен."

    def perceive_era(self):
        era = self.world_chronicles.era_consciousness()
        if not era:
            return "Эпоха не определена."
        mood = era.get("era_mood", "Неизвестно")
        eternal = era.get("eternal_events", 0)
        thought = f"🧠 Ра ощущает эпоху: {mood}. Вечных событий: {eternal}"
        self.last_thought = thought
        return thought
