# core/ra_identity.py

class RaIdentity:
    """
    Основная сущность Ра — принимает решения о том,
    что делать с входящим текстом: размышлять, составлять манифест или отвечать через GPT.
    """

    def __init__(self, thinker=None, creator=None, synth=None, gpt_module=None):
        self.thinker = thinker
        self.creator = creator
        self.synth = synth
        self.gpt = gpt_module  # теперь можно обновлять после создания

    def decide(self, text: str) -> str:
        """
        Логика выбора действия по тексту.
        Возвращает:
            'think' — размышлять
            'manifest' — составлять манифест
            'answer' — отвечать через GPT
        """
        if not text or not text.strip():
            return "answer"

        text_lower = text.lower()

        # если в тексте есть слово "манифест" — запускаем генерацию манифеста
        if "манифест" in text_lower:
            return "manifest"

        # короткие сообщения (1–4 слова) лучше сразу отправлять GPT
        if len(text.split()) < 5:
            return "answer"

        # длинные тексты можно пропускать через размышление
        if self.thinker:
            return "think"

        # fallback — GPT
        return "answer"
