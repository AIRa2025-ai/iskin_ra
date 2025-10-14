import os

def collect_context(target_path='context.txt'):
    with open(target_path, 'w', encoding='utf-8') as context_file:
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.py') and 'venv' not in root:
                    full_path = os.path.join(root, file)
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            context_file.write(f"\n# --- {full_path} ---\n")
                            context_file.write(content + "\n")
                    except Exception as e:
                        print(f"⚠️ Не удалось прочитать {full_path}: {e}")

if __name__ == '__main__':
    collect_context()
