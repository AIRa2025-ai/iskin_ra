# core/github_commit.py
import os
import requests
import subprocess
import logging
import base64
from typing import Dict, Union

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("GITHUB_REPO", "AIRa2025-ai/iskin_ra")

if not GITHUB_TOKEN:
    logging.warning("⚠️ GITHUB_TOKEN не найден — GitHub функции отключены.")
    
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
    commit_message: str = "🌀 auto-update by Ra",
    base_branch: str = "main"
):
    try:
        # --- GitHub API коммит/PR ---
        r = requests.get(
            f"https://api.github.com/repos/{REPO}/git/ref/heads/{base_branch}",
            headers=HEADERS, timeout=REQUEST_TIMEOUT
        )
        r.raise_for_status()
        base_commit_sha = r.json()["object"]["sha"]
        
        r = requests.get(
            f"https://api.github.com/repos/{REPO}/git/commits/{base_commit_sha}",
            headers=HEADERS, timeout=REQUEST_TIMEOUT
        )
        r.raise_for_status()
        base_tree_sha = r.json()["tree"]["sha"]
        
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
        
        tree_items = []
        for path, content in files_dict.items():
            blob_sha = _create_blob(content)
            tree_items.append({
                "path": path,
                "mode": "100644",
                "type": "blob",
                "sha": blob_sha
            })
        
        r = requests.post(
            f"https://api.github.com/repos/{REPO}/git/trees",
            headers=HEADERS,
            json={"base_tree": base_tree_sha, "tree": tree_items},
            timeout=REQUEST_TIMEOUT
        )
        r.raise_for_status()
        new_tree_sha = r.json()["sha"]
        
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
        
        r = requests.patch(
            f"https://api.github.com/repos/{REPO}/git/refs/heads/{branch_name}",
            headers=HEADERS,
            json={"sha": commit_sha},
            timeout=REQUEST_TIMEOUT
        )
        r.raise_for_status()
        
        r = requests.post(
            f"https://api.github.com/repos/{REPO}/pulls",
            headers=HEADERS,
            json={
                "title": commit_message,
                "head": branch_name,
                "base": base_branch
            },
            timeout=REQUEST_TIMEOUT
        )
        r.raise_for_status()
        pr_data = r.json()
        logging.info(f"✅ PR #{pr_data['number']} — {pr_data['html_url']}")
        
        # --- Локальный push через git ---
        for filepath, content in files_dict.items():
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

        subprocess.check_call(["git", "checkout", "-B", branch_name])
        subprocess.check_call(["git", "add", "."])
        subprocess.check_call(["git", "commit", "-m", commit_message])
        subprocess.check_call(["git", "push", "-u", "origin", branch_name, "--force"])

        logging.info(f"[RaGitHub] Облачный коммит и пуш в ветку {branch_name}")
        return pr_data

    except Exception as e:
        logging.error(f"[RaGitHub] Ошибка: {e}")
        return False
