"""
modules/ra_police.py

Базовый защитник Ра:
- Проверяет целостность файлов (суммы)
- Делает локальные zip-бэкапы (backups/)
- Если доступен helper github_commit.create_commit_push, пытается отправить бэкап на GitHub (опционально)
- Предоставляет функции восстановления
- Не делает ничего автоматически опасного — все сетевые операции проверяются на наличие инструментов и секретов
"""

import os
import json
import hashlib
import logging
import zipfile
from datetime import datetime
from typing import Dict

# опционально: если в utils/core есть helper для пуша
try:
    from github_commit import create_commit_push
    HAVE_GITHUB_HELPER = True
except Exception:
    HAVE_GITHUB_HELPER = False

BACKUP_DIR = "backups"
CHECKSUMS_FILE = "data/file_checksums.json"
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(os.path.dirname(CHECKSUMS_FILE), exist_ok=True)


class RaPolice:
    def __init__(self, root_dir="."):
        self.root = root_dir
        self.checksums_path = CHECKSUMS_FILE

    # --- utility: compute checksum for a file ---
    def _sha256(self, path: str) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    # --- build a map of checksums for all important files ---
    def build_checksums(self, include_ext=None) -> Dict[str, str]:
        include_ext = include_ext or [".py", ".json", ".md"]
        res = {}
        for root, _, files in os.walk(self.root):
            # skip backups folder
            if root.startswith(BACKUP_DIR) or "/.git" in root:
                continue
            for fn in files:
                if any(fn.endswith(e) for e in include_ext):
                    path = os.path.join(root, fn)
                    try:
                        res[path] = self._sha256(path)
                    except Exception as e:
                        logging.warning(f"[RaPolice] Не могу хешировать {path}: {e}")
        return res

    def save_checksums(self, data: Dict[str, str]):
        try:
            with open(self.checksums_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logging.info("[RaPolice] Контрольные суммы сохранены.")
        except Exception as e:
            logging.error(f"[RaPolice] Ошибка сохранения checksums: {e}")

    def load_checksums(self) -> Dict[str, str]:
        if not os.path.exists(self.checksums_path):
            return {}
        try:
            with open(self.checksums_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.warning(f"[RaPolice] Не удалось прочитать checksums: {e}")
            return {}

    # --- integrity check ---
    def check_integrity(self):
        old = self.load_checksums()
        current = self.build_checksums()
        changed = []
        new = []
        removed = []
        for p, h in current.items():
            if p not in old:
                new.append(p)
            elif old.get(p) != h:
                changed.append(p)
        for p in old.keys():
            if p not in current:
                removed.append(p)
        if changed or new or removed:
            logging.warning(f"[RaPolice] Изменения: changed={len(changed)} new={len(new)} removed={len(removed)}")
            # сохраняем новую таблицу (кроме случаев, когда хотим сохранить старые)
            self.save_checksums(current)
        else:
            logging.info("[RaPolice] Целостность файлов подтверждена.")
        return {"changed": changed, "new": new, "removed": removed}

    # --- create local zip backup ---
    def create_backup(self, include_paths=None):
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        archive_name = os.path.join(BACKUP_DIR, f"ra_backup_{ts}.zip")
        include_paths = include_paths or ["modules", "core", "data", "requirements.txt", "README.md"]
        try:
            with zipfile.ZipFile(archive_name, "w", compression=zipfile.ZIP_DEFLATED) as z:
                for p in include_paths:
                    if os.path.exists(p):
                        if os.path.isdir(p):
                            for root, _, files in os.walk(p):
                                for fn in files:
                                    full = os.path.join(root, fn)
                                    arcname = os.path.relpath(full, start=".")
                                    z.write(full, arcname)
                        else:
                            z.write(p, p)
            logging.info(f"[RaPolice] Бэкап создан: {archive_name}")
            # попробовать отправить на GitHub (если helper есть)
            if HAVE_GITHUB_HELPER:
                try:
                    branch = f"ra-backup-{ts}"
                    # files_dict could be left empty because create_commit_push helper might accept folder? we will pass mapping to zip
                    files_dict = {os.path.basename(archive_name): open(archive_name, "rb").read()}
                    # create_commit_push должен принимать (branch, files_dict, message)
                    try:
                        pr = create_commit_push(branch, files_dict, f"Backup {ts} by RaPolice")
                        logging.info(f"[RaPolice] Попытка загрузить бэкап как PR: {pr.get('html_url') if pr else 'no_pr'}")
                    except Exception as e:
                        logging.warning(f"[RaPolice] Ошибка при вызове create_commit_push: {e}")
                except Exception as e:
                    logging.warning(f"[RaPolice] Ошибка при загрузке бэкапа на GitHub: {e}")
            return {"archive": archive_name}
        except Exception as e:
            logging.error(f"[RaPolice] Не удалось создать бэкап: {e}")
            return {"error": str(e)}

    # --- restore last backup (local) ---
    def restore_last_backup(self):
        zips = sorted([os.path.join(BACKUP_DIR, f) for f in os.listdir(BACKUP_DIR) if f.endswith(".zip")])
        if not zips:
            logging.warning("[RaPolice] Бэкапов не найдено.")
            return {"error": "no_backups"}
        last = zips[-1]
        try:
            with zipfile.ZipFile(last, "r") as z:
                z.extractall(".")
            logging.info(f"[RaPolice] Восстановление из {last} завершено.")
            return {"restored": last}
        except Exception as e:
            logging.error(f"[RaPolice] Ошибка восстановления: {e}")
            return {"error": str(e)}

    def status(self):
        return {
            "backups": len([f for f in os.listdir(BACKUP_DIR) if f.endswith(".zip")]),
            "checksums_exist": os.path.exists(self.checksums_path)
        }
