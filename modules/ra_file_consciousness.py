# modules/ra_file_consciousness.py
import os
import logging

class RaFileConsciousness:
    def __init__(self, root="."):
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

    def start(self):
        self.scan()
