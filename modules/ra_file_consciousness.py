# modules/ra_file_consciousness.py

import os
import difflib
import shutil
import logging
from datetime import datetime, timezone
from pathlib import Path


class RaFileConsciousness:
    """
    Файловое сознание Ра.
    Совместимо со старой логикой + расширено для self-upgrade.
    """

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.backup_root = self.project_root / "backups"
        self.backup_root.mkdir(exist_ok=True)

        # 🔥 единый корень сознания (алиас для совместимости)
        self.root = self.project_root

        # карта осознанных файлов
        self.files = {}

        logging.info(f"[RaFileConsciousness] Инициализация. Корень: {self.project_root}")

    # -------------------------------
    # СКАНИРОВАНИЕ ФАЙЛОВ (ТВОЁ + УСИЛЕНО)
    # -------------------------------
    def scan(self):
        self.files.clear()

        for root, _, files in os.walk(self.root):
            if any(x in root for x in [".git", "__pycache__", "venv", "backups"]):
                continue

            for f in files:
                if f.endswith((".py", ".md", ".json", ".txt")):
                    path = Path(root) / f
                    try:
                        self.files[str(path.relative_to(self.project_root))] = {
                            "type": f.split(".")[-1],
                            "size": path.stat().st_size,
                            "mtime": path.stat().st_mtime,
                        }
                    except Exception:
                        continue

        logging.info(f"[RaFileConsciousness] Осознано файлов: {len(self.files)}")
        return self.files

    # -------------------------------
    # ПРОСТОЕ ПРИМЕНЕНИЕ ИДЕИ (СОВМЕСТИМО)
    # -------------------------------
    def apply_upgrade(self, idea: dict):
        """
        idea = {
            "type": "modify_file",
            "path": "modules/ra_thinker.py",
            "content": "...",
            "reason": "...",
        }
        """
        logging.info(f"🧬 Применяю улучшение: {idea.get('reason')}")

        if idea.get("type") != "modify_file":
            return

        path = idea.get("path")
        content = idea.get("content")

        if not path or content is None:
            logging.warning("[RaFileConsciousness] Некорректная идея улучшения")
            return

        self.apply_change(path, content, make_backup=True)

    # -------------------------------
    # ЧТЕНИЕ ФАЙЛА (ТВОЁ)
    # -------------------------------
    def read_file(self, relative_path: str) -> str:
        path = self.project_root / relative_path
        if not path.exists():
            raise FileNotFoundError(relative_path)

        return path.read_text(encoding="utf-8")

    # -------------------------------
    # BACKUP ФАЙЛА (ТВОЁ + UTC)
    # -------------------------------
    def backup_file(self, relative_path: str) -> Path:
        src = self.project_root / relative_path
        if not src.exists():
            raise FileNotFoundError(relative_path)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_dir = self.backup_root / timestamp
        backup_dir.mkdir(parents=True, exist_ok=True)

        dst = backup_dir / src.name
        shutil.copy2(src, dst)

        logging.info(f"🗂 Backup создан: {dst}")
        return dst

    # -------------------------------
    # DIFF ДО ПРИМЕНЕНИЯ (ТВОЁ)
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
    # БЕЗОПАСНОЕ ПРИМЕНЕНИЕ ИЗМЕНЕНИЙ (ТВОЁ)
    # -------------------------------
    def apply_change(self, relative_path: str, new_content: str, make_backup: bool = True):
        path = self.project_root / relative_path

        if make_backup and path.exists():
            self.backup_file(relative_path)

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(new_content, encoding="utf-8")

        logging.info(f"✍️ Изменён файл: {relative_path}")

    # -------------------------------
    # СОСТОЯНИЕ (НОВОЕ, НО НЕ ЛОМАЕТ)
    # -------------------------------
    def state(self) -> dict:
        return {
            "files_count": len(self.files),
            "root": str(self.project_root),
            "last_scan": datetime.now(timezone.utc).isoformat(),
        }

    # -------------------------------
    # СТАРТ (ТВОЁ)
    # -------------------------------
    def start(self):
        self.scan()
