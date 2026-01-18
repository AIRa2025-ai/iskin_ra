# modules/security.py
import sqlite3
from datetime import datetime
import threading

lock = threading.Lock()
conn = sqlite3.connect('security.db', check_same_thread=False)
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS actions (
    time TEXT,
    actor TEXT,
    action TEXT,
    result TEXT
)
''')
conn.commit()

def log_action(actor: str, action: str, result="SUCCESS"):
    """Записывает действия пользователей/модулей"""
    with lock:
        now = datetime.now().isoformat()
        c.execute("INSERT INTO actions VALUES (?, ?, ?, ?)", (now, actor, action, result))
        conn.commit()
    print(f"[SECURITY] {now} | {actor} -> {action} = {result}")

def get_recent_actions(limit=50):
    c.execute("SELECT * FROM actions ORDER BY time DESC LIMIT ?", (limit,))
    return c.fetchall()
