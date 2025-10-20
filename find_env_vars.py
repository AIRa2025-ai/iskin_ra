import os
import re

# путь к корню проекта
project_root = "."

env_vars = set()

# проходимся по всем папкам и файлам
for dirpath, dirnames, filenames in os.walk(project_root):
    for filename in filenames:
        if filename.endswith(".py"):
            filepath = os.path.join(dirpath, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    matches = re.findall(r'os\.getenv\(["\'](.+?)["\']\)', content)
                    if matches:
                        env_vars.update(matches)
                        print(f"В {filepath} найдены переменные: {matches}")
            except Exception as e:
                print(f"Не удалось прочитать {filepath}: {e}")

print("\nВсе переменные окружения, используемые кодом:")
for var in sorted(env_vars):
    print(var)
