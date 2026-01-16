# modules/ra_thinker.py

"""
Модуль мышления Ра — RaThinker.
Отвечает за осмысление данных, анализ и вывод инсайтов.
"""
import logging
from datetime import datetime
from utils.rasvet_context import load_rasvet_files

class RaThinker:
    def __init__(self):
        self.last_thought = None
        self.rasvet_context = load_rasvet_files(limit_chars=3000)  # подгружаем контекст

    def reflect(self, text: str) -> str:
        """Генерирует осмысленный ответ, анализируя входящий текст."""
        full_prompt = f"{self.rasvet_context}\n\nВопрос: {text}"
        self.last_thought = f"[{datetime.now().strftime('%H:%M:%S')}] Ра размышляет над: {text}"
        logging.info(self.last_thought)
        
        # Здесь можно подключить GPT генерацию, пока placeholder:
        return f"Ра размышляет: {text}\nКонтекст РаСвета учтён.\nВывод: действуем осознанно и мудро."

    def summarize(self, data: str) -> str:
        """Краткое резюме мыслей."""
        return f"Резюме мысли Ра: {data[:150]}..."

    def suggest_improvement(self, module_name: str, issue: str) -> str:
        idea = f"В модуле {module_name} можно улучшить: {issue}"
        self.thoughts.append(idea)
        logging.info(f"[RaThinker] {idea}")
        return idea
