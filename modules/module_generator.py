# modules/module_generator.py
# -*- coding: utf-8 -*-
# Автогенератор файлов Света ✨ 

import os
import uuid
import json
from datetime import datetime
import tempfile
import shutil

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

    # Если всё ок, перемещаем в финальный файл
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

    registry.append({
        "name": name,
        "id": module_id,
        "created_at": datetime.now().isoformat(),
        "path": filename
    })

    # Атомарная запись в реестр через временный файл
    temp_registry_fd, temp_registry_path = tempfile.mkstemp(suffix=".json", dir=folder)
    with os.fdopen(temp_registry_fd, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
    shutil.move(temp_registry_path, REGISTRY_FILE)

    print(f"🗂 Реестр модулей безопасно обновлён: {REGISTRY_FILE}")
