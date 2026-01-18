import logging


class RaSelfUpgradeLoop:
    def __init__(self, self_master):
        self.self_master = self_master
        self.file_consciousness = getattr(self_master, "file_consciousness", None)

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
        else:
            logging.info("⏸ Апгрейд отклонён")
