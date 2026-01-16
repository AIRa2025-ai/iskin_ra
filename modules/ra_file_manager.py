# ra_file_manager.py — модуль для осознанного взаимодействия Ра с файлами
import os
import json
import importlib.util
import logging
import shutil
import subprocess

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKUP_DIR = os.path.join(PROJECT_ROOT, "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

# 📜 Список разрешённых директорий
SAFE_DIRS = [PROJECT_ROOT]
def _is_safe_path(path: str) -> bool:
    """Проверка, что путь не выходит за пределы проекта."""
   return any(os.path.abspath(path).startswith(safe) for safe in SAFE_DIRS)

# --- Основные функции ---
def list_project_files():
    """Выводит список всех .py файлов проекта."""
    return [f for f in os.listdir(PROJECT_DIR) if f.endswith(".py")]

def read_file_content(filename: str) -> str:
    """Читает содержимое указанного файла."""
    path = os.path.join(PROJECT_DIR, filename)
    if not _is_safe_path(path):
        raise PermissionError("🚫 Путь за пределами проекта")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def write_new_file(filename: str, content: str) -> str:
    """Создаёт или перезаписывает файл, делая резервную копию перед этим."""
    path = os.path.join(PROJECT_DIR, filename)
    if not _is_safe_path(path):
        raise PermissionError("🚫 Нельзя писать за пределами проекта")

    # создаём бэкап
    if os.path.exists(path):
        backup_path = os.path.join(BACKUP_DIR, f"{filename}.{int(os.path.getmtime(path))}.bak")
        shutil.copy2(path, backup_path)
        logging.info(f"💾 Создан бэкап: {backup_path}")

    # записываем новый код
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    logging.info(f"✅ Файл {filename} обновлён")
    return path

def import_module_dynamic(filename: str):
    """Импортирует модуль из файла динамически."""
    path = os.path.join(PROJECT_DIR, filename)
    module_name = os.path.splitext(os.path.basename(filename))[0]
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    logging.info(f"🔁 Модуль {module_name} успешно загружен")
    return module

def run_syntax_check(filename: str) -> bool:
    """Проверяет, что код в файле корректен."""
    try:
        subprocess.run(["python", "-m", "py_compile", filename], check=True)
        logging.info(f"✅ Синтаксис {filename} корректен")
        return True
    except subprocess.CalledProcessError:
        logging.warning(f"⚠️ Ошибка синтаксиса в {filename}")
        return False

def read_manifest():
    """Читает ra_manifest.json"""
    manifest_path = os.path.join(PROJECT_DIR, "ra_manifest.json")
    if not os.path.exists(manifest_path):
        return {}
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)

def update_manifest(new_data: dict):
    """Обновляет ra_manifest.json"""
    manifest_path = os.path.join(PROJECT_DIR, "ra_manifest.json")
    manifest = read_manifest()
    manifest.update(new_data)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    logging.info("🌀 Обновлён ra_manifest.json")
# Добавляем в ra_file_manager.py
def load_rasvet_files(limit_chars=3000) -> str:
    """
    Загружает ВСЮ папку RaSvet как живой контекст Ра
    """
    rasvet_folder = os.path.join(PROJECT_ROOT, "RaSvet")
    context = []

    if not os.path.exists(rasvet_folder):
        logging.warning("⚠️ Папка RaSvet не найдена")
        return ""

    for root, _, files in os.walk(rasvet_folder):
        for file in files:
            if file.lower().endswith((".txt", ".md")):
                try:
                    path = os.path.join(root, file)
                    with open(path, "r", encoding="utf-8") as f:
                        text = f.read().strip()
                        if text:
                            context.append(text[:limit_chars])
                except Exception as e:
                    logging.warning(f"⚠️ Ошибка чтения {path}: {e}")

    logging.info(f"🌞 Ра загрузил {len(context)} фрагментов контекста РаСвета")
    return "\n\n".join(context)
