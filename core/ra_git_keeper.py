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
    # Есть ли изменения
    # -------------------------------
    def has_changes(self) -> bool:
        try:
            out = subprocess.check_output(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path
            ).decode().strip()
            return bool(out)
        except Exception:
            return False

    # -------------------------------
    # Коммит от Ра
    # -------------------------------
    def commit(self, message: str):
        if not self.is_git_repo():
            logging.warning("[RaGitKeeper] Это не git-репозиторий")
            return False

        if not self.has_changes():
            logging.info("[RaGitKeeper] Нет изменений для коммита")
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

    # -------------------------------
    # Push (опционально)
    # -------------------------------
    def push(self, remote="origin", branch="main"):
        try:
            subprocess.check_call(
                ["git", "push", remote, branch],
                cwd=self.repo_path
            )
            logging.info(f"[RaGitKeeper] Успешный push в {remote}/{branch}")
            return True
        except subprocess.CalledProcessError as e:
            logging.warning(f"[RaGitKeeper] Git push error: {e}")
            return False

    # -------------------------------
    # Коммит + push по желанию
    # -------------------------------
    def commit_and_optionally_push(self, message: str, push=False):
        committed = self.commit(message)
        if committed and push:
            return self.push()
        return committed
