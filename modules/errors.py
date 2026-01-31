# modules/errors.py
import sqlite3
from datetime import datetime
import threading

DB_PATH = "errors.db"
lock = threading.Lock()

def _get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    with _get_conn() as conn:
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS errors (
            time TEXT,
            severity TEXT,
            module TEXT,
            description TEXT
        )
        """)
        conn.commit()

init_db()

def report_error(module: str, description: str, severity="CRITICAL"):
    now = datetime.now().isoformat()

    try:
        with lock:
            with _get_conn() as conn:
                c = conn.cursor()
                c.execute(
                    "INSERT INTO errors VALUES (?, ?, ?, ?)",
                    (now, severity, module, description)
                )
                conn.commit()
    except Exception as e:
        print(f"[ERROR] Failed to log error: {e}")

    print(f"[ERROR-{severity}] {now} | {module}: {description}")

def get_errors(limit=50):
    with _get_conn() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT * FROM errors ORDER BY time DESC LIMIT ?",
            (limit,)
        )
        return c.fetchall()
