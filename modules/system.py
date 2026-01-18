# modules/system.py
import sqlite3
from datetime import datetime
import platform
import psutil
import threading

lock = threading.Lock()
conn = sqlite3.connect('system.db', check_same_thread=False)
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS system_info (
    time TEXT,
    key TEXT,
    value TEXT
)
''')
conn.commit()

def record_system_info():
    """Записывает текущее состояние системы"""
    with lock:
        now = datetime.now().isoformat()
        info = {
            "platform": platform.platform(),
            "cpu_count": str(psutil.cpu_count()),
            "memory_total": str(psutil.virtual_memory().total),
            "memory_available": str(psutil.virtual_memory().available),
            "disk_total": str(psutil.disk_usage('/').total),
            "disk_free": str(psutil.disk_usage('/').free),
        }
        for key, value in info.items():
            c.execute("INSERT INTO system_info VALUES (?, ?, ?)", (now, key, value))
        conn.commit()
    print(f"[SYSTEM] {now} | System info recorded.")

def get_recent_info(limit=20):
    c.execute("SELECT * FROM system_info ORDER BY time DESC LIMIT ?", (limit,))
    return c.fetchall()
