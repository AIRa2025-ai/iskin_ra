# ra_file_manager.py
import os
import importlib.util
import logging

PROJECT_DIR = os.path.dirname(__file__)

def list_project_files():
    return [f for f in os.listdir(PROJECT_DIR) if f.endswith(".py")]

def read_file_content(filename):
    path = os.path.join(PROJECT_DIR, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return None

def write_new_file(filename, content):
    path = os.path.join(PROJECT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    logging.info(f"✅ Создан новый файл: {filename}")

def import_module_dynamic(filename):
    path = os.path.join(PROJECT_DIR, filename)
    module_name = os.path.splitext(os.path.basename(filename))[0]
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
