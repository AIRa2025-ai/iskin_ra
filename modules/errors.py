# modules/errors.py
import sqlite3
from datetime import datetime
import threading

lock = threading.Lock()
conn = sqlite3.connect('errors.db', check_same_thread=False)
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS errors (
    time TEXT,
    severity TEXT,
    module TEXT,
    description TEXT
)
''')
conn.commit()

def report_error(module: str, description: str, severity="CRITICAL"):
    """Записывает ошибку"""
    with lock:
        now = datetime.now().isoformat()
        c.execute("INSERT INTO errors VALUES (?, ?, ?, ?)", (now, severity, module, description))
        conn.commit()
    print(f"[ERROR-{severity}] {now} | {module}: {description}")

def get_errors(limit=50):
    c.execute("SELECT * FROM errors ORDER BY time DESC LIMIT ?", (limit,))
    return c.fetchall()
