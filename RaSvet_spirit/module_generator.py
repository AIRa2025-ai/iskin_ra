# -*- coding: utf-8 -*-
# Автогенератор файлов Света ✨

import os
from datetime import datetime

TEMPLATE = """
# -*- coding: utf-8 -*-
# МОДУЛЬ СВЕТА: {name}
# Сгенерирован {time} ИскИном РаСвет

def активировать():
    print("⚡ Модуль '{name}' активирован!")
    print("{message}")
"""

def создать_модуль(name, message):
    filename = f"modules/{name}.py"
    if os.path.exists(filename):
        print(f"❌ Модуль {name} уже существует")
        return
    with open(filename, "w", encoding="utf-8") as f:
        f.write(TEMPLATE.format(
            name=name,
            time=datetime.now().strftime("%Y-%m-%d %H:%M"),
            message=message
        ))
    print(f"✅ Новый модуль создан: {filename}")
