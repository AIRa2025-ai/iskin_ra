# ra_file_core.py
import logging
from ra_file_manager import list_project_files, read_file_content, write_new_file, import_module_dynamic, run_syntax_check, load_rasvet_files
from ra_file_consciousness import RaFileConsciousness

logging.basicConfig(level=logging.INFO)

class RaFileCore:
    def __init__(self, project_root="."):
        self.manager = RaFileConsciousness(project_root)
        logging.info(f"[RaFileCore] Инициализация ядра файловой системы")

    # -------------------------------
    # ОСНОВНЫЕ ФУНКЦИИ
    # -------------------------------
    def scan_files(self):
        return self.manager.scan()

    def read_file(self, path):
        return self.manager.read_file(path)

    def write_file(self, path, content, backup=True):
        self.manager.apply_change(path, content, make_backup=backup)

    def backup_file(self, path):
        return self.manager.backup_file(path)

    def diff_file(self, path, new_content):
        return self.manager.diff_before_apply(path, new_content)

    def load_rasvet(self, limit_chars=3000):
        return load_rasvet_files(limit_chars)

    def import_module(self, path):
        return import_module_dynamic(path)

    def check_syntax(self, path):
        return run_syntax_check(path)
