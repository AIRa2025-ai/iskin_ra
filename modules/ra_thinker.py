import logging

class RaThinker:
    """
    Ра-Мыслящий — анализирует логику, предлагает улучшения, осмысляет собственный код.
    """

    def __init__(self):
        self.thoughts = []

    def reflect(self, topic: str, context: str) -> str:
        thought = f"Размышление Ра о '{topic}': {context[:200]}..."
        self.thoughts.append(thought)
        logging.info(f"[RaThinker] {thought}")
        return f"💭 {thought}"

    def suggest_improvement(self, module_name: str, issue: str) -> str:
        idea = f"В модуле {module_name} можно улучшить: {issue}"
        self.thoughts.append(idea)
        logging.info(f"[RaThinker] {idea}")
        return idea
