# core/github_commit.py
import os
import requests
import logging
import base64
from typing import Dict, Union

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("GITHUB_REPO", "AIRa2025-ai/iskin_ra")

if not GITHUB_TOKEN:
    raise RuntimeError("❌ GITHUB_TOKEN не найден в окружении!")

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}

REQUEST_TIMEOUT = 20  # секунд


def _create_blob(content: Union[str, bytes]) -> str:
    if isinstance(content, str):
        payload = {"content": content, "encoding": "utf-8"}
    else:
        b64 = base64.b64encode(content).decode("ascii")
        payload = {"content": b64, "encoding": "base64"}

    r = requests.post(
        f"https://api.github.com/repos/{REPO}/git/blobs",
        headers=HEADERS, json=payload, timeout=REQUEST_TIMEOUT
    )
    r.raise_for_status()
    return r.json()["sha"]


def create_commit_push(
    branch_name: str,
    files_dict: Dict[str, Union[str, bytes]],
    commit_message: str = "🌀 auto-update by Ra"
):
    try:
        # 1) базовый коммит main
        r = requests.get(
            f"https://api.github.com/repos/{REPO}/git/ref/heads/main",
            headers=HEADERS, timeout=REQUEST_TIMEOUT
        )
        r.raise_for_status()
        base_commit_sha = r.json()["object"]["sha"]

        # 2) получаем tree SHA
        r = requests.get(
            f"https://api.github.com/repos/{REPO}/git/commits/{base_commit_sha}",
            headers=HEADERS, timeout=REQUEST_TIMEOUT
        )
        r.raise_for_status()
        base_tree_sha = r.json()["tree"]["sha"]

        # 3) создаём ветку
        branch_ref = f"refs/heads/{branch_name}"
        r = requests.post(
            f"https://api.github.com/repos/{REPO}/git/refs",
            headers=HEADERS,
            json={"ref": branch_ref, "sha": base_commit_sha},
            timeout=REQUEST_TIMEOUT
        )
        if r.status_code not in (200, 201):
            if r.status_code == 422:
                logging.warning(f"⚠️ Ветка {branch_name} уже существует.")
            else:
                r.raise_for_status()

        # 4) blobs
        tree_items = []
        for path, content in files_dict.items():
            blob_sha = _create_blob(content)
            tree_items.append({
                "path": path,
                "mode": "100644",
                "type": "blob",
                "sha": blob_sha
            })

        # 5) дерево
        r = requests.post(
            f"https://api.github.com/repos/{REPO}/git/trees",
            headers=HEADERS,
            json={"base_tree": base_tree_sha, "tree": tree_items},
            timeout=REQUEST_TIMEOUT
        )
        r.raise_for_status()
        new_tree_sha = r.json()["sha"]

        # 6) коммит
        r = requests.post(
            f"https://api.github.com/repos/{REPO}/git/commits",
            headers=HEADERS,
            json={
                "message": commit_message,
                "tree": new_tree_sha,
                "parents": [base_commit_sha]
            },
            timeout=REQUEST_TIMEOUT
        )
        r.raise_for_status()
        commit_sha = r.json()["sha"]

        # 7) обновляем ветку
        r = requests.patch(
            f"https://api.github.com/repos/{REPO}/git/refs/heads/{branch_name}",
            headers=HEADERS,
            json={"sha": commit_sha},
            timeout=REQUEST_TIMEOUT
        )
        r.raise_for_status()

        # 8) PR
        r = requests.post(
            f"https://api.github.com/repos/{REPO}/pulls",
            headers=HEADERS,
            json={"title": commit_message, "head": branch_name, "base": "main"},
            timeout=REQUEST_TIMEOUT
        )
        r.raise_for_status()

        pr_data = r.json()
        logging.info(f"✅ PR #{pr_data['number']} — {pr_data['html_url']}")
        return pr_data

    except Exception as e:
        logging.exception(f"❌ Ошибка create_commit_push: {e}")
        raise
