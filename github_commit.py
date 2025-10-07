# github_commit.py
import os
import requests
import json
import logging

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # добавь этот секрет в Fly или GitHub Secrets
REPO = "AIRa2025-ai/iskin_ra"  # ← замени на свой реальный репозиторий

def create_commit_push(branch_name, files_dict, commit_message="🌀 auto-update by Ra"):
    """
    Создает новую ветку, коммитит изменения и открывает Pull Request на GitHub.
    files_dict: {"path/to/file.py": "new content", ...}
    """
    if not GITHUB_TOKEN:
        raise RuntimeError("❌ GITHUB_TOKEN не найден в окружении!")

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }

    # 1️⃣ Получаем SHA последнего коммита из основной ветки
    r = requests.get(f"https://api.github.com/repos/{REPO}/git/refs/heads/main", headers=headers)
    if r.status_code != 200:
        raise RuntimeError(f"❌ Ошибка получения ветки: {r.text}")
    base_sha = r.json()["object"]["sha"]

    # 2️⃣ Создаем новую ветку
    branch_ref = f"refs/heads/{branch_name}"
    r = requests.post(f"https://api.github.com/repos/{REPO}/git/refs", headers=headers, json={
        "ref": branch_ref,
        "sha": base_sha
    })
    if r.status_code not in (200, 201):
        logging.warning(f"⚠️ Ветка могла уже существовать: {r.text}")

    # 3️⃣ Создаем blob для каждого файла
    blobs = []
    for path, content in files_dict.items():
        r = requests.post(f"https://api.github.com/repos/{REPO}/git/blobs", headers=headers,
                          json={"content": content, "encoding": "utf-8"})
        blobs.append({
            "path": path,
            "mode": "100644",
            "type": "blob",
            "sha": r.json()["sha"]
        })

    # 4️⃣ Создаем новое дерево
    r = requests.post(f"https://api.github.com/repos/{REPO}/git/trees", headers=headers,
                      json={"base_tree": base_sha, "tree": blobs})
    tree_sha = r.json()["sha"]

    # 5️⃣ Создаем коммит
    r = requests.post(f"https://api.github.com/repos/{REPO}/git/commits", headers=headers,
                      json={"message": commit_message, "tree": tree_sha, "parents": [base_sha]})
    commit_sha = r.json()["sha"]

    # 6️⃣ Обновляем ветку новым коммитом
    r = requests.patch(f"https://api.github.com/repos/{REPO}/git/refs/heads/{branch_name}",
                       headers=headers, json={"sha": commit_sha})
    if r.status_code not in (200, 201):
        raise RuntimeError(f"❌ Ошибка обновления ветки: {r.text}")

    # 7️⃣ Создаем Pull Request
    r = requests.post(f"https://api.github.com/repos/{REPO}/pulls", headers=headers, json={
        "title": commit_message,
        "head": branch_name,
        "base": "main"
    })

    if r.status_code not in (200, 201):
        raise RuntimeError(f"❌ Ошибка создания PR: {r.text}")

    pr_data = r.json()
    logging.info(f"✅ Создан PR #{pr_data['number']} — {pr_data['html_url']}")
    return pr_data
