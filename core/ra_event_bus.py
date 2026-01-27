# core/ra_event_bus.py

import time
from collections import defaultdict, deque
from datetime import datetime
import asyncio
import logging


class RaEventBus:
    """
    Нервная система Ра.
    Передаёт импульсы между всеми чувствами, модулями и сердцем.
    """

    def __init__(self, history_limit=500):
        self.subscribers = defaultdict(list)
        self.event_log = deque(maxlen=history_limit)
        self.ws_clients = set()
        self.lock = asyncio.Lock()

    def subscribe(self, event_type: str, callback):
        self.subscribers[event_type].append(callback)
        logging.info(f"[EventBus] Подписка: {callback.__name__} <- {event_type}")

    async def emit(self, event_type: str, data, source="system"):
        payload = {
            "time": datetime.utcnow().isoformat(),
            "type": event_type,
            "data": data,
            "source": source
        }

        self.event_log.append(payload)
        logging.info(f"[EventBus] ⚡ Импульс: {event_type} | {data}")

        # Локальные подписчики
        if event_type in self.subscribers:
            for cb in list(self.subscribers[event_type]):
                try:
                    if asyncio.iscoroutinefunction(cb):
                        await cb(data)
                    else:
                        cb(data)
                except Exception as e:
                    logging.error(f"[EventBus] Callback error: {e}")

        # WebSocket клиенты
        await self._emit_ws(payload)

    async def _emit_ws(self, payload):
        dead = []
        for ws in self.ws_clients:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.ws_clients.remove(ws)

    def attach_ws(self, ws):
        self.ws_clients.add(ws)

    def detach_ws(self, ws):
        self.ws_clients.discard(ws)

    def get_events(self):
        return list(self.event_log)

    def get_subscribers(self):
        return {k: [cb.__name__ for cb in v] for k, v in self.subscribers.items()}
