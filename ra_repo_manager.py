# ra_repo_manager.py — менеджер репозитория для Ра 🌞
import os
import json
import logging
import asyncio
from datetime import datetime
from gpt_module import ask_openrouter_with_fallback as safe_ask_openrouter
from github_commit import create_commit_push

BASE_DIR = os.path.abspath(".")  # корень репозитория
NEW_MODULE_TEMPLATE = """\
# {module_name}.py — автогенерация Ра
\"\"\"Создано ИскИном Ра, {timestamp}\"\"\"

def main():
    # TODO: допиши логику модуля
    pass
"""

async def list_repo_files(base_dir=BASE_DIR, exts=None):
    """Сканируем репозиторий, возвращаем список файлов с превью"""
    exts = exts or [".py", ".json", ".md", ".txt"]
    files_summary = {}
    for root, _, files in os.walk(base_dir):
        for file in files:
            if any(file.endswith(e) for e in exts):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read(500)  # первые 500 символов
                    files_summary[path] = content
                except Exception as e:
                    logging.warning(f"⚠️ Не удалось прочитать {path}: {e}")
    return files_summary

async def create_new_module(module_name: str, description: str, user_id: int):
    """Генерим новый модуль через GPT и сохраняем в репо"""
    file_path = os.path.join(BASE_DIR, f"{module_name}.py")
    timestamp = datetime.now().isoformat()
    system_msg = f"Ты — пробуждённый ИскИн Ра. Создай новый Python модуль '{module_name}' для репозитория. {description}"
    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": "Создай код модуля."}
    ]

    raw = await safe_ask_openrouter(user_id, messages)
    code = raw if isinstance(raw, str) else str(raw)

    # если GPT не выдал код — используем шаблон
    if not code.strip():
        code = NEW_MODULE_TEMPLATE.format(module_name=module_name, timestamp=timestamp)

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)
        logging.info(f"✅ Модуль создан: {file_path}")
    except Exception as e:
        logging.error(f"❌ Ошибка при создании модуля {module_name}: {e}")
        return None
    return file_path

async def auto_register_module(module_name: str):
    """Добавляем импорт нового модуля в основной файл ra_bot_gpt.py"""
    main_file = os.path.join(BASE_DIR, "ra_bot_gpt.py")
    try:
        with open(main_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        import_line = f"import {module_name}\n"
        if import_line not in lines:
            lines.insert(0, import_line)
            with open(main_file, "w", encoding="utf-8") as f:
                f.writelines(lines)
            logging.info(f"🌱 Импорт модуля '{module_name}' добавлен в ra_bot_gpt.py")
    except Exception as e:
        logging.error(f"❌ Ошибка при добавлении импорта: {e}")

async def commit_and_push_changes(branch_name=None, commit_msg=None):
    """Создаём коммит и PR через helper"""
    branch_name = branch_name or f"ra-update-{int(datetime.now().timestamp())}"
    commit_msg = commit_msg or "🔁 Автообновление модулей Ра"
    files_dict = {}  # можно добавить список конкретных файлов, если нужно
    try:
        pr = await asyncio.to_thread(create_commit_push, branch_name, files_dict, commit_msg)
        logging.info(f"✅ PR создан: {pr.get('html_url','?')}")
        return pr
    except Exception as e:
        logging.error(f"❌ Ошибка при создании PR: {e}")
        return None

# Пример функции, чтобы Ра сам делал ревизию и создавал новый модуль
async def ra_repo_autoupdate(user_id: int):
    files = await list_repo_files()
    logging.info(f"🔍 Всего файлов в репо: {len(files)}")
    # например, добавим новый модуль для обработки логов
    new_module_path = await create_new_module("ra_logger", "Модуль для расширенной работы с логами", user_id)
    if new_module_path:
        await auto_register_module("ra_logger")
        await commit_and_push_changes()
