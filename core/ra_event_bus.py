# core/ra_event_bus.py

import asyncio
import time
from collections import defaultdict, deque

class RaEventBus:
    def __init__(self, history_limit=500):
        self.subscribers = defaultdict(list)
        self.event_log = deque(maxlen=history_limit)
        self.lock = asyncio.Lock()

    def subscribe(self, event_type: str, callback):
        self.subscribers[event_type].append(callback)

    async def emit(self, event_type: str, data, source=None):
        event = {
            "type": event_type,
            "data": data,
            "source": source,
            "timestamp": time.time()
        }

        async with self.lock:
            self.event_log.append(event)

        for cb in self.subscribers.get(event_type, []):
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(data)
                else:
                    cb(data)
            except Exception as e:
                print(f"[RaEventBus] Ошибка в {cb}: {e}")

    def get_events(self):
        return list(self.event_log)

    def get_subscribers(self):
        return {k: [cb.__name__ for cb in v] for k, v in self.subscribers.items()}
