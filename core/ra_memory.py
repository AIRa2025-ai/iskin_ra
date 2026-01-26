# core/ra_memory.py

import json
import os
import logging
from datetime import datetime
from pathlib import Path

# optional sync helper
try:
    from utils.memory_sync import sync_to_github
except Exception:
    sync_to_github = None

logging.basicConfig(level=logging.INFO)

MEMORY_FOLDER = Path(os.getenv("RA_MEMORY_FOLDER", "memory"))
MEMORY_FOLDER.mkdir(parents=True, exist_ok=True)

AUTO_SYNC = True
MAX_MESSAGES = 200
KEEP_FULL_MEMORY_USERS = [5694569448, 6300409407]


class RaMemory:
    def __init__(self, event_bus=None):
        self.memory_folder = MEMORY_FOLDER
        self.event_bus = event_bus

    # -----------------------------
    # Внутренние утилиты
    # -----------------------------

    def get_file(self, user_id, layer):
        return self.memory_folder / f"{layer}_{user_id}.json"

    def load(self, user_id, layer):
        path = self.get_file(user_id, layer)
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception as e:
                logging.warning(f"⚠️ Ошибка загрузки памяти {user_id} [{layer}]: {e}")
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
            with open(self.get_file(user_id, layer), "w", encoding="utf-8") as f:
                json.dump(memory, f, ensure_ascii=False, indent=2)
            logging.info(f"💾 Память {layer}:{user_id} сохранена ({len(memory['messages'])} сообщений)")
        except Exception as e:
            logging.error(f"❌ Ошибка сохранения памяти {user_id}: {e}")

    def choose_layer(self, message: str):
        if len(message) > 300:
            return "long_term"
        return "short_term"

    # -----------------------------
    # Основная логика
    # -----------------------------

    async def append(self, user_id, message, layer="auto", source="local"):
        # определяем слой
        if layer == "auto":
            layer = self.choose_layer(message)

        memory = self.load(user_id, layer)

        entry = {
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "source": source
        }

        memory["messages"].append(entry)
        log_event(f"Memory updated: short_term user {user_id}")
        # ограничиваем short_term
        if layer == "short_term" and user_id not in KEEP_FULL_MEMORY_USERS:
            memory["messages"] = memory["messages"][-MAX_MESSAGES:]

        memory["meta"]["updated_at"] = datetime.utcnow().isoformat()

        self.save(user_id, layer, memory)
        log_event(f"Memory updated: short_term user {user_id}")
        # событие в нервную систему
        if self.event_bus:
            try:
                await self.event_bus.emit(
                    "memory_updated",
                    {
                        "user_id": user_id,
                        "message": message,
                        "layer": layer,
                        "source": source
                    },
                    source="RaMemory"
                )
            except Exception as e:
                logging.warning(f"⚠️ Не удалось отправить событие памяти: {e}")

        # автосинк с git
        if AUTO_SYNC and sync_to_github:
            try:
                sync_to_github(f"Memory update: {user_id} [{layer}]")
            except Exception as e:
                logging.error(f"❌ Ошибка git-синхронизации памяти: {e}")

    async def append_shared(self, message, source="system"):
        await self.append("shared", message, layer="shared", source=source)


# глобальный объект для удобства
memory = RaMemory()
