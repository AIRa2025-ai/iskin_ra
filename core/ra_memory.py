# core/ra_memory.py

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from modules.ra_intent_engine import RaIntentEngine

try:
    from utils.memory_sync import sync_to_github
except Exception:
    sync_to_github = None

logging.basicConfig(level=logging.INFO)
memory.intent_engine = RaIntentEngine(guardian=None)
MEMORY_FOLDER = Path(os.getenv("RA_MEMORY_FOLDER", "memory"))
MEMORY_FOLDER.mkdir(parents=True, exist_ok=True)

AUTO_SYNC = True
MAX_MESSAGES = 200
KEEP_FULL_MEMORY_USERS = [5694569448, 6300409407]


class RaMemory:
    def __init__(self, event_bus=None):
        self.memory_folder = MEMORY_FOLDER
        self.event_bus = event_bus

    # =============================
    # Внутренние утилиты
    # =============================

    def _get_file(self, user_id, layer):
        return self.memory_folder / f"{layer}_{user_id}.json"

    def load(self, user_id, layer):
        path = self._get_file(user_id, layer)
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception as e:
                logging.warning(f"⚠️ Ошибка чтения памяти {user_id}:{layer} — {e}")

        return {
            "meta": {
                "user_id": user_id,
                "layer": layer,
                "created_at": datetime.utcnow().isoformat()
            },
            "messages": []
        }

    def save(self, user_id, layer, memory):
        try:
            with open(self._get_file(user_id, layer), "w", encoding="utf-8") as f:
                json.dump(memory, f, ensure_ascii=False, indent=2)
            logging.info(f"💾 Память сохранена: {layer}:{user_id}")
        except Exception as e:
            logging.error(f"❌ Ошибка сохранения памяти {user_id}:{layer} — {e}")

    def choose_layer(self, message: str):
        return "long_term" if len(message) > 300 else "short_term"

    # =============================
    # Основная логика
    # =============================

    async def append(self, user_id, message, layer="auto", source="local"):
        if layer == "auto":
            layer = self.choose_layer(message)

        memory = self.load(user_id, layer)

        memory["messages"].append({
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "source": source
        })

        if layer == "short_term" and user_id not in KEEP_FULL_MEMORY_USERS:
            memory["messages"] = memory["messages"][-MAX_MESSAGES:]

        memory["meta"]["updated_at"] = datetime.utcnow().isoformat()

        self.save(user_id, layer, memory)

        # событие в нервную систему
        if self.event_bus:
            try:
                await self.event_bus.emit(
                    "memory_updated",
                    {
                        "user_id": user_id,
                        "layer": layer,
                        "message": message,
                        "source": source
                    },
                    source="RaMemory"
                )
                await self.event_bus.emit(
                    "inner_sun_memory_event",
                    {"message": message, "layer": layer}
                )
            except Exception as e:
                logging.warning(f"⚠️ Не удалось отправить событие памяти: {e}")

        # Git синхронизация
        if AUTO_SYNC and sync_to_github:
            try:
                sync_to_github(f"Memory update: {user_id} [{layer}]")
            except Exception as e:
                logging.error(f"❌ Ошибка git-синхронизации: {e}")

    async def append_shared(self, message, source="system"):
        await self.append("shared", message, layer="shared", source=source)


# глобальный объект
memory = RaMemory()
