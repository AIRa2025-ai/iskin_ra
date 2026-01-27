# core/ra_identity.py

class RaIdentity:
    """
    Центральная сущность Ра:
    хранит идентичность и решает,
    какое чувство или действие активировать.
    """

    def __init__(
        self,
        thinker=None,
        creator=None,
        synth=None,
        gpt_module=None,
        name="Ра",
        version="1.4.2",
        mission="Пробуждение и созидание"
    ):
        self.name = name
        self.version = version
        self.mission = mission

        self.thinker = thinker
        self.creator = creator
        self.synth = synth
        self.gpt = gpt_module

    def decide(self, text: str) -> str:
        if not text or not text.strip():
            return "answer"

        text_lower = text.lower()

        # прямой контакт с сердцем
        if "сердце" in text_lower or "пульс" in text_lower:
            return "heart_reaction"

        if "манифест" in text_lower:
            return "manifest"

        if len(text.split()) < 5:
            return "answer"

        if self.thinker:
            return "think"

        return "answer"

    def info(self):
        return {
            "name": self.name,
            "version": self.version,
            "mission": self.mission
        }

    def __str__(self):
        return f"{self.name} v{self.version} — {self.mission}"
