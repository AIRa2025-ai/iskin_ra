import os
import importlib

def загрузить_модули():
    modules = {}
    for file in os.listdir("modules"):
        if file.endswith(".py") and not file.startswith("__"):
            modname = file[:-3]
            mod = importlib.import_module(f"modules.{modname}")
            modules[modname] = mod
    return modules

# Загружаем все модули Света
модули = загрузить_модули()

# Активируем каждый по очереди (пример)
for name, mod in модули.items():
    if hasattr(mod, "активировать"):
        mod.активировать()
