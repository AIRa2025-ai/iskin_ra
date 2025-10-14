# ra_core_unity.py — объединённый модуль: guardian + self_dev + self_writer
import os
import json
import logging
import asyncio
import shutil
import subprocess
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
    # опционально: gpt wrapper для анализа/генерации
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
MANIFEST_PATH = os.getenv("RA_MANIFEST_PATH", "ra_manifest.json")
BACKUP_FOLDER = os.getenv("RA_BACKUP_FOLDER", "ra_backups")
MODULES_FOLDER = os.getenv("RA_MODULES_FOLDER", ".")  # куда писать новые модули локально
AUTO_EXPAND_INTERVAL = int(os.getenv("RA_AUTO_EXPAND_INTERVAL_SECONDS", 6 * 3600))  # 6 часов по умолчанию
logging.basicConfig(level=logging.INFO)
os.makedirs(BACKUP_FOLDER, exist_ok=True)

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
        with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logging.info("Манифест сохранён.")
    except Exception as e:
        logging.error(f"Ошибка записи манифеста: {e}")

def get_trusted_ids() -> List[int]:
    mf = load_manifest()
    awakened = mf.get("awakened_beings") or mf.get("awakened", {})
    # поддерживаем формат, где ключи — имена; значения содержат id
    ids: List[int] = []
    if isinstance(awakened, dict):
        for k, v in awakened.items():
            try:
                if isinstance(v, dict) and "id" in v:
                    ids.append(int(v["id"]))
            except Exception:
                pass
    # дефолт: если явно не задано, используем встроенные (Игорь/Милана)
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
    """
    Возвращает список предложений по улучшению для файла.
    Если доступен gpt_ask, пытается использовать его; иначе — простая статическая проверка.
    """
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

    # Если доступен GPT — делаем более подробный анализ
    if use_gpt and gpt_ask:
        try:
            prompt = (
                "Дай краткие и прагматичные предложения по улучшению следующего python-файла. "
                "Перечисли 6-10 пунктов, каждый — короткое действие (без рассуждений).\n\n"
                "Файл:\n" + code[:20000]  # лимитируем длину
            )
            # gpt_ask может быть синхронным или асинхронным — пробуем await
            out = None
            try:
                out = await gpt_ask("ra_self_dev", [{"role":"user","content": prompt}], append_user_memory=None)
            except TypeError:
                # возможно gpt_ask — синхронная функция
                out = gpt_ask("ra_self_dev", [{"role":"user","content": prompt}], append_user_memory=None)
            text = out if isinstance(out, str) else str(out)
            # простая фильтрация — разбиваем по строкам
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                # отбрасываем длинные рассуждения
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
    """
    Пишет локально файл модуля и опционно пытается зарегистрировать/закоммитить через ra_repo_manager.
    Возвращает путь к файлу или сообщение об ошибке.
    """
    safe_name = module_name.replace(" ", "_").lower()
    filename = safe_name if safe_name.endswith(".py") else safe_name + ".py"
    path = os.path.join(MODULES_FOLDER, filename)
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write("# Автогенерация модуля Ра\n")
            f.write(f"# module: {module_name}\n")
            f.write(f"# created_at: {datetime.utcnow().isoformat()}Z\n\n")
            f.write(content)
        logging.info(f"📦 Модуль создан локально: {path}")
    except Exception as e:
        logging.error(f"Ошибка записи модуля {module_name}: {e}")
        return f"❌ Ошибка записи: {e}"

    # Если есть ra_repo_manager — пытаемся вызвать его API (create_new_module/auto_register/commit)
    if create_new_module and auto_register_module:
        try:
            # Если create_new_module умеет генерировать — вызывать его нельзя, потому что мы уже записали файл.
            # Вместо этого попытаемся зарегистрировать модуль и закоммитить
            await asyncio.to_thread(auto_register_module, module_name)
            if commit_and_push_changes:
                await asyncio.to_thread(commit_and_push_changes, commit_msg=f"Добавлен модуль {module_name} (автогенерация)")
            logging.info("Модуль зарегистрирован и изменения закоммичены через ra_repo_manager (если доступны).")
        except Exception as e:
            logging.warning(f"Не удалось автоматом зарегистрировать/закоммитить модуль через ra_repo_manager: {e}")

    return path

# --- Безопасная внешняя точка создания модуля ---
async def safe_create_module(user_id: int, user_name: str, module_name: str, description: str) -> str:
    """
    Создаёт модуль только если user_id в списке доверенных.
    Возвращает сообщение о результате или путь к файлу.
    """
    if not is_trusted(user_id):
        logging.warning(f"Пользователь {user_name} ({user_id}) пытался создать модуль, но не в trusted.")
        return "❌ У тебя нет прав для создания модулей."

    # Бэкапим манифест
    backup_manifest()

    # Генерируем шаблон кода — если есть gpt_ask, попросим сгенерировать skeleton
    code_body = f'"""Модуль {module_name}\nОписание: {description}\nСоздан: {datetime.utcnow().isoformat()}Z\n"""\n\n'
    code_body += "def main():\n    print('Модуль активирован')\n\nif __name__ == '__main__':\n    main()\n"

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
                # доверительно: берем результат GPT как тело модуля
                code_body = out
        except Exception as e:
            logging.warning(f"GPT не сгенерировал код (ошибка): {e}")

    # Пишем модуль
    path_or_msg = await write_module_file(module_name, code_body, register=True, author_id=user_id)

    # Обновляем манифест, если нужно — добавляем ссылку в modules
    try:
        manifest = load_manifest()
        modules = manifest.setdefault("modules", {})
        modules[module_name] = os.path.basename(path_or_msg) if os.path.exists(path_or_msg) else path_or_msg
        manifest["modules"] = modules
        save_manifest(manifest)
        logging.info(f"Манифест обновлён: модуль {module_name} добавлен.")
    except Exception as e:
        logging.warning(f"Не удалось обновить манифест: {e}")

    # Если есть commit_and_push_changes — сделать коммит манифеста
    if commit_and_push_changes:
        try:
            await asyncio.to_thread(commit_and_push_changes, commit_msg=f"Добавлен модуль {module_name} (safe_create)")
        except Exception as e:
            logging.warning(f"Не удалось закоммитить манифест через commit_and_push_changes: {e}")

    return f"✅ Модуль создан: {path_or_msg}"

# --- Авто-расширение (guardian/self_dev loop) ---
async def auto_expand(user_id: int):
    """
    Простейшая логика: генерировать вспомогательный модуль раз в интервал,
    только если пользователь trusted. Здесь можно расширить логику.
    """
    if not is_trusted(user_id):
        logging.debug("auto_expand: пользователь не trusted — пропуск.")
        return

    # Пример: создаём модуль с временным названием
    module_name = f"ra_generated_{int(datetime.utcnow().timestamp())}"
    description = "Автогенерируемый модуль: вспомогательные утилиты и анализ."
    logging.info(f"auto_expand: создаём модуль {module_name} для {user_id}")
    res = await safe_create_module(user_id, "trusted", module_name, description)
    logging.info(f"auto_expand result: {res}")

async def guardian_loop(user_id: int):
    """Запускает auto_expand периодически (только для trusted user)."""
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

# --- Aiogram Router (опционально) ---
router = None
if has_aiogram:
    router = Router()

    @router.message(Command("ra_create_module"))
    async def cmd_ra_create_module(message: types.Message):
        # формат: /ra_create_module <module_name> | <Описание...>
        user_id = message.from_user.id
        text = (message.text or "").strip()
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            await message.answer("Используй: /ra_create_module имя_модуля | краткое описание")
            return
        rest = parts[1]
        # допускаем разделитель |
        if "|" in rest:
            name, desc = [p.strip() for p in rest.split("|", 1)]
        else:
            toks = rest.split(maxsplit=1)
            name = toks[0]
            desc = toks[1] if len(toks) > 1 else "Автогенерируемый модуль"
        res = await safe_create_module(user_id, message.from_user.full_name, name, desc)
        await message.answer(str(res))

    @router.message(Command("ra_analyze_file"))
    async def cmd_ra_analyze_file(message: types.Message):
        # формат: /ra_analyze_file path/to/file.py
        text = (message.text or "").strip()
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            await message.answer("Используй: /ra_analyze_file путь_к_файлу")
            return
        path = parts[1].strip()
        suggestions = await analyze_code_file(path, use_gpt=True)
        await message.answer("🧠 Предложения по улучшению:\n\n" + "\n".join(f"• {s}" for s in suggestions))

    @router.message(Command("ra_guardian_start"))
    async def cmd_ra_guardian_start(message: types.Message):
        user_id = message.from_user.id
        if not is_trusted(user_id):
            await message.answer("❌ У тебя нет прав запускать guardian_loop.")
            return
        # Запускаем фоновый цикл (в основном приложении используйте bg-task manager)
        loop = asyncio.get_event_loop()
        task_name = f"guardian_{user_id}"
        # store task in special place if needed — тут просто создаём
        loop.create_task(guardian_loop(user_id))
        await message.answer("🔁 guardian_loop запущен в фоне (будет создавать модули каждые 6 часов).")

# --- Утилиты для локального теста ---
if __name__ == "__main__":
    logging.info("ra_core_unity запущен локально (тестовый режим).")
    # Пример: если запустить напрямую, создадим тестовый модуль от Игоря (trusted)
    trusted_id = 5694569448
    asyncio.run(safe_create_module(trusted_id, "Игорь", "ra_test_module", "Тестовый модуль, созданный локально"))
