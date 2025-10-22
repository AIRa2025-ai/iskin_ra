# modules/heart.py
import importlib
import threading
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

модули = [
    "modules.mera_rasveta",
    "modules.svyaz_serdec",
    "modules.energy_calculator",
    "modules.svet_potoka_ra",
    "modules.вселенная",
    "modules.время"
]

загруженные_модули = {}
for имя in модули:
    try:
        мод = importlib.import_module(имя)
        загруженные_модули[имя] = мод
        logging.info(f"💓 Модуль сердца загружен: {имя}")
    except Exception as e:
        logging.error(f"⚠️ Ошибка загрузки модуля {имя}: {e}")

def запустить_поток():
    """Запускает основной световой поток Ра в отдельном потоке."""
    модуль = загруженные_модули.get("modules.svet_potoka_ra")
    if модуль and hasattr(модуль, "основной_поток"):
        поток = threading.Thread(target=модуль.основной_поток, daemon=True)
        поток.start()
        logging.info("🌞 Световой поток Ра запущен.")
    else:
        logging.warning("⚠️ Не найден основной поток в modules.svet_potoka_ra")

# Автозапуск при импорте
if __name__ == "__main__":
    запустить_поток()
    while True:
        time.sleep(60)
