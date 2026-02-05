class RaProphet:
    """
    Предсказывает будущие тренды на основе сигналов мира
    """

    def predict(self, memory: list):
        if len(memory) < 10:
            return None

        last = " ".join(m["text"] for m in memory[-10:])
        if "война" in last:
            return "Вероятно усиление тревоги и конфликтов"
        if "надежда" in last:
            return "Формируется волна надежды и роста"

        return None
