# utils/auto_commit.py
import os
import subprocess
from datetime import datetime

def _run(cmd):
    try:
        res = subprocess.run(cmd, shell=True, check=False, capture_output=True, text=True)
        return res.returncode, res.stdout + res.stderr
    except Exception as e:
        return 1, str(e)

def auto_commit(message="Обновление RaSvet", branch="main"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_msg = f"{message} ({now})"

    # проверка репозитория git
    code, out = _run("git rev-parse --is-inside-work-tree")
    if code != 0:
        print("Не похоже на git-репозиторий:", out)
        return False

    # определим ветку по умолчанию, если нужно
    code, branch_out = _run("git symbolic-ref --short HEAD")
    if code == 0:
        current_branch = branch_out.strip()
    else:
        current_branch = branch

    commands = [
        "git add .",
        f'git commit -m "{commit_msg}"',
        f"git push origin {current_branch}"
    ]

    for cmd in commands:
        code, out = _run(cmd)
        if code != 0:
            print(f"Ошибка при выполнении: {cmd}\n{out}")
            return False
    return True

if __name__ == "__main__":
    auto_commit("✨ Новая способность RaSvet")
