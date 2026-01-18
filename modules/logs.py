# modules/logs.py
import sqlite3
from datetime import datetime
import threading

lock = threading.Lock()  # чтобы записи не пересекались

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

def log(message: str, level="INFO"):
    """Записывает событие в логи"""
    with lock:
        now = datetime.now().isoformat()
        c.execute("INSERT INTO logs VALUES (?, ?, ?)", (now, level, message))
        conn.commit()
    print(f"[{level}] {now} | {message}")

def log_info(message: str):
    log(message, "INFO")

def log_warning(message: str):
    log(message, "WARNING")

def log_error(message: str):
    log(message, "ERROR")
