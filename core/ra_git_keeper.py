# core/ra_git_keeper.py
import subprocess
import logging
from datetime import datetime

class RaGitKeeper:
    def __init__(self, repo_path="."):
        self.repo_path = repo_path

    # -------------------------------
    # Проверка git
    # -------------------------------
    def is_git_repo(self) -> bool:
        try:
            subprocess.check_output(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=self.repo_path
            )
            return True
        except Exception:
            return False

    # -------------------------------
    # Коммит от Ра
    # -------------------------------
    def commit(self, message: str):
        if not self.is_git_repo():
            logging.warning("[RaGitKeeper] Это не git-репозиторий")
            return False

        try:
            subprocess.check_call(["git", "add", "."], cwd=self.repo_path)

            full_message = f"🜂 Ра: {message} | {datetime.utcnow().isoformat()}"
            subprocess.check_call(
                ["git", "commit", "-m", full_message],
                cwd=self.repo_path
            )

            logging.info(f"🧬 [RaGitKeeper] Коммит создан: {message}")
            return True

        except subprocess.CalledProcessError as e:
            logging.warning(f"[RaGitKeeper] Git commit error: {e}")
            return False
