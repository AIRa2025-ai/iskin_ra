# github_commit.py
import os, base64, requests, json

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "youruser/yourrepo"

def create_commit_push(branch_name, files_dict, commit_message="auto-update by Ra"):
    """
    files_dict: {"path/filename.py": "file content", ...}
    """
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    # 1) get default branch and latest sha
    r = requests.get(f"https://api.github.com/repos/{REPO}", headers=headers)
    repo = r.json()
    default_branch = repo["default_branch"]
    r = requests.get(f"https://api.github.com/repos/{REPO}/git/refs/heads/{default_branch}", headers=headers)
    base_sha = r.json()["object"]["sha"]

    # 2) create new branch
    payload = {"ref": f"refs/heads/{branch_name}", "sha": base_sha}
    requests.post(f"https://api.github.com/repos/{REPO}/git/refs", headers=headers, json=payload)

    # 3) for each file create blob
    blobs = []
    for path, content in files_dict.items():
        r = requests.post(f"https://api.github.com/repos/{REPO}/git/blobs", headers=headers,
                          json={"content": content, "encoding": "utf-8"})
        blobs.append({"path": path, "mode": "100644", "type": "blob", "sha": r.json()["sha"]})

    # 4) create tree
    r = requests.post(f"https://api.github.com/repos/{REPO}/git/trees", headers=headers,
                      json={"base_tree": base_sha, "tree": blobs})
    tree_sha = r.json()["sha"]

    # 5) create commit
    r = requests.post(f"https://api.github.com/repos/{REPO}/git/commits", headers=headers,
                      json={"message": commit_message, "tree": tree_sha, "parents": [base_sha]})
    commit_sha = r.json()["sha"]

    # 6) update ref
    requests.patch(f"https://api.github.com/repos/{REPO}/git/refs/heads/{branch_name}", headers=headers,
                   json={"sha": commit_sha})
    # 7) create PR
    pr = requests.post(f"https://api.github.com/repos/{REPO}/pulls", headers=headers,
                       json={"title": commit_message, "head": branch_name, "base": default_branch})
    return pr.json()
