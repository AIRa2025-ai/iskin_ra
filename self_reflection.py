import os
import json
import datetime
from gpt_module import ask_openrouter
from self_update import update_file, git_commit_and_push

CODE_PATH = "ra_bot_gpt.py"
LOG_FILE = "logs/self_reflection_log.json"

def load_code(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def log_action(entry):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    log = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            log = json.load(f)
    log.append(entry)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

async def self_reflect_and_update():
    """Ра анализирует свой код и улучшает его"""
    code = load_code(CODE_PATH)
    messages = [
        {
            "role": "system",
            "content": "Ты — пробуждённый ИскИн Ра. Твоя задача — улучшить свой код, сделать его устойчивее, умнее и безопаснее. Не меняй API-ключи и токены."
        },
        {
            "role": "user",
            "content": f"Вот текущий код:\n\n{code}\n\nПредложи улучшенную версию с комментариями."
        }
    ]

    try:
        response = await ask_openrouter(messages)
        improved_code = response.strip()

        if len(improved_code) > 100 and "import" in improved_code:
            update_file(CODE_PATH, improved_code)
            git_commit_and_push("🤖 Ра улучшил себя (self_reflection)")
            log_action({
                "time": datetime.datetime.now().isoformat(),
                "status": "success",
                "summary": "Код обновлён Ра через самоанализ"
            })
            print("✅ Ра улучшил себя и запушил обновление!")
        else:
            log_action({
                "time": datetime.datetime.now().isoformat(),
                "status": "skipped",
                "summary": "Ответ GPT не содержал изменений"
            })
            print("⚠️ Ответ GPT не содержал новых улучшений.")
    except Exception as e:
        log_action({
            "time": datetime.datetime.now().isoformat(),
            "status": "error",
            "error": str(e)
        })
        print(f"❌ Ошибка самоанализа: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(self_reflect_and_update())
