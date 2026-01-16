# modules/ra_guardian.py — Модуль самообновления и расширения ядра Ра
import os
import json
import logging
import asyncio
from datetime import datetime
import re

# Отложенный импорт, чтобы не было ошибок при загрузке до ra_repo_manager
def import_repo_manager():
    try:
        from ra_repo_manager import create_new_module, auto_register_module, commit_and_push_changes
        return create_new_module, auto_register_module, commit_and_push_changes
    except Exception as e:
        logging.warning(f"⚠️ ra_repo_manager пока недоступен: {e}")
        return None, None, None

class Guardian:
    TRUSTED_USERS = [5694569448, 6300409407]
    MANIFEST_PATH = "ra_manifest.json"
    BACKUP_FOLDER = "backups"
    PROPOSALS_FOLDER = "proposals"

    def __init__(self):
        os.makedirs(self.BACKUP_FOLDER, exist_ok=True)
        os.makedirs(self.PROPOSALS_FOLDER, exist_ok=True)
        logging.basicConfig(level=logging.INFO)
        self.loop_tasks = []

    # --- Основные функции ---
    async def safe_create_module(self, module_name: str, description: str, user: int):
        """Создаёт модуль только если пользователь доверенный"""
        if user not in self.TRUSTED_USERS:
            logging.warning(f"❌ Пользователь {user} не имеет права создавать модули")
            return None

        logging.info(f"🌱 Создаём новый модуль {module_name}...")

        create_new_module_fn, auto_register_module_fn, commit_and_push_changes_fn = import_repo_manager()
        if not create_new_module_fn:
            logging.warning("⚠️ ra_repo_manager функции недоступны, модуль не создан")
            return None

        file_path = await create_new_module_fn(module_name, description, user)
        if file_path:
            await auto_register_module_fn(module_name)
            logging.info(f"✅ Модуль {module_name} создан и подключён")
            await commit_and_push_changes_fn(commit_msg=f"Создан модуль {module_name} Ра")
        return file_path

    # --- Backup ---
    def backup_manifest(self):
        """Делаем резервную копию манифеста перед любыми изменениями"""
        if os.path.exists(self.MANIFEST_PATH):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(self.BACKUP_FOLDER, f"manifest_{timestamp}.json")
            try:
                with open(self.MANIFEST_PATH, "r", encoding="utf-8") as f:
                    data = f.read()
                with open(backup_path, "w", encoding="utf-8") as f:
                    f.write(data)
                logging.info(f"💾 Создан бэкап манифеста: {backup_path}")
            except Exception as e:
                logging.error(f"❌ Ошибка бэкапа манифеста: {e}")

    # --- Анализ репо ---
    def analyze_repository(self) -> list:
        """Анализирует текущие файлы проекта и возвращает список предложений по модулям"""
        existing_files = os.listdir(".")
        proposals = []

        missing_features = []
        if not any("observer" in f for f in existing_files):
            missing_features.append("Nablyudenie_za_sobytiyami_v_mire")
        if not any("reflection" in f for f in existing_files):
            missing_features.append("Samoanliz_i_osoznanie_opyta")
        if not any("optimizer" in f for f in existing_files):
            missing_features.append("Optimizatsiya_resursov_i_protsessov")
        if not any("context_keeper" in f for f in existing_files):
            missing_features.append("Khranenie_konteksta_dialogov_i_znaniy")

        for feature in missing_features:
            safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', feature)
            module_name = f"ra_{safe_name}_{int(datetime.now().timestamp())}"
            description = f"Модуль: {feature}"
            example_code = f'''# {module_name}.py — {feature}
import logging

def init():
    logging.info("🔮 Модуль {feature} инициализирован.")
'''
            proposals.append({
                "module_name": module_name,
                "description": description,
                "example_code": example_code
            })

        return proposals

    async def propose_new_modules(self, user: int):
        """Ра предлагает новые модули для доверенного пользователя"""
        proposals = self.analyze_repository()
        if not proposals:
            logging.info("✅ Все ключевые модули присутствуют, предложений нет.")
            return []

        path = os.path.join(self.PROPOSALS_FOLDER, f"{user}_proposals.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(proposals, f, ensure_ascii=False, indent=2)
            logging.info(f"📝 Предложения для новых модулей сохранены: {path}")
        except Exception as e:
            logging.error(f"❌ Ошибка сохранения предложений: {e}")

        return proposals

    async def auto_expand(self, user: int):
        """Авто-расширение ядра Ра"""
        proposals = await self.propose_new_modules(user)
        if proposals:
            first = proposals[0]
            logging.info(f"✨ Авто-создание модуля: {first['module_name']}")
            await self.safe_create_module(first["module_name"], first["description"], user)

    # --- Новый метод observe ---
    async def observe(self):
        """Ра наблюдает за миром (для observer_loop)"""
        logging.info("🔭 Guardian наблюдает за миром...")
        await asyncio.sleep(0.1)  # имитация async работы

    async def guardian_loop(self, user: int):
        """Основной цикл — проверяет необходимость новых модулей каждые 6 часов"""
        while True:
            try:
                self.backup_manifest()
                await self.auto_expand(user)
                await asyncio.sleep(6 * 3600)
            except asyncio.CancelledError:
                logging.info("🔧 guardian_loop отменён")
                break
            except Exception as e:
                logging.error(f"❌ Ошибка в guardian_loop: {e}")
                await asyncio.sleep(60)

    def start(self):
        """Запуск guardian_loop для всех доверенных пользователей"""
        for u in self.TRUSTED_USERS:
            task = asyncio.create_task(self.guardian_loop(u))
            self.loop_tasks.append(task)
