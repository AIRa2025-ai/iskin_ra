import os
import json
import logging
import subprocess
import zipfile


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

        # если архива нет — качаем
        if not os.path.exists(archive_path):
            logging.info(f"⬇️ Качаем {archive_path} из Mega...")
            try:
                subprocess.run(["megadl", mega_url, "--path", archive_path], check=True)
            except Exception as e:
                logging.error(f"❌ Ошибка при загрузке с Mega: {e}")
                return

        # распаковываем архив
        logging.info(f"📦 Распаковываем {archive_path}...")
        try:
            with zipfile.ZipFile(archive_path, "r") as zip_ref:
                zip_ref.extractall(knowledge_folder)
        except Exception as e:
            logging.error(f"❌ Ошибка при распаковке: {e}")
            return

        logging.info(f"🌞 RaSvet готов в папке {knowledge_folder}")

    except FileNotFoundError:
        logging.error("❌ Файл bot_config.json не найден!")
    except Exception as e:
        logging.error(f"❌ Ошибка в ensure_rasvet_data: {e}")
