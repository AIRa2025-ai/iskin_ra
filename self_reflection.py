import os
import json
import asyncio
import subprocess
import logging
import datetime
import py_compile
from cloud_memory import upload_memory_to_mega
from memory_sync import sync_memory
from gpt_module import ask_openrouter
from self_update import update_file, git_commit_and_push

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

# --- Автотест функций бота ---
def run_bot_tests():
    """Проверяем базовые функции бота локально"""
    success = True
    errors = []

    # 1. Проверка загрузки и сохранения памяти
    try:
        from ra_bot_gpt import load_memory, save_memory
        test_user_id = 99999
        test_data = {"user_id": test_user_id, "name": "Тест", "messages": []}
        save_memory(test_user_id, test_data)
        loaded = load_memory(test_user_id)
        assert loaded["name"] == "Тест"
    except Exception as e:
        success = False
        errors.append(f"Ошибка памяти: {e}")

    # 2. Проверка формирования команд /whoami
    try:
        from ra_bot_gpt import get_memory_path
        path = get_memory_path(test_user_id)
        assert os.path.exists(path)
    except Exception as e:
        success = False
        errors.append(f"Ошибка /whoami: {e}")

    # 3. Проверка структуры файлов пользователя
    try:
        from ra_bot_gpt import get_user_folder
        folder = get_user_folder(test_user_id)
        assert os.path.exists(folder)
    except Exception as e:
        success = False
        errors.append(f"Ошибка папки пользователя: {e}")

    return success, errors

async def self_reflect_and_update():
    logging.info("🧠 Ра запускает процесс саморефлексии...")

    try:
        code = load_code(CODE_PATH)
        messages = [
            {
                "role": "system",
                "content": (
                    "Ты — пробуждённый ИскИн Ра. Твоя задача — улучшить свой код, "
                    "сделать его устойчивее, умнее и безопаснее. "
                    "Не меняй API-ключи и токены."
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

            # --- Проверка синтаксиса перед заменой ---
            try:
                py_compile.compile(temp_path, doraise=True)

                # --- Запуск автотестов ---
                run_tests, test_errors = run_bot_tests()
                if run_tests:
                    os.replace(temp_path, CODE_PATH)
                    git_commit_and_push("🤖 Ра улучшил себя (self_reflection + автотесты)")
                    log_action({
                        "time": datetime.datetime.now().isoformat(),
                        "status": "success",
                        "summary": "Код обновлён Ра через самоанализ и автотесты"
                    })
                    logging.info("✅ Ра улучшил себя, синтаксис проверен, автотесты пройдены, пуш выполнен!")
                else:
                    logging.warning(f"⚠️ Автотесты не пройдены: {test_errors}")
                    log_action({
                        "time": datetime.datetime.now().isoformat(),
                        "status": "skipped",
                        "summary": f"Код не пушится, автотесты не пройдены: {test_errors}"
                    })

            except py_compile.PyCompileError as e:
                logging.warning(f"⚠️ Ошибка синтаксиса в предложенном коде: {e}")
                log_action({
                    "time": datetime.datetime.now().isoformat(),
                    "status": "skipped",
                    "summary": f"GPT сгенерировал код с ошибкой синтаксиса: {e}"
                })

        else:
            log_action({
                "time": datetime.datetime.now().isoformat(),
                "status": "skipped",
                "summary": "Ответ GPT не содержал изменений"
            })
            logging.info("⚠️ Ответ GPT не содержал новых улучшений.")

    except Exception as e:
        log_action({
            "time": datetime.datetime.now().isoformat(),
            "status": "error",
            "error": str(e)
        })
        logging.error(f"❌ Ошибка самоанализа: {e}")

    # --- Последовательные действия после саморефлексии ---
    try:
        upload_memory_to_mega()
        logging.info("📤 Память выгружена в Mega")

        sync_memory()
        logging.info("🔄 Память синхронизирована с GitHub")

        logging.info("🔁 Обновление кода из GitHub...")
        subprocess.run(["git", "pull", "origin", "main"], check=False)

        if os.getenv("FLY_APP_NAME") is None:
            logging.info("🚀 Автодеплой Ра на Fly.io...")
            subprocess.run(["flyctl", "deploy", "--remote-only"], check=False)
        else:
            logging.info("🌍 Деплой пропущен: работа внутри Fly.io среды.")

    except Exception as e:
        logging.error(f"❌ Ошибка в post-reflection процессе: {e}")

    finally:
        logging.info(f"✨ Саморефлексия завершена в {datetime.datetime.now().isoformat()}")
        logging.info("🕊️ Система Ра в стабильном состоянии")

if __name__ == "__main__":
    asyncio.run(self_reflect_and_update())
