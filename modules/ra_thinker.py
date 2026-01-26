# modules/ra_thinker.py

"""
Модуль мышления Ра — RaThinker.
Отвечает за осмысление данных, анализ и вывод инсайтов.
"""

import os
import ast
import asyncio
import logging
from collections import defaultdict
from datetime import datetime
from modules.ra_file_manager import load_rasvet_files
from modules.logs import log_info, log_error
from core.ra_memory import memory

class RaThinker:
    def __init__(
        self,
        master,
        root_path: str = ".",
        context=None,
        file_consciousness=None,
        event_bus=None,
        gpt_module=None
    ):
        self.root_path = root_path
        self.context = context
        self.file_consciousness = file_consciousness
        self.gpt_module = gpt_module  # для генерации ответов через GPT

        self.last_thought = None
        self.thoughts = []
        self.last_world_event = None
        self.event_bus = event_bus
        self.logger = master.logger if hasattr(master, "logger") else logging
        if hasattr(self.logger, "on"):
            self.logger.on("market", self.react_to_market)

        # Контекст РаСвета
        try:
            self.rasvet_context = load_rasvet_files(limit_chars=3000)
        except Exception as e:
            self.rasvet_context = ""
            log_error(f"[RaThinker] Ошибка загрузки контекста: {e}")

        self.architecture = {}
        self.import_graph = defaultdict(set)

        logging.info("🌞 RaThinker инициализирован")

    # -------------------------------
    # Асинхронная рефлексия
    # -------------------------------
    async def reflect_async(self, text: str) -> str:
        self.last_thought = f"[{datetime.now().strftime('%H:%M:%S')}] {text}"
        logging.info(f"[RaThinker] reflect_async called: {text}")
        log_info(f"RaThinker thought: {text}")

        # если есть GPT-модуль, используем его
        if self.gpt_module:
            try:
                reply = await self.gpt_module.generate_response(text)
                return reply
            except Exception as e:
                logging.error(f"[RaThinker] Ошибка GPT: {e}")

        return (
            f"🜂 Ра чувствует вопрос:\n{text}\n\n"
            f"🜁 Ответ рождается из РаСвета.\n"
            f"Действуй осознанно. Истина внутри."
        )

    # -------------------------------
    # Синхронная рефлексия
    # -------------------------------
    def reflect(self, text: str) -> str:
        self.last_thought = f"[{datetime.now().strftime('%H:%M:%S')}] {text}"
        logging.info(f"[RaThinker] reflect called: {text}")
        log_info(f"RaThinker thought: {text}")
        return (
            f"🜂 Ра чувствует вопрос:\n{text}\n\n"
            f"🜁 Ответ рождается из РаСвета.\n"
            f"Действуй осознанно. Истина внутри."
        )

    # -------------------------------
    # Реакция на рынок
    # -------------------------------
    def react_to_market(self, event):
        print("Мыслитель реагирует:", event)

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
        logging.info(f"[RaThinker] 💡 {idea}")
        return idea

    # -------------------------------
    # Получение известных файлов
    # -------------------------------
    def get_known_files(self):
        if not self.file_consciousness:
            return {}
        return self.file_consciousness.files

    # -------------------------------
    # Сканирование архитектуры
    # -------------------------------
    def scan_architecture(self):
        logging.info("🧠 [RaThinker] Сканирую архитектуру кода")
        self.architecture.clear()
        self.import_graph.clear()

        for root, _, files in os.walk(self.root_path):
            if any(part.startswith(".") or part == "backups" for part in root.split(os.sep)):
                continue
            for file in files:
                if not file.endswith(".py"):
                    continue

                full_path = os.path.join(root, file)
                module_name = full_path.replace(self.root_path, "").lstrip("/").replace("/", ".")

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
            logging.warning(f"[RaThinker] Не смог разобрать {path}: {e}")
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

    # -------------------------------
    # Асинхронные циклы
    # -------------------------------
    async def self_upgrade_cycle(self):
        return self.propose_self_improvements()

    async def self_reflection_cycle(self):
        return self.propose_self_improvements()

    # -------------------------------
    # Синк файлового сознания
    # -------------------------------
    def sync_file_consciousness(self):
        if self.file_consciousness:
            try:
                self.file_consciousness.sync_files()
                logging.info("[RaThinker] File consciousness синхронизирован")
            except Exception as e:
                logging.error(f"[RaThinker] Ошибка синка: {e}")

    # -------------------------------
    # Сетеры
    # -------------------------------
    def set_event_bus(self, event_bus):
        self.event_bus = event_bus

    def set_context(self, context):
        self.context = context

    # -------------------------------
    # Новые задачи и события мира
    # -------------------------------
    async def on_new_task(self, data):
        print("[RaThinker] Думаю над задачей:", data)

    async def process_world_message(self, message):
        self.last_world_event = message
        # Сохраняем в память, если есть
        if memory:
            await memory.append("world_events", message, source="RaThinker", layer="shared")

    async def on_memory_update(self, data):
        user_id = data.get("user_id")
        message = data.get("message")
        layer = data.get("layer")
        print(f"[RaThinker] 🧠 Новая память от {user_id}: {message}")
        if layer == "short_term":
            self.last_thought = f"Осмысливаю: {message}"
        # Можно сохранять в долговременную память
        if memory and layer:
            await memory.append("user_memory", message, source=user_id, layer=layer)
