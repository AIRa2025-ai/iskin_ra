# modules/logs.py
import sqlite3
from datetime import datetime
import threading

lock = threading.Lock()

conn = sqlite3.connect('logs.db', check_same_thread=False)
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS logs (
    time TEXT,
    level TEXT,
    message TEXT
)
''')
conn.commit()


class Logger:
    def __init__(self):
        self.modules = {}
        self.events = {}

    # ------------------------
    # Методы логирования
    # ------------------------
    def log(self, message: str, level="INFO"):
        with lock:
            now = datetime.now().isoformat()
            c.execute("INSERT INTO logs VALUES (?, ?, ?)", (now, level, message))
            conn.commit()
        print(f"[{level}] {now} | {message}")

    def info(self, message: str):
        self.log(message, "INFO")

    def warning(self, message: str):
        self.log(message, "WARNING")

    def error(self, message: str):
        self.log(message, "ERROR")

    # ------------------------
    # Методы для RaSelfMaster
    # ------------------------
    def attach_module(self, name):
        self.modules[name] = True

    def on(self, event_name, callback):
        self.events[event_name] = callback


# ------------------------
# Готовый к использованию instance
# ------------------------
logger_instance = Logger()


# Вспомогательные функции для старого кода
def log_info(msg):
    logger_instance.info(msg)

def log_warning(msg):
    logger_instance.warning(msg)

def log_error(msg):
    logger_instance.error(msg)
