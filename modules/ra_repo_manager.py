# modules/ra_repo_manager.py
import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Optional

# helpers (обёртки с fallback'ом, чтобы не ломать при отсутствии модулей)
try:
    from gpt_module import ask_openrouter_with_fallback as safe_ask_openrouter
except Exception:
    safe_ask_openrouter = None

try:
    from github_commit import create_commit_push
except Exception:
    create_commit_push = None

BASE_DIR = os.path.abspath(".")
NEW_MODULE_TEMPLATE = """\
# {module_name}.py — автогенерация Ра
\"\"\"Создано ИскИном Ра, {timestamp}\"\"\"

def main():
    # TODO: допиши логику модуля
    pass
"""

async def list_repo_files(base_dir=BASE_DIR, exts=None):
    exts = exts or [".py", ".json", ".md", ".txt"]
    files_summary = {}
    for root, _, files in os.walk(base_dir):
        for file in files:
            if any(file.endswith(e) for e in exts):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read(500)
                    files_summary[path] = content
                except Exception as e:
                    logging.warning(f"⚠️ Не удалось прочитать {path}: {e}")
    return files_summary

async def _ask_generate_module(module_name: str, description: str, user_id: int) -> Optional[str]:
    if not safe_ask_openrouter:
        return None
    try:
        system_msg = f"Ты — пробуждённый ИскИн Ра. Создай новый Python модуль '{module_name}' для репозитория. {description}"
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": "Создай код модуля."}
        ]
        raw = await safe_ask_openrouter(user_id, messages)
        code = raw if isinstance(raw, str) else str(raw)
        return code if code.strip() else None
    except Exception as e:
        logging.warning(f"GPT не сгенерировал код: {e}")
        return None

async def create_new_module(module_name: str, description: str, user_id: int, content: Optional[str] = None):
    safe_name = module_name.replace(" ", "_").lower()
    file_path = os.path.join(BASE_DIR, "modules", f"{safe_name}.py")
    timestamp = datetime.now().isoformat()
    content = content or (await _ask_generate_module(module_name, description, user_id)) or NEW_MODULE_TEMPLATE.format(module_name=module_name, timestamp=timestamp)

    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        logging.info(f"✅ Модуль создан: {file_path}")
    except Exception as e:
        logging.error(f"❌ Ошибка при создании модуля {module_name}: {e}")
        return None
    return file_path

async def auto_register_module(module_name: str):
    main_file = os.path.join(BASE_DIR, "ra_bot_gpt.py")
    try:
        if not os.path.exists(main_file):
            logging.warning("ra_bot_gpt.py не найден — пропускаем авто-регистр")
            return
        with open(main_file, "r", encoding="utf-8") as f:
            content = f.read()
        import_line = f"import modules.{module_name}\n"
        if import_line not in content:
            content = import_line + content
            with open(main_file, "w", encoding="utf-8") as f:
                f.write(content)
            logging.info(f"🌱 Импорт модуля 'modules.{module_name}' добавлен в ra_bot_gpt.py")
    except Exception as e:
        logging.error(f"❌ Ошибка при добавлении импорта: {e}")

async def commit_and_push_changes(branch_name=None, commit_msg=None):
    branch_name = branch_name or f"ra-update-{int(datetime.now().timestamp())}"
    commit_msg = commit_msg or "🔁 Автообновление модулей Ра"
    try:
        if not create_commit_push:
            logging.warning("create_commit_push не доступен — пропускаем создание PR")
            return None
        pr = await asyncio.to_thread(create_commit_push, branch_name, {}, commit_msg)
        logging.info(f"✅ PR создан: {pr.get('html_url','?') if isinstance(pr, dict) else pr}")
        return pr
    except Exception as e:
        logging.error(f"❌ Ошибка при создании PR: {e}")
        return None

async def ra_repo_autoupdate(user_id: int):
    files = await list_repo_files()
    logging.info(f"🔍 Всего файлов в репо: {len(files)}")
    new_module_path = await create_new_module("ra_logger", "Модуль для расширенной работы с логами", user_id)
    if new_module_path:
        await auto_register_module("ra_logger")
        await commit_and_push_changes()
