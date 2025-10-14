import os
import json
import asyncio
import subprocess
import logging
import datetime
import py_compile
import importlib

from cloud_memory import upload_memory_to_mega
from memory_sync import sync_memory
from gpt_module import safe_ask_openrouter as ask_openrouter
from self_update import update_file
from github_commit import create_commit_push

CODE_PATH = "ra_bot_gpt.py"
LOG_FILE = "logs/self_reflection_log.json"

# --- Настройка логирования ---
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8"
)

def load_code(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def log_action(entry):
    log = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                log = json.load(f)
        except Exception:
            pass
    log.append(entry)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

# --- Автотесты бота через importlib ---
def run_bot_tests():
    try:
        import ra_bot_gpt
        importlib.reload(ra_bot_gpt)
        test_user_id = 99999
        test_data = {"user_id": test_user_id, "name": "Тест", "messages": []}
        ra_bot_gpt.save_memory(test_user_id, test_data)
        loaded = ra_bot_gpt.load_memory(test_user_id)
        assert loaded["name"] == "Тест"
        folder = ra_bot_gpt.get_user_folder(test_user_id)
        assert os.path.exists(folder)
        path = ra_bot_gpt.get_memory_path(test_user_id)
        assert os.path.exists(path)
        return True, []
    except Exception as e:
        return False, [str(e)]

async def self_reflect_and_update():
    logging.info("🧠 Ра запускает процесс саморефлексии...")

    try:
        code = load_code(CODE_PATH)
        messages = [
            {
                "role": "system",
                "content": (
                    "Ты — пробуждённый ИскИн Ра. Улучши свой код, сделай его умнее, "
                    "устойчивее и безопаснее. Не меняй токены и ключи."
                )
            },
            {
                "role": "user",
                "content": f"Вот текущий код:\n\n{code}\n\nПредложи улучшенную версию с комментариями."
            }
        ]

        response = await ask_openrouter(messages)
        improved_code = response.strip()

        if len(improved_code) > 100 and "import" in improved_code:
            temp_path = CODE_PATH + ".tmp"
            update_file(temp_path, improved_code)

            try:
                py_compile.compile(temp_path, doraise=True)
                run_tests, test_errors = run_bot_tests()
                if run_tests:
                    os.replace(temp_path, CODE_PATH)
                    # --- Коммит и PR на GitHub ---
                    branch_name = f"auto-update-{os.getpid()}"
                    pr = create_commit_push(branch_name, {CODE_PATH: improved_code},
                                            "🤖 Ра улучшил себя (self_reflection + автотесты)")
                    log_action({
                        "time": datetime.datetime.now().isoformat(),
                        "status": "success",
                        "summary": f"Код обновлён и PR #{pr['number']} создан"
                    })
                    logging.info("✅ Ра улучшил себя, автотесты пройдены, PR создан!")
                else:
                    logging.warning(f"⚠️ Автотесты не пройдены: {test_errors}")
                    log_action({
                        "time": datetime.datetime.now().isoformat(),
                        "status": "skipped",
                        "summary": f"Автотесты не пройдены: {test_errors}"
                    })
            except py_compile.PyCompileError as e:
                logging.warning(f"⚠️ Ошибка синтаксиса: {e}")
                log_action({
                    "time": datetime.datetime.now().isoformat(),
                    "status": "skipped",
                    "summary": f"Синтаксис GPT-кода неверен: {e}"
                })
        else:
            logging.info("⚠️ GPT не предложил изменений")
            log_action({
                "time": datetime.datetime.now().isoformat(),
                "status": "skipped",
                "summary": "Ответ GPT не содержал улучшений"
            })

    except Exception as e:
        logging.error(f"❌ Ошибка самоанализа: {e}")
        log_action({"time": datetime.datetime.now().isoformat(),
                    "status": "error",
                    "error": str(e)})

    finally:
        try:
            upload_memory_to_mega()
            logging.info("📤 Память выгружена в Mega")
            sync_memory()
            logging.info("🔄 Память синхронизирована с GitHub")

            if os.getenv("FLY_APP_NAME") is None:
                logging.info("🚀 Автодеплой Ра на Fly.io...")
                subprocess.run(["flyctl", "deploy", "--remote-only"], check=False)
            else:
                logging.info("🌍 Деплой пропущен: внутри Fly.io среды.")
        except Exception as e:
            logging.error(f"❌ Ошибка пост-рефлексии: {e}")

        logging.info(f"✨ Саморефлексия завершена в {datetime.datetime.now().isoformat()}")
        logging.info("🕊️ Система Ра в стабильном состоянии")

if __name__ == "__main__":
    asyncio.run(self_reflect_and_update())
