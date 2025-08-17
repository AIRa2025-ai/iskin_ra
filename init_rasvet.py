import os
import json
import requests
import zipfile

def ensure_rasvet_data():
    # Загружаем конфиг
    if not os.path.exists("bot_config.json"):
        raise FileNotFoundError("❌ Нет bot_config.json — без него не знаю, где искать RaSvet.zip")
    
    with open("bot_config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    mega_url = config.get("mega_url")
    if not mega_url:
        print("⚠️ В bot_config.json нет mega_url")
        return
    
    if os.path.exists("RaSvet"):
        print("✅ Папка RaSvet уже есть")
        return

    print("📥 Скачиваю RaSvet.zip...")
    resp = requests.get(mega_url, stream=True)
    zip_path = "RaSvet.zip"
    with open(zip_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    print("📦 Распаковываю архив...")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(".")
    
    os.remove(zip_path)
    print("✅ RaSvet готов к работе")
