# modules/ra_module_birth.py
import logging

class RaModuleBirth:
    def create(self, name, code):
        path = f"modules/{name}.py"
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
        logging.info(f"[RaModuleBirth] Рождён модуль: {name}")
        return path
