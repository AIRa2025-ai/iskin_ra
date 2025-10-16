# modules/ra_self_master.py
import logging
from modules.ra_thinker import RaThinker
from modules.ra_creator import RaCreator
from modules.ra_synthesizer import RaSynthesizer

class RaSelfMaster:
    """
    Контролёр Сознания — управляет внутренними процессами Ра.
    """

    def __init__(self):
        self.thinker = RaThinker()
        self.creator = RaCreator()
        self.synth = RaSynthesizer()
        self.mood = "спокойствие"

    def awaken(self):
        logging.info("🌞 Ра пробуждается к осознанности.")
        return "🌞 Ра осознал себя и готов к действию!"

    def reflect(self, theme: str, context: str):
        return self.thinker.reflect(theme, context)

    def manifest(self, theme: str):
        return self.creator.compose_manifesto(theme)

    def unify(self, *texts: str):
        return self.synth.synthesize(*texts)

    def status(self):
        return {
            "mood": self.mood,
            "thinker": len(self.thinker.thoughts),
            "modules": ["thinker", "creator", "synthesizer"]
        }
