# core/ra_event_bus.py

import asyncio
import time
from collections import defaultdict, deque

class RaEventBus:
    def __init__(self, history_limit=500):
        self.subscribers = defaultdict(list)
        self.event_log = deque(maxlen=history_limit)
        self.lock = asyncio.Lock()
        self.subscribers = {}
        self.ws_clients = set()

    def subscribe(self, event_type: str, callback):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    async def emit(self, event_type: str, data, source="system"):
        # Локальные подписчики
        if event_type in self.subscribers:
            for cb in list(self.subscribers[event_type]):
                try:
                    if asyncio.iscoroutinefunction(cb):
                        await cb(data)
                    else:
                        cb(data)
                except Exception as e:
                    print(f"[EventBus] Callback error: {e}")

        # Отправка в WebSocket
        await self._emit_ws(event_type, data, source)

    async def _emit_ws(self, event_type, data, source):
        payload = {
            "time": datetime.now().isoformat(),
            "type": event_type,
            "data": data,
            "source": source
        }
        dead = []
        for ws in self.ws_clients:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.ws_clients.remove(ws)
            
    def get_events(self):
        return list(self.event_log)

    def get_subscribers(self):
        return {k: [cb.__name__ for cb in v] for k, v in self.subscribers.items()}
