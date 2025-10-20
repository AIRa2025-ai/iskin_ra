#core/ra_memory.py
import json
import os
import logging
from datetime import datetime
from utils.memory_sync import sync_to_github

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Папка для памяти пользователей
MEMORY_FOLDER = os.getenv("RA_MEMORY_FOLDER", "memory")
os.makedirs(MEMORY_FOLDER, exist_ok=True)

AUTO_SYNC = True  # авто-пуш на Git
MAX_MESSAGES = 200  # лимит сообщений для большинства пользователей
KEEP_FULL_MEMORY_USERS = [5694569448, 6300409407]  # сюда твой ID и ID Миланы

def get_memory_file(user_id):
    """Путь к файлу памяти конкретного пользователя"""
    return os.path.join(MEMORY_FOLDER, f"{user_id}.json")

def load_user_memory(user_id):
    """Загружает память пользователя"""
    path = get_memory_file(user_id)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.warning(f"⚠️ Ошибка загрузки памяти {user_id}: {e}")
    return {"messages": []}

def save_user_memory(user_id, memory):
    """Сохраняет память пользователя"""
    try:
        with open(get_memory_file(user_id), "w", encoding="utf-8") as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)
        logging.info(f"💾 Память пользователя {user_id} сохранена ({len(memory['messages'])} сообщений)")
    except Exception as e:
        logging.error(f"❌ Ошибка сохранения памяти {user_id}: {e}")

def append_user_memory(user_id, message):
    """Добавляет сообщение пользователя в память"""
    memory = load_user_memory(user_id)
    memory.setdefault("messages", [])
    memory["messages"].append({
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    })

    # Если пользователь не в списке KEEP_FULL_MEMORY_USERS, применяем лимит
    if user_id not in KEEP_FULL_MEMORY_USERS and len(memory["messages"]) > MAX_MESSAGES:
        memory["messages"] = memory["messages"][-MAX_MESSAGES:]

    save_user_memory(user_id, memory)

    # Авто-пуш на Git
    if AUTO_SYNC:
        try:
            sync_to_github(f"Memory update for user {user_id}")
        except Exception as e:
            logging.error(f"❌ Ошибка авто-пуша памяти: {e}")
