# modules/ra_thinker.py

"""
Модуль мышления Ра — RaThinker.
Отвечает за осмысление данных, анализ и вывод инсайтов.
"""
import logging
from datetime import datetime
from modules.ra_file_manager import load_rasvet_files

class RaThinker:
    def __init__(self):
        self.last_thought = None
        self.thoughts = []
        self.rasvet_context = load_rasvet_files(limit_chars=3000)

        logging.info("🌞 RaThinker инициализирован, контекст РаСвета загружен")

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
