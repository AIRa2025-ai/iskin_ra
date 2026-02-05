class RaWarPeaceObserver:
    watch_words = ["война", "ракета", "мир", "перемирие", "конфликт"]

    def observe(self, text: str):
        hits = [w for w in self.watch_words if w in text.lower()]
        if hits:
            return {
                "priority": "critical",
                "message": f"Глобальный сигнал: {', '.join(hits)}"
            }
        return None
