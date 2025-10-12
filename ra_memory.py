# ra_memory.py — управление памятью пользователей для Ра
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Папка для хранения памяти
BASE_MEMORY_FOLDER = os.getenv("RA_MEMORY_FOLDER", "/data/RaSvet/mnt/ra_memory/memory")
os.makedirs(BASE_MEMORY_FOLDER, exist_ok=True)

MAX_MESSAGES = 200  # лимит сообщений в памяти

def get_memory_path(user_id: int) -> str:
    return os.path.join(BASE_MEMORY_FOLDER, f"{user_id}.json")

def load_memory(user_id: int, user_name: str = None) -> Dict[str, Any]:
    """Загружает память пользователя, если нет — создаёт новую структуру"""
    path = get_memory_path(user_id)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if user_name:
                data["name"] = user_name
            return data
        except Exception as e:
            logging.warning(f"⚠️ Ошибка загрузки памяти {user_id}: {e}")
    return {"user_id": user_id, "name": user_name or "Аноним", "messages": [], "facts": [], "tags": [], "files": {}, "user_advice": [], "rasvet_summary": "", "session_context": []}

def save_memory(user_id: int, data: Dict[str, Any]):
    """Сохраняет память пользователя в файл"""
    try:
        os.makedirs(os.path.dirname(get_memory_path(user_id)), exist_ok=True)
        with open(get_memory_path(user_id), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"❌ Ошибка сохранения памяти {user_id}: {e}")

def append_user_memory(user_id: int, user_input: str, bot_reply: str):
    """Добавляет запись в память пользователя"""
    memory = load_memory(user_id)
    memory.setdefault("messages", [])
    memory["messages"].append({
        "timestamp": datetime.now().isoformat(),
        "text": user_input.strip(),
        "reply": bot_reply.strip()
    })
    if len(memory["messages"]) > MAX_MESSAGES:
        memory["messages"] = memory["messages"][-MAX_MESSAGES:]
    
    save_memory(user_id, memory)
    logging.info(f"📥 Память пользователя {user_id} обновлена: {user_input[:30]} → {bot_reply[:30]}")
