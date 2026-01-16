# modules/__init__.py
from core.identity import RaIdentity

self.identity = RaIdentity(
    thinker=self.thinker,
    creator=self.creator,
    synth=self.synth,
    gpt_module=self.gpt_module
)

if self.thinker:
    self.identity.thinker_context = getattr(self.thinker, "rasvet_context", None)
