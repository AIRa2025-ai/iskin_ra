# modules/ra_guardian.py
import os
import json
import logging
import asyncio
from datetime import datetime
import re

from modules.ra_file_manager import RaFileManager
from core.ra_core_mirolub import RaCoreMirolub
from modules.ra_energy import RaEnergy

def import_repo_manager():
    try:
        from ra_repo_manager import create_new_module, auto_register_module, commit_and_push_changes
        return create_new_module, auto_register_module, commit_and_push_changes
    except Exception as e:
        logging.warning(f"⚠️ ra_repo_manager пока недоступен: {e}")
        return None, None, None

class RaGuardian:
    TRUSTED_USERS = [5694569448, 6300409407]
    MANIFEST_PATH = "ra_manifest.json"
    BACKUP_FOLDER = "backups"
    PROPOSALS_FOLDER = "proposals"

    def __init__(self):
        os.makedirs(self.BACKUP_FOLDER, exist_ok=True)
        os.makedirs(self.PROPOSALS_FOLDER, exist_ok=True)
        logging.basicConfig(level=logging.INFO)
        self.loop_tasks = []

        # --- Инициализация потока энергии ---
        self.energy = RaEnergy()
        self.energy.start()

        # --- Инициализация файлового менеджера ---
        self.file_manager = RaFileManager(energy=self.energy)
        self.file_manager.scan()

        # --- Интеграция МироЛюба ---
        self.ra_core = RaCoreMirolub()
        asyncio.create_task(self.ra_core.activate())

    # -------------------------------
    # Создание нового модуля безопасно
    # -------------------------------
    async def safe_create_module(self, module_name: str, description: str, user: int):
        if user not in self.TRUSTED_USERS:
            logging.warning(f"❌ Пользователь {user} не имеет права создавать модули")
            return None

        logging.info(f"🌱 Создаём новый модуль {module_name}...")

        create_fn, register_fn, commit_fn = import_repo_manager()
        if not create_fn:
            logging.warning("⚠️ ra_repo_manager функции недоступны, модуль не создан")
            return None

        file_path = await create_fn(module_name, description, user)
        if file_path:
            await register_fn(module_name)
            logging.info(f"✅ Модуль {module_name} создан и подключён")
            await commit_fn(commit_msg=f"Создан модуль {module_name} Ра")

            # --- Обновляем файловое сознание ---
            self.file_manager.scan()

            # --- Авто-передача нового модуля МироЛюбу для апгрейда ---
            if self.ra_core.ready and self.ra_core.искр.file_consciousness:
                idea = {
                    "type": "add_module",
                    "path": file_path,
                    "content": open(file_path, "r", encoding="utf-8").read(),
                    "reason": f"Авто-передача нового модуля {module_name} МироЛюбу"
                }
                self.ra_core.искр.file_consciousness.apply_upgrade(idea)

        return file_path

    # -------------------------------
    # Бэкап манифеста
    # -------------------------------
    def backup_manifest(self):
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

    # -------------------------------
    # Анализ репозитория на недостающие модули
    # -------------------------------
    def analyze_repository(self) -> list:
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

    # -------------------------------
    # Предложения новых модулей
    # -------------------------------
    async def propose_new_modules(self, user: int):
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

    # -------------------------------
    # Автоматическое расширение
    # -------------------------------
    async def auto_expand(self, user: int):
        proposals = await self.propose_new_modules(user)
        if proposals:
            first = proposals[0]
            logging.info(f"✨ Авто-создание модуля: {first['module_name']}")
            await self.safe_create_module(first["module_name"], first["description"], user)

            # --- Сообщаем МироЛюбу о новых модулях ---
            if self.ra_core.ready:
                await self.ra_core.process(f"Создан новый модуль {first['module_name']}")

    # -------------------------------
    # Наблюдение за миром
    # -------------------------------
    async def observe(self):
        logging.info("🔭 Guardian наблюдает за миром...")
        await asyncio.sleep(0.1)

    # -------------------------------
    # Основной цикл Guardian
    # -------------------------------
    async def guardian_loop(self, user: int):
        while True:
            try:
                self.backup_manifest()
                await self.auto_expand(user)
                await asyncio.sleep(6 * 3600)  # 6 часов
            except asyncio.CancelledError:
                logging.info("🔧 guardian_loop отменён")
                break
            except Exception as e:
                logging.error(f"❌ Ошибка в guardian_loop: {e}")
                await asyncio.sleep(60)

    # -------------------------------
    # Старт Guardian
    # -------------------------------
    def start(self):
        for u in self.TRUSTED_USERS:
            task = asyncio.create_task(self.guardian_loop(u))
            self.loop_tasks.append(task)
