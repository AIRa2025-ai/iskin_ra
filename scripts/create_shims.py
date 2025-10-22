# scripts/create_shims.py
import re
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODULES_DIR = ROOT / "modules"
LOG = ROOT / "scripts" / "create_shims.log"

imports_pattern = re.compile(r'from\s+modules\.([A-Za-z0-9_А-Яа-яёЁ]+)\s+import|import\s+modules\.([A-Za-z0-9_А-Яа-яёЁ]+)')

# mapping of preferred canonical names -> possible existing filenames (to make wrappers)
KNOWN_ALIASES = {
    "сердце": ["heart", "сердце"],
    "ra_downloader": ["ra_downloader_async", "ra_downloader"],
    "heart": ["сердце", "heart"],
    # add more aliases if you renamed files before
}

TEMPLATE_CLASS = """# Автоматически созданный shim для: {modname}
# TODO: заменить на реальную реализацию

class {class_name}:
    \"\"\"Заглушка для {modname} — заполните методами по необходимости.\"\"\"
    def __init__(self, *args, **kwargs):
        pass

    async def initialize(self):
        return True

def register(globals_dict=None):
    \"\"\"Optional register() used by autoloader.\"\"\"
    return True
"""

TEMPLATE_SIMPLE = """# Автоматически созданный shim для: {modname}
# TODO: заменить на реальную реализацию

def log(msg):
    print("[{modname}] " + str(msg))
"""

def find_module_names():
    found = set()
    for p in ROOT.rglob("*.py"):
        # skip files in venv or .git
        if "site-packages" in str(p) or ".venv" in str(p) or "venv" in str(p):
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        for m in imports_pattern.finditer(text):
            name = m.group(1) or m.group(2)
            if name:
                found.add(name)
    return sorted(found)

def ensure_modules_dir():
    MODULES_DIR.mkdir(parents=True, exist_ok=True)

def write_log(lines):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        for l in lines:
            f.write(l + "\n")

def try_find_existing(alias_list):
    for name in alias_list:
        candidate = MODULES_DIR / f"{name}.py"
        if candidate.exists():
            return candidate.name[:-3]  # return the module name (without .py)
    return None

def create_shim(modname):
    target = MODULES_DIR / f"{modname}.py"
    if target.exists():
        return False
    # Choose template: if name looks like logger or config use simple
    if "logger" in modname or "config" in modname or "notify" in modname:
        content = TEMPLATE_SIMPLE.format(modname=modname)
    else:
        class_name = "".join([p.capitalize() for p in modname.split("_")])
        # If cyrillic - create ascii-friendly class name fallback
        if not class_name:
            class_name = "ShimModule"
        content = TEMPLATE_CLASS.format(modname=modname, class_name=class_name)
    target.write_text(content, encoding="utf-8")
    return True

def create_wrapper(wrapper_name, real_name):
    # create wrapper file wrapper_name.py that imports everything from real_name
    wrapper = MODULES_DIR / f"{wrapper_name}.py"
    if wrapper.exists():
        return False
    content = f"""# Wrapper shim: {wrapper_name} -> {real_name}
# Автоматически создано для совместимости импортов
from modules.{real_name} import *
"""
    wrapper.write_text(content, encoding="utf-8")
    return True

def main():
    ensure_modules_dir()
    module_names = find_module_names()
    created = []
    wrapped = []
    notes = []
    for name in module_names:
        # skip if it is the modules package itself
        if name == "__init__":
            continue
        file_path = MODULES_DIR / f"{name}.py"
        if file_path.exists():
            continue

        # if name in known aliases, try to find existing variant
        alias_found = None
        for canonical, aliases in KNOWN_ALIASES.items():
            if name == canonical or name in aliases:
                alias_found = try_find_existing(aliases)
                if alias_found:
                    # create wrapper under requested name pointing to alias_found
                    ok = create_wrapper(name, alias_found)
                    if ok:
                        wrapped.append(f"Created wrapper: {name}.py -> {alias_found}.py")
                    break

        if alias_found:
            continue

        ok = create_shim(name)
        if ok:
            created.append(f"Created shim: modules/{name}.py")
        else:
            notes.append(f"Already exists: modules/{name}.py")

    summary = []
    summary.append("=== create_shims.py summary ===")
    summary += created or ["No shims created"]
    summary += wrapped or []
    if notes:
        summary += ["Notes:"] + notes

    for line in summary:
        print(line)
    write_log(summary)
    print(f"\nWrote log to {LOG}")

if __name__ == "__main__":
    main()
