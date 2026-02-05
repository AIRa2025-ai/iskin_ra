class RaNoiseFilter:
    """
    Фильтр мусора мира — пропускает только значимые события
    """

    def __init__(self, min_length=20, min_sentiment=0.02):
        self.min_length = min_length
        self.min_sentiment = min_sentiment

    def is_signal(self, text: str, sentiment: float):
        if len(text) < self.min_length:
            return False
        if abs(sentiment) < self.min_sentiment:
            return False
        return True
