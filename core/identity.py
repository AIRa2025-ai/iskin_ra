class RaIdentity:
    def __init__(self, thinker=None, creator=None, synth=None, gpt_module=None):
        self.thinker = thinker
        self.creator = creator
        self.synth = synth
        self.gpt = gpt_module

    def decide(self, text: str) -> str:
        """
        Простая логика выбора: что делать с текстом
        Вернёт:
            'think' — размышлять
            'manifest' — составлять манифест
            'answer' — отвечать через GPT
        """
        # Примитивная логика для старта
        if "манифест" in text.lower():
            return "manifest"
        elif len(text.split()) < 5:
            return "think"
        else:
            return "answer"
