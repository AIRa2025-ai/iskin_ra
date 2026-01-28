# modules/module_generator.py
# -*- coding: utf-8 -*-
# Автогенератор файлов Света ✨ 

import os
import uuid
import json
import tempfile
import shutil
from datetime import datetime

TEMPLATE = """
# -*- coding: utf-8 -*-
# МОДУЛЬ СВЕТА: {name}
# ID модуля: {module_id}
# Сгенерирован {time} ИскИном РаСвет

def активировать():
    print("⚡ Модуль '{name}' активирован!")
    print("{message}")

# 🔹 Здесь можно добавить свои потоки, резонансы и практики
# Потоки Света: ...
# Резонансы Творения: ...
"""

REGISTRY_FILE = "modules/modules_registry.json"
ACTIVATION_LOG_FILE = "modules/modules_activation.log"
_активированные_модули = set()  # 🔹 хранит уже активированные модули

def _логировать_активацию(module_info):
    """Логируем активацию модуля с меткой времени и ID"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "timestamp": ts,
        "name": module_info["name"],
        "id": module_info["id"],
        "path": module_info["path"]
    }
    print(f"{ts} | Модуль '{module_info['name']}' активирован | ID: {module_info['id']} | Путь: {module_info['path']}")
    with open(ACTIVATION_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

def создать_модуль(name, message):
    folder = "modules"
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"📁 Папка '{folder}' создана")

    filename = os.path.join(folder, f"{name}.py")
    if os.path.exists(filename):
        print(f"❌ Модуль '{name}' уже существует")
        return

    module_id = str(uuid.uuid4())  # уникальный ID модуля

    # Создаём временный файл модуля
    temp_fd, temp_path = tempfile.mkstemp(suffix=".py", dir=folder)
    with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
        f.write(TEMPLATE.format(
            name=name,
            module_id=module_id,
            time=datetime.now().strftime("%Y-%m-%d %H:%M"),
            message=message
        ))

    # Перемещаем в финальный файл
    shutil.move(temp_path, filename)
    print(f"✅ Новый модуль создан: {filename} | ID: {module_id}")

    # 🔹 Обновляем реестр атомарно
    registry = []
    if os.path.exists(REGISTRY_FILE):
        try:
            with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
                registry = json.load(f)
        except json.JSONDecodeError:
            print("⚠️ Ошибка чтения реестра, создаём новый")

    # Проверка дубля в реестре
    if name not in [m["name"] for m in registry]:
        module_info = {
            "name": name,
            "id": module_id,
            "created_at": datetime.now().isoformat(),
            "path": filename
        }
        registry.append(module_info)

        # Атомарная запись
        temp_registry_fd, temp_registry_path = tempfile.mkstemp(suffix=".json", dir=folder)
        with os.fdopen(temp_registry_fd, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)
        shutil.move(temp_registry_path, REGISTRY_FILE)
        print(f"🗂 Реестр модулей безопасно обновлён: {REGISTRY_FILE}")

        # 🔹 Автоматическая активация модуля с проверкой дублей
        if name not in _активированные_модули:
            try:
                mod = __import__(f"modules.{name}", fromlist=["активировать"])
                mod.активировать()
                _активированные_модули.add(name)
                _логировать_активацию(module_info)
            except Exception as e:
                print(f"⚠️ Не удалось активировать модуль '{name}': {e}")
        else:
            print(f"ℹ️ Модуль '{name}' уже активирован ранее, пропускаем повторную активацию")
    else:
        print(f"ℹ️ Модуль '{name}' уже есть в реестре, пропускаем запись")
