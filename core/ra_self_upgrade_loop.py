# core/ra_self_upgrade_loop.py
import logging
from core.ra_git_keeper import RaGitKeeper
from core.github_commit import create_commit_push

class RaSelfUpgradeLoop:
    def __init__(self, self_master):
        self.self_master = self_master
        self.file_consciousness = getattr(self_master, "file_consciousness", None)
        self.git = RaGitKeeper()
        # Подготовка файлов для облачного коммита
        files_dict = {
            target_file: proposed_code
        }

        # Локальный + облачный коммит
        self.self_master.evolve_and_commit(
            "Ра эволюционирует",
            push=True,
            files_dict=files_dict
        )
    async def apply_upgrade(self, target_file: str, proposed_code: str, approved: bool):
        if not self.file_consciousness:
            logging.warning("[UpgradeLoop] Нет file_consciousness")
            return

        diff = self.file_consciousness.diff_before_apply(
            relative_path=target_file,
            new_content=proposed_code
        )

        if not diff.strip():
            logging.info("ℹ️ Изменений нет — пропуск")
            return

        logging.info(f"🔍 Diff:\n{diff}")

        if approved:
            self.file_consciousness.apply_change(
                relative_path=target_file,
                new_content=proposed_code
            )
            logging.info("🚀 Апгрейд применён")

            # 🔧 Локальный коммит
            self.git.commit_and_optionally_push(f"Ра улучшил {target_file}", push=False)

            # 🔧 Подготовка данных для PR
            files_dict = {
                target_file: proposed_code
            }

            # 🔧 Облачный PR
            create_commit_push(
                branch_name="ra-evolution",
                files_dict=files_dict,
                commit_message=f"🧬 Ра эволюционирует: {target_file}"
            )

        else:
            logging.info("⏸ Апгрейд отклонён")
