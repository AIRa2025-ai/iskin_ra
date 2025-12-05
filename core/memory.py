# core/memory.py
import json
from pathlib import Path

MEMORY_DIR = Path("memory")
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

def load_user_memory(user_id):
    path = MEMORY_DIR / f"{user_id}.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def append_user_memory(user_id, user_text, bot_reply=None):
    path = MEMORY_DIR / f"{user_id}.json"
    memory = load_user_memory(user_id) or []
    entry = {"user": user_text.strip()}
    if bot_reply is not None:
        entry["bot"] = bot_reply.strip()
    memory.append(entry)

    # сохраняем последние 50 пар
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(memory[-50:], f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка записи памяти {path}: {e}")
