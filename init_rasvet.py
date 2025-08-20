import os
import json
import logging
import zipfile
import requests

def ensure_rasvet_data():
    """
    Проверяет наличие папки RaSvet.
    Если её нет — качает архив с Mega и распаковывает.
    """
    try:
        # читаем конфиг
        with open("bot_config.json", "r", encoding="utf-8") as f:
            config = json.load(f)

        mega_url = config.get("mega_url")
        knowledge_folder = config.get("knowledge_folder", "RaSvet")
        archive_path = "RaSvet.zip"

        # если папка уже есть — выходим
        if os.path.exists(knowledge_folder):
            logging.info(f"✅ Папка {knowledge_folder} уже существует, пропускаем загрузку.")
            return

        # качаем архив, если его нет
        if not os.path.exists(archive_path):
            logging.info(f"⬇️ Качаем архив из Mega...")
            try:
                response = requests.get(mega_url, stream=True)
                response.raise_for_status()
                with open(archive_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
            except Exception as e:
                logging.error(f"❌ Ошибка при загрузке: {e}")
                return

        # распаковываем архив
        logging.info(f"📦 Распаковываем {archive_path}...")
        try:
            with zipfile.ZipFile(archive_path, "r") as zip_ref:
                zip_ref.extractall(knowledge_folder)
            os.remove(archive_path)  # удаляем архив после распаковки
        except Exception as e:
            logging.error(f"❌ Ошибка при распаковке: {e}")
            return

        logging.info(f"🌞 RaSvet готов в папке {knowledge_folder}")

    except FileNotFoundError:
        logging.error("❌ Файл bot_config.json не найден!")
    except Exception as e:
        logging.error(f"❌ Ошибка в ensure_rasvet_data: {e}")
