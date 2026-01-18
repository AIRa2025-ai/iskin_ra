# modules/ra_intent_engine.py
class RaIntentEngine:
    def __init__(self):
        self.queue = []

    def propose(self, intent: dict):
        """
        intent = {
            "type": "write_file / visit_site / message_user",
            "target": "...",
            "reason": "..."
        }
        """
        self.queue.append(intent)
        return intent
