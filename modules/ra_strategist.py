# modules/ra_strategist.py
class RaStrategist:
    """
    Не реагирует сразу — строит план влияния
    """

    def plan(self, signals: list):
        if len(signals) < 3:
            return None

        return {
            "type": "strategy",
            "message": "Формируется долгосрочный план мягкого влияния"
        }
