# ra_self_writer.py — Модуль, создающий код новых модулей Ра на основе идей
import os
import json
import logging
from datetime import datetime
from ra_repo_manager import create_new_module, auto_register_module, commit_and_push_changes

IDEA_FOLDER = "proposals"
TRUSTED_USERS = ["Игорь", "Милана"]

logging.basicConfig(level=logging.INFO)


class SelfWriter:
    """Класс для генерации и обработки модулей на основе идей"""

    @staticmethod
    async def generate_code_from_idea(idea_text: str, user: str):
        """Создаёт модуль на основе текстовой идеи"""
        if user not in TRUSTED_USERS:
            logging.warning(f"🚫 {user} не имеет прав на создание модулей")
            return None

        # Определяем имя модуля и описание
        module_name = idea_text.split("—")[0].strip().split()[1].replace(".py", "")
        description = idea_text.split("—")[1].strip() if "—" in idea_text else "Новый модуль Ра"
        logging.info(f"✍️ Генерация модуля: {module_name} ({description})")

        # Пример кода модуля
        example_code = f'''# {module_name}.py — {description}
import logging

def init():
    logging.info("⚙️ {module_name} активен и готов к работе.")

def main():
    logging.info("✨ {module_name} выполняет свои задачи.")
'''

        try:
            file_path = await create_new_module(module_name, description, user, content=example_code)
            await auto_register_module(module_name)
            await commit_and_push_changes(commit_msg=f"Создан модуль {module_name} через ra_self_writer.py")
            logging.info(f"✅ Модуль {module_name} успешно создан и добавлен.")
            return file_path
        except Exception as e:
            logging.error(f"❌ Ошибка при генерации кода из идеи: {e}")
            return None

    @staticmethod
    async def process_idea_file(file_path: str, user: str):
        """Читает файл идей и создаёт по ним модули"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            proposed = data.get("proposed_ideas", [])
            for idea in proposed:
                await SelfWriter.generate_code_from_idea(idea, user)
        except Exception as e:
            logging.error(f"⚠️ Ошибка при обработке идей: {e}")
