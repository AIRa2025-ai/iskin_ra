class RaPsychologist:
    """
    Чувствует боль людей и эмоциональную перегрузку мира
    """

    pain_words = ["боль", "страх", "депрессия", "одиночество", "ужас"]

    def analyze(self, text: str):
        pain = sum(text.lower().count(w) for w in self.pain_words)
        if pain >= 2:
            return {
                "priority": "high",
                "message": "Обнаружена боль людей — требуется мягкая реакция"
            }
        return None
