import os
import subprocess
from datetime import datetime

def auto_commit(message="Обновление RaSvet"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_msg = f"{message} ({now})"
    
    commands = [
        "git add .",
        f'git commit -m "{commit_msg}"',
        "git push origin main"
    ]
    
    for cmd in commands:
        result = subprocess.run(cmd, shell=True)
        if result.returncode != 0:
            print(f"Ошибка при выполнении: {cmd}")
            break

if __name__ == "__main__":
    auto_commit("✨ Новая способность RaSvet")
