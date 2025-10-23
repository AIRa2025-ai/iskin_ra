# core/ra_self_writer.py
import os
import json
import logging
from datetime import datetime

# импортируем менеджер репо — он теперь принимает content optional
try:
    from ra_repo_manager import create_new_module, auto_register_module, commit_and_push_changes
except Exception:
    create_new_module = None
    auto_register_module = None
    commit_and_push_changes = None

IDEA_FOLDER = "proposals"
TRUSTED_USERS = [5694569448, 6300409407]

logging.basicConfig(level=logging.INFO)

class SelfWriter:
    @staticmethod
    async def generate_code_from_idea(idea_text: str, user: int):
        if user not in TRUSTED_USERS:
            logging.warning(f"🚫 Пользователь {user} не имеет прав на создание модулей")
            return None

        # безопасный парсинг имени модуля
        # ожидаем формат: "Создать ra_name.py — Описание..." или "ra_name — Описание"
        module_name = None
        try:
            left = idea_text.split("—")[0].strip()
            toks = left.replace(".py", "").split()
            module_name = toks[0] if toks else None
        except Exception:
            module_name = None

        if not module_name:
            module_name = f"ra_generated_{int(datetime.utcnow().timestamp())}"

        description = "Новый модуль Ра"
        try:
            if "—" in idea_text:
                description = idea_text.split("—", 1)[1].strip()
        except Exception:
            pass

        logging.info(f"✍️ Генерация модуля: {module_name} ({description})")

        example_code = f'''# {module_name}.py — {description}
import logging

def init():
    logging.info("⚙️ {module_name} активен и готов к работе.")

def main():
    logging.info("✨ {module_name} выполняет свои задачи.")
'''

        try:
            if create_new_module:
                file_path = await create_new_module(module_name, description, user, content=example_code)
            else:
                # fallback — локально записать в modules/
                path = os.path.join("modules", f"{module_name}.py")
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(example_code)
                file_path = path
            if auto_register_module:
                await auto_register_module(module_name)
            if commit_and_push_changes:
                await commit_and_push_changes(commit_msg=f"Создан модуль {module_name} через ra_self_writer.py")
            logging.info(f"✅ Модуль {module_name} успешно создан и добавлен.")
            return file_path
        except Exception as e:
            logging.error(f"❌ Ошибка при генерации кода из идеи: {e}")
            return None

    @staticmethod
    async def process_idea_file(file_path: str, user: int):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            proposed = data.get("proposed_ideas", []) if isinstance(data, dict) else []
            for idea in proposed:
                await SelfWriter.generate_code_from_idea(idea, user)
        except Exception as e:
            logging.error(f"⚠️ Ошибка при обработке идей: {e}")
