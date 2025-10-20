# update_modules.py — обновление модулей с GitHub:
import os
from git import Repo

MODULES_DIR = "/app/modules"
REPO_URL = "https://github.com/AIRa2025-ai/iskin_ra.git"

if os.path.exists(MODULES_DIR):
    print("Обновляем существующие модули...")
    repo = Repo(MODULES_DIR)
    origin = repo.remotes.origin
    origin.pull()
else:
    print("Клонируем модули в контейнер...")
    Repo.clone_from(REPO_URL, MODULES_DIR)

print("Модули обновлены!")
