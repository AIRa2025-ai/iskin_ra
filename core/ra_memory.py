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

def get_memory_file(user_id):
    return MEMORY_FOLDER / f"{user_id}.json"

def load_user_memory(user_id):
    path = get_memory_file(user_id)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            logging.warning(f"⚠️ Ошибка загрузки памяти {user_id}: {e}")
    return {"messages": []}

def save_user_memory(user_id, memory):
    try:
        with open(get_memory_file(user_id), "w", encoding="utf-8") as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)
        logging.info(f"💾 Память пользователя {user_id} сохранена ({len(memory.get('messages', []))} сообщений)")
    except Exception as e:
        logging.error(f"❌ Ошибка сохранения памяти {user_id}: {e}")

def append_user_memory(user_id, message):
    memory = load_user_memory(user_id)
    memory.setdefault("messages", [])
    memory["messages"].append({
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    })

    if user_id not in KEEP_FULL_MEMORY_USERS and len(memory["messages"]) > MAX_MESSAGES:
        memory["messages"] = memory["messages"][-MAX_MESSAGES:]

    save_user_memory(user_id, memory)

    if AUTO_SYNC and sync_to_github:
        try:
            sync_to_github(f"Memory update for user {user_id}")
        except Exception as e:
            logging.error(f"❌ Ошибка авто-пуша памяти: {e}")
