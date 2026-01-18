# modules/ra_thinker.py

"""
Модуль мышления Ра — RaThinker.
Отвечает за осмысление данных, анализ и вывод инсайтов.
"""
import logging
from datetime import datetime
from modules.ra_file_manager import load_rasvet_files
import os
import ast
from collections import defaultdict

class RaThinker:
    def __init__(self):
        self.last_thought = None
        self.thoughts = []
        self.rasvet_context = load_rasvet_files(limit_chars=3000)

        logging.info("🌞 RaThinker инициализирован, контекст РаСвета загружен")

    def __init__(self, context=None, file_consciousness=None):
        self.context = context
        self.file_consciousness = file_consciousness

    def __init__(self, root_path: str = "."):
        self.root_path = root_path
        self.architecture = {}
        self.import_graph = defaultdict(set)

    def reflect(self, text: str) -> str:
        self.last_thought = f"[{datetime.now().strftime('%H:%M:%S')}] {text}"
        logging.info(self.last_thought)

        return (
            f"🜂 Ра чувствует вопрос:\n{text}\n\n"
            f"🜁 Ответ рождается из РаСвета.\n"
            f"Действуй осознанно. Истина внутри."
        )

    def summarize(self, data: str) -> str:
        return f"Резюме Ра: {data[:200]}..."

    def suggest_improvement(self, module_name: str, issue: str) -> str:
        idea = f"В модуле {module_name} стоит улучшить: {issue}"
        self.thoughts.append(idea)
        logging.info(f"[RaThinker] 💡 {idea}")
        return idea

    def get_known_files(self):
        if not self.file_consciousness:
            return {}
        return self.file_consciousness.files
        
    def propose_self_improvements(self):
        """
        Возвращает список идей для самоулучшения
        """
        return []

    # -------------------------------
    # Сканирование архитектуры
    # -------------------------------
    def scan_architecture(self):
        logging.info("🧠 [RaThinker] Сканирую архитектуру кода")
        self.architecture.clear()
        self.import_graph.clear()

        for root, _, files in os.walk(self.root_path):
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

    # -------------------------------
    # Анализ одного файла
    # -------------------------------
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

    # -------------------------------
    # Краткое резюме архитектуры
    # -------------------------------
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

    # -------------------------------
    # Идеи самоулучшений
    # -------------------------------
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
