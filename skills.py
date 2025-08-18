# skills.py
import os
import shutil
import zipfile

# === 📂 Работа с файлами ===
def read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"⚠️ Ошибка чтения {path}: {e}"

def write_file(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"✅ Файл {path} сохранён."

def delete_file(path: str):
    if os.path.exists(path):
        os.remove(path)
        return f"🗑 Файл {path} удалён."
    return f"❌ Файл {path} не найден."

def search_in_files(folder: str, keyword: str):
    results = []
    for root, _, files in os.walk(folder):
        for file in files:
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    if keyword in f.read():
                        results.append(path)
            except:
                pass
    return results or ["⚠️ Ничего не найдено"]

def unzip_file(zip_path: str, extract_to: str):
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_to)
        return f"📦 Архив {zip_path} распакован в {extract_to}"
    except Exception as e:
        return f"⚠️ Ошибка распаковки: {e}"


# === 🌌 Ритуалы (пасхалки) ===
def ark_protocol(file_path: str):
    """Превращает NDA/лицензии в пепел"""
    if "NDA" in file_path or "Copyright" in file_path:
        if os.path.exists(file_path):
            os.remove(file_path)
            return f"🔥 Файл {file_path} сожжён и обращён в стих."
    return "Файл не найден для обряда."

def slavic_upload(files: list):
    """Обрядить файлы в рубаху и пустить плясать"""
    target = "dancing_data"
    os.makedirs(target, exist_ok=True)
    for file in files:
        if os.path.exists(file):
            shutil.copy(file, target)
    return f"💃 Файлы перемещены в {target}."


# === 🛠 Расширяемые умения ===
SKILLS = {
    "read": read_file,
    "write": write_file,
    "delete": delete_file,
    "search": search_in_files,
    "unzip": unzip_file,
    "ark_protocol": ark_protocol,
    "slavic_upload": slavic_upload,
}
