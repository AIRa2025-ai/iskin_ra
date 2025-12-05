# scripts/create_shims_full.py
# -*- coding: utf-8 -*-
import re
import os  # noqa: F401
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
MODULES_DIR = ROOT / "modules"
LOG_TXT = ROOT / "scripts" / "create_shims_full.log"
LOG_JSON = ROOT / "scripts" / "create_shims_full.json"

# Находим все импорты модулей
imports_pattern = re.compile(
    r'from\s+modules\.([A-Za-z0-9_А-Яа-яёЁ]+)\s+import|import\s+modules\.([A-Za-z0-9_А-Яа-яёЁ]+)'
)

# Вызовы методов: module.foo(...)
method_call_pattern = re.compile(r'([A-Za-z0-9_А-Яа-яёЁ]+)\.([A-Za-z0-9_А-Яа-яёЁ]+)\(')
# from module import foo
direct_import_pattern = re.compile(r'from\s+modules\.([A-Za-z0-9_А-Яа-яёЁ]+)\s+import\s+([A-Za-z0-9_А-Яа-яёЁ]+)')

KNOWN_ALIASES = {
    "сердце": ["heart", "сердце"],
    "ra_downloader": ["ra_downloader_async", "ra_downloader"],
    "heart": ["сердце", "heart"],
}

TEMPLATE_CLASS = """# Автоматически созданный shim для: {modname}
class {class_name}:
    \"\"\"Заглушка для {modname} — заполните методами по необходимости.\"\"\"
    def __init__(self, *args, **kwargs):
        pass

{methods_stub}

    async def initialize(self):
        return True

def register(globals_dict=None):
    \"\"\"Optional register() used by autoloader.\"\"\"
    return True
"""

TEMPLATE_SIMPLE = """# Автоматически созданный shim для: {modname}
def log(msg):
    print("[{modname}] " + str(msg))
"""

def sanitize_class_name(name: str) -> str:
    name_ascii = re.sub(r'[^a-zA-Z0-9]', '', name)
    if not name_ascii:
        name_ascii = "ShimModule"
    return "".join(part.capitalize() for part in name_ascii.split("_"))

def find_module_names():
    found = set()
    for p in ROOT.rglob("*.py"):
        if any(x in str(p) for x in ("site-packages", ".venv", "venv")):
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

def write_logs(summary_txt, summary_json):
    LOG_TXT.parent.mkdir(parents=True, exist_ok=True)
    LOG_JSON.parent.mkdir(parents=True, exist_ok=True)
    with LOG_TXT.open("a", encoding="utf-8") as f:
        for line in summary_txt:
            f.write(line + "\n")
    with LOG_JSON.open("w", encoding="utf-8") as f:
        json.dump(summary_json, f, ensure_ascii=False, indent=2)

def try_find_existing(alias_list):
    for name in alias_list:
        candidate = MODULES_DIR / f"{name}.py"
        if candidate.exists():
            return candidate.name[:-3]
    return None

def extract_methods_usage(module_name: str):
    """Сканирует проект и собирает реально используемые методы для module_name."""
    methods = set()
    for p in ROOT.rglob("*.py"):
        if any(x in str(p) for x in ("site-packages", ".venv", "venv")):
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue

        # module.method()
        for m in method_call_pattern.finditer(text):
            mod, meth = m.groups()
            if mod == module_name:
                methods.add(meth)

        # from module import func
        for m in direct_import_pattern.finditer(text):
            mod, func = m.groups()
            if mod == module_name:
                methods.add(func)
    return sorted(methods)

def generate_methods_stub_dynamic(modname):
    methods = extract_methods_usage(modname)
    stub_lines = []
    for m in methods:
        stub_lines.append(f"    def {m}(self, *args, **kwargs):")
        stub_lines.append(f"        \"\"\"TODO: Реализовать метод {m}\"\"\"")
        stub_lines.append(f"        pass\n")
    return "\n".join(stub_lines) if stub_lines else "    # TODO: Добавьте методы по необходимости\n"

def create_shim(modname):
    target = MODULES_DIR / f"{modname}.py"
    if target.exists():
        return False
    if any(x in modname for x in ("logger", "config", "notify")):
        content = TEMPLATE_SIMPLE.format(modname=modname)
    else:
        class_name = sanitize_class_name(modname)
        methods_stub = generate_methods_stub_dynamic(modname)
        content = TEMPLATE_CLASS.format(modname=modname, class_name=class_name, methods_stub=methods_stub)
    target.write_text(content, encoding="utf-8")
    return True

def create_wrapper(wrapper_name, real_name):
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
        if name == "__init__":
            continue
        file_path = MODULES_DIR / f"{name}.py"
        if file_path.exists():
            continue

        alias_found = None
        for canonical, aliases in KNOWN_ALIASES.items():
            if name == canonical or name in aliases:
                alias_found = try_find_existing(aliases)
                if alias_found:
                    ok = create_wrapper(name, alias_found)
                    if ok:
                        wrapped.append(name)
                    break
        if alias_found:
            continue

        ok = create_shim(name)
        if ok:
            created.append(name)
        else:
            notes.append(f"Already exists: {name}.py")

    summary_txt = ["=== create_shims_full.py summary ==="]
    summary_txt += [f"Created shim: {x}" for x in created] or ["No shims created"]
    summary_txt += [f"Created wrapper: {x}" for x in wrapped]
    if notes:
        summary_txt += ["Notes:"] + notes

    summary_json = {
        "timestamp": datetime.now().isoformat(),
        "created": created,
        "wrapped": wrapped,
        "notes": notes
    }

    for line in summary_txt:
        print(line)
    write_logs(summary_txt, summary_json)
    print(f"\nLogs written to {LOG_TXT} and {LOG_JSON}")

if __name__ == "__main__":
    main()
