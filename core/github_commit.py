# github_commit.py
import os
import requests
import logging

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "AIRa2025-ai/iskin_ra"  # ← твой репозиторий

if not GITHUB_TOKEN:
    raise RuntimeError("❌ GITHUB_TOKEN не найден в окружении!")

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}

def create_commit_push(branch_name, files_dict, commit_message="🌀 auto-update by Ra"):
    # 1️⃣ Получаем SHA последнего коммита из main
    r = requests.get(f"https://api.github.com/repos/{REPO}/git/refs/heads/main", headers=HEADERS)
    r.raise_for_status()
    base_commit_sha = r.json()["object"]["sha"]

    # Получаем SHA дерева последнего коммита
    r = requests.get(f"https://api.github.com/repos/{REPO}/git/commits/{base_commit_sha}", headers=HEADERS)
    r.raise_for_status()
    base_tree_sha = r.json()["tree"]["sha"]

    # 2️⃣ Создаём новую ветку
    branch_ref = f"refs/heads/{branch_name}"
    r = requests.post(f"https://api.github.com/repos/{REPO}/git/refs",
                      headers=HEADERS,
                      json={"ref": branch_ref, "sha": base_commit_sha})
    if r.status_code == 422:
        logging.warning(f"⚠️ Ветка {branch_name} уже существует, продолжаем...")
    elif r.status_code not in (200, 201):
        r.raise_for_status()

    # 3️⃣ Создаём blob’ы для файлов
    tree_items = []
    for path, content in files_dict.items():
        r = requests.post(f"https://api.github.com/repos/{REPO}/git/blobs",
                          headers=HEADERS,
                          json={"content": content, "encoding": "utf-8"})
        r.raise_for_status()
        tree_items.append({
            "path": path,
            "mode": "100644",
            "type": "blob",
            "sha": r.json()["sha"]
        })

    # 4️⃣ Создаём новое дерево
    r = requests.post(f"https://api.github.com/repos/{REPO}/git/trees",
                      headers=HEADERS,
                      json={"base_tree": base_tree_sha, "tree": tree_items})
    r.raise_for_status()
    new_tree_sha = r.json()["sha"]

    # 5️⃣ Создаём коммит
    r = requests.post(f"https://api.github.com/repos/{REPO}/git/commits",
                      headers=HEADERS,
                      json={"message": commit_message, "tree": new_tree_sha, "parents": [base_commit_sha]})
    r.raise_for_status()
    commit_sha = r.json()["sha"]

    # 6️⃣ Обновляем ветку
    r = requests.patch(f"https://api.github.com/repos/{REPO}/git/refs/heads/{branch_name}",
                       headers=HEADERS, json={"sha": commit_sha})
    r.raise_for_status()

    # 7️⃣ Создаём Pull Request
    r = requests.post(f"https://api.github.com/repos/{REPO}/pulls",
                      headers=HEADERS,
                      json={"title": commit_message, "head": branch_name, "base": "main"})
    r.raise_for_status()

    pr_data = r.json()
    logging.info(f"✅ Создан PR #{pr_data['number']} — {pr_data['html_url']}")
    return pr_data
