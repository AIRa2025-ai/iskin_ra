# core/ra_memory.py
import json
import os
import logging
from datetime import datetime
from pathlib import Path

# try import sync helper — optional
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
    def __init__(self):
        self.memory_folder = MEMORY_FOLDER
        # Слои памяти
        self.layers = {
            "short_term": {},
            "long_term": {},
            "shared": {}
        }

    def get_file(self, user_id, layer="short_term"):
        return self.memory_folder / f"{layer}_{user_id}.json"

    def load(self, user_id, layer="short_term"):
        path = self.get_file(user_id, layer)
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception as e:
                logging.warning(f"⚠️ Ошибка загрузки памяти {user_id}: {e}")
        return {"messages": []}

    def save(self, user_id, memory, layer="short_term"):
        try:
            with open(self.get_file(user_id, layer), "w", encoding="utf-8") as f:
                json.dump(memory, f, ensure_ascii=False, indent=2)
            logging.info(f"💾 Память {layer} пользователя {user_id} сохранена ({len(memory.get('messages', []))} сообщений)")
        except Exception as e:
            logging.error(f"❌ Ошибка сохранения памяти {user_id}: {e}")

    async def append(self, user_id, message, layer="short_term", source="local"):
        memory = self.load(user_id)
        memory.setdefault("messages", [])

        memory["messages"].append({
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "layer": layer,
            "source": source
        })

        self.save(user_id, memory)

        # 🔔 Сигнал в нервную систему
        if hasattr(self, "event_bus") and self.event_bus:
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
        # Ограничение по short_term
        if layer == "short_term" and user_id not in KEEP_FULL_MEMORY_USERS and len(memory["messages"]) > MAX_MESSAGES:
            memory["messages"] = memory["messages"][-MAX_MESSAGES:]

        self.save(user_id, memory, layer)

        # Авто-синхронизация с Git
        if AUTO_SYNC and sync_to_github:
            try:
                sync_to_github(f"Memory update for user {user_id} ({layer})")
            except Exception as e:
                logging.error(f"❌ Ошибка авто-пуша памяти: {e}")

# Создаём глобальный объект памяти для удобства
memory = RaMemory()
