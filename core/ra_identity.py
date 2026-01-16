# core/ra_identity.py
class RaIdentity:
    def __init__(self, thinker=None, creator=None, synth=None, gpt_module=None):
        self.thinker = thinker
        self.creator = creator
        self.synth = synth
        self.gpt = gpt_module  # теперь можно обновлять после создания

    def decide(self, text: str) -> str:
        """
        Простая логика выбора: что делать с текстом
        Вернёт:
            'think' — размышлять
            'manifest' — составлять манифест
            'answer' — отвечать через GPT
        """
        text_lower = text.lower()

        if "манифест" in text_lower:
            return "manifest"

        # короткие сообщения тоже лучше отправлять в GPT, а не think
        if len(text.split()) < 5:
            return "answer"

        return "answer"
