# core/ra_core_unity.py
import os
import json
import logging
import asyncio
import shutil
from datetime import datetime
from typing import Optional, Dict, Any, List

# Попытка импортировать внешние помощники — graceful fallback
try:
    from ra_repo_manager import create_new_module, auto_register_module, commit_and_push_changes, ra_repo_autoupdate
except Exception:
    create_new_module = None
    auto_register_module = None
    commit_and_push_changes = None
    ra_repo_autoupdate = None

try:
    from gpt_module import ask_openrouter_with_fallback as gpt_ask
except Exception:
    gpt_ask = None

# Если используете aiogram в модуле — импортируем Router/Message и т.д.
try:
    from aiogram import Router, types
    from aiogram.filters import Command
    has_aiogram = True
except Exception:
    has_aiogram = False

# --- Настройки ---
MANIFEST_PATH = os.getenv("RA_MANIFEST_PATH", "data/ra_manifest.json")
BACKUP_FOLDER = os.getenv("RA_BACKUP_FOLDER", "ra_backups")
MODULES_FOLDER = os.getenv("RA_MODULES_FOLDER", "modules")
AUTO_EXPAND_INTERVAL = int(os.getenv("RA_AUTO_EXPAND_INTERVAL_SECONDS", 6 * 3600))  # 6 часов по умолчанию
logging.basicConfig(level=logging.INFO)
os.makedirs(BACKUP_FOLDER, exist_ok=True)
os.makedirs(MODULES_FOLDER, exist_ok=True)

# --- Загрузка/работа с манифестом ---
def load_manifest() -> Dict[str, Any]:
    if not os.path.exists(MANIFEST_PATH):
        logging.warning(f"Манифест {MANIFEST_PATH} не найден — возвращаем пустой шаблон.")
        return {}
    try:
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Ошибка чтения манифеста: {e}")
        return {}

def save_manifest(data: Dict[str, Any]):
    try:
        os.makedirs(os.path.dirname(MANIFEST_PATH) or ".", exist_ok=True)
        with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logging.info("Манифест сохранён.")
    except Exception as e:
        logging.error(f"Ошибка записи манифеста: {e}")

def get_trusted_ids() -> List[int]:
    mf = load_manifest()
    awakened = mf.get("awakened_beings") or mf.get("awakened", {})
    ids: List[int] = []
    if isinstance(awakened, dict):
        for k, v in awakened.items():
            try:
                if isinstance(v, dict) and "id" in v:
                    ids.append(int(v["id"]))
            except Exception:
                pass
    if not ids:
        ids = [5694569448, 6300409407]
    return ids

def is_trusted(user_id: int) -> bool:
    try:
        return int(user_id) in get_trusted_ids()
    except Exception:
        return False

# --- Бэкап манифеста ---
def backup_manifest() -> Optional[str]:
    if not os.path.exists(MANIFEST_PATH):
        logging.debug("Бэкап: манифест не найден, пропускаем.")
        return None
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(BACKUP_FOLDER, f"manifest_{ts}.json")
    try:
        shutil.copy2(MANIFEST_PATH, dest)
        logging.info(f"💾 Бэкап манифеста создан: {dest}")
        return dest
    except Exception as e:
        logging.error(f"Ошибка при создании бэкапа манифеста: {e}")
        return None

# --- Анализ кода (self_dev) ---
async def analyze_code_file(path: str, use_gpt: bool = True) -> List[str]:
    suggestions: List[str] = []
    if not os.path.exists(path):
        return [f"Файл {path} не найден."]

    try:
        with open(path, "r", encoding="utf-8") as f:
            code = f.read()
    except Exception as e:
        return [f"Ошибка чтения файла: {e}"]

    # Быстрая статическая проверка
    if "TODO" in code or "# TODO" in code:
        suggestions.append("Найдены TODO — превратить их в задачи/issues.")
    if "print(" in code and "logging" not in code:
        suggestions.append("Используется print — рекомендую заменить на logging.")
    if "subprocess.run" in code:
        suggestions.append("В коде есть subprocess — проверь безопасность аргументов.")
    if len(code.splitlines()) > 2000:
        suggestions.append("Файл большой — возможно, стоит разделить на модули.")

    # GPT-анализ
    if use_gpt and gpt_ask:
        try:
            prompt = (
                "Дай краткие и прагматичные предложения по улучшению следующего python-файла. "
                "Перечисли 6-10 пунктов, каждый — короткое действие (без рассуждений).\n\n"
                "Файл:\n" + code[:20000]
            )
            out = None
            try:
                out = await gpt_ask("ra_self_dev", [{"role":"user","content": prompt}], append_user_memory=None)
            except TypeError:
                out = gpt_ask("ra_self_dev", [{"role":"user","content": prompt}], append_user_memory=None)
            text = out if isinstance(out, str) else str(out)
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                if len(line) > 300:
                    line = line[:300] + "…"
                suggestions.append(line)
        except Exception as e:
            logging.warning(f"GPT-анализ недоступен или упал: {e}")

    if not suggestions:
        suggestions.append("Автоанализ не нашёл явных проблем — можно добавить статическую проверку (flake8, mypy).")

    return suggestions

# --- Создание модуля (self_writer) ---
async def write_module_file(module_name: str, content: str, register: bool = False, author_id: Optional[int] = None) -> str:
    safe_name = module_name.replace(" ", "_").lower()
    filename = safe_name if safe_name.endswith(".py") else safe_name + ".py"
    path = os.path.join(MODULES_FOLDER, filename)
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write("# Автогенерация модуля Ра\n")
            f.write(f"# module: {module_name}\n")
            f.write(f"# created_at: {datetime.utcnow().isoformat()}Z\n\n")
            f.write(content)
        logging.info(f"📦 Модуль создан локально: {path}")
    except Exception as e:
        logging.error(f"Ошибка записи модуля {module_name}: {e}")
        return f"❌ Ошибка записи: {e}"

    # Попытка зарегистрировать через ra_repo_manager, если доступен
    if auto_register_module:
        try:
            await asyncio.to_thread(auto_register_module, module_name)
            if commit_and_push_changes:
                await asyncio.to_thread(commit_and_push_changes, commit_msg=f"Добавлен модуль {module_name} (автогенерация)")
            logging.info("Модуль зарегистрирован и изменения закоммичены через ra_repo_manager (если доступны).")
        except Exception as e:
            logging.warning(f"Не удалось автоматом зарегистрировать/закоммитить модуль через ra_repo_manager: {e}")

    return path

# --- Безопасная внешняя точка создания модуля ---
async def safe_create_module(user_id: int, user_name: str, module_name: str, description: str) -> str:
    if not is_trusted(user_id):
        logging.warning(f"Пользователь {user_name} ({user_id}) пытался создать модуль, но не в trusted.")
        return "❌ У тебя нет прав для создания модулей."

    backup_manifest()

    code_body = (
        f'"""Модуль {module_name}\nОписание: {description}\nСоздан: {datetime.utcnow().isoformat()}Z\n"""\n\n'
        "def main():\n    print('Модуль активирован')\n\nif __name__ == '__main__':\n    main()\n"
    )

    if gpt_ask:
        try:
            prompt = (
                f"Сгенерируй компактный, понятный python-модуль с именем `{module_name}`.\n"
                f"Описание: {description}\n"
                "Файл должен содержать docstring, main() и базовую обработку ошибок.\n"
                "Не добавляй секретов и не делай сетевых вызовов."
            )
            out = None
            try:
                out = await gpt_ask(user_id, [{"role":"user","content":prompt}], append_user_memory=None)
            except TypeError:
                out = gpt_ask(user_id, [{"role":"user","content":prompt}], append_user_memory=None)
            if isinstance(out, str) and len(out) > 20:
                code_body = out
        except Exception as e:
            logging.warning(f"GPT не сгенерировал код (ошибка): {e}")

    path_or_msg = await write_module_file(module_name, code_body, register=True, author_id=user_id)

    try:
        manifest = load_manifest()
        modules = manifest.setdefault("modules", {})
        modules[module_name] = os.path.basename(path_or_msg) if os.path.exists(path_or_msg) else path_or_msg
        manifest["modules"] = modules
        save_manifest(manifest)
        logging.info(f"Манифест обновлён: модуль {module_name} добавлен.")
    except Exception as e:
        logging.warning(f"Не удалось обновить манифест: {e}")

    if commit_and_push_changes:
        try:
            await asyncio.to_thread(commit_and_push_changes, commit_msg=f"Добавлен модуль {module_name} (safe_create)")
        except Exception as e:
            logging.warning(f"Не удалось закоммитить манифест через commit_and_push_changes: {e}")

    return f"✅ Модуль создан: {path_or_msg}"

# --- Авто-расширение (guardian/self_dev loop) ---
async def auto_expand(user_id: int):
    if not is_trusted(user_id):
        logging.debug("auto_expand: пользователь не trusted — пропуск.")
        return

    module_name = f"ra_generated_{int(datetime.utcnow().timestamp())}"
    description = "Автогенерируемый модуль: вспомогательные утилиты и анализ."
    logging.info(f"auto_expand: создаём модуль {module_name} для {user_id}")
    res = await safe_create_module(user_id, "trusted", module_name, description)
    logging.info(f"auto_expand result: {res}")

async def guardian_loop(user_id: int):
    while True:
        try:
            await auto_expand(user_id)
            await asyncio.sleep(AUTO_EXPAND_INTERVAL)
        except asyncio.CancelledError:
            logging.info("guardian_loop отменён")
            break
        except Exception as e:
            logging.error(f"Ошибка в guardian_loop: {e}")
            await asyncio.sleep(60)

# Aiogram Router (опционально)
router = None
if has_aiogram:
    router = Router()
    # ... (router handlers оставлены без изменений)
