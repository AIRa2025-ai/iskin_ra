# modules/ra_file_consciousness.py
import os
import difflib
import shutil
import logging
from datetime import datetime
from pathlib import Path

class RaFileConsciousness:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.backup_root = self.project_root / "backups"
        self.backup_root.mkdir(exist_ok=True)
        self.root = root
        self.files = {}

    def scan(self):
        for root, _, files in os.walk(self.root):
            for f in files:
                if f.endswith((".py", ".md", ".json", ".txt")):
                    path = os.path.join(root, f)
                    self.files[path] = {
                        "type": f.split(".")[-1],
                        "size": os.path.getsize(path)
                    }
        logging.info(f"[RaFileConsciousness] Осознано файлов: {len(self.files)}")
        return self.files
        
    def apply_upgrade(self, idea: dict):
        logging.info(f"🧬 Применяю улучшение: {idea.get('reason')}")

    # -------------------------------
    # Чтение файла
    # -------------------------------
    def read_file(self, relative_path: str) -> str:
        path = self.project_root / relative_path
        if not path.exists():
            raise FileNotFoundError(relative_path)

        return path.read_text(encoding="utf-8")

    # -------------------------------
    # Backup файла
    # -------------------------------
    def backup_file(self, relative_path: str) -> Path:
        src = self.project_root / relative_path
        if not src.exists():
            raise FileNotFoundError(relative_path)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.backup_root / timestamp
        backup_dir.mkdir(parents=True, exist_ok=True)

        dst = backup_dir / src.name
        shutil.copy2(src, dst)

        logging.info(f"🗂 Backup создан: {dst}")
        return dst

    # -------------------------------
    # Diff ДО применения
    # -------------------------------
    def diff_before_apply(self, relative_path: str, new_content: str) -> str:
        old_content = self.read_file(relative_path).splitlines(keepends=True)
        new_content_lines = new_content.splitlines(keepends=True)

        diff = difflib.unified_diff(
            old_content,
            new_content_lines,
            fromfile=f"{relative_path} (before)",
            tofile=f"{relative_path} (after)",
            lineterm=""
        )

        return "".join(diff)

    # -------------------------------
    # Применение изменений (безопасно)
    # -------------------------------
    def apply_change(self, relative_path: str, new_content: str, make_backup: bool = True):
        path = self.project_root / relative_path

        if make_backup and path.exists():
            self.backup_file(relative_path)

        path.write_text(new_content, encoding="utf-8")
        logging.info(f"✍️ Изменён файл: {relative_path}")
        
    def start(self):
        self.scan()
