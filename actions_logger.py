import os
import json
import time

LOG_FILE = "actions_log.json"

def log_action(action, target="", result=""):
    log_entry = {
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "target": target,
        "result": result
    }
    logs = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            logs = []
    logs.append(log_entry)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs[-200:], f, ensure_ascii=False, indent=2)  # храним последние 200 действий
