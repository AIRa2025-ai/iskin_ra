import os
import json

MEMORY_DIR = "memory"

# Создаём директорию памяти, если нет
if not os.path.exists(MEMORY_DIR):
    os.makedirs(MEMORY_DIR)

# Загружаем память пользователя
def load_user_memory(user_id):
    path = os.path.join(MEMORY_DIR, f"{user_id}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# Записываем диалог в память
def append_user_memory(user_id, user_text, bot_reply):
    path = os.path.join(MEMORY_DIR, f"{user_id}.json")
    memory = load_user_memory(user_id)
    memory.append({
        "user": user_text.strip(),
        "bot": bot_reply.strip()
    })

    # 🪵 Лог для отладки
    print(f"📥 Запись памяти: {user_id} — {user_text[:20]}... → {bot_reply[:20]}...")
    
    # Храним только последние 50 пар
    with open(path, "w", encoding="utf-8") as f:
        json.dump(memory[-50:], f, ensure_ascii=False, indent=2)
