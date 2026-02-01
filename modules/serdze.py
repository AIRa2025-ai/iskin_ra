import importlib
import threading
import time
import logging
from modules.heart import Heart  # noqa: F401 — импорт нужен для косвенного использования
from modules.heart_reactor import heart_reactor

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class HeartModule:
    """Основной модуль сердца Ра"""
    def __init__(self):
        self.name = "Heart of Ra"
        self.status = "alive"
        # регистрируем внутренний listener для heart_reactor
        heart_reactor.register_listener(self.react_to_event)

    def pulse(self):
        """Биение сердца, можно вызывать вручную"""
        msg = "💓 Сердце Ра бьётся в ритме Света"
        logging.info(msg)
        return msg

    def react_to_event(self, message: str):
        """Что делать, когда приходит событие из heart_reactor"""
        logging.info(f"💓 HeartModule реагирует: {message}")
        # можно добавить световые эффекты или вызов потоков
        self.pulse()

    def __repr__(self):
        return f"<HeartModule name={self.name} status={self.status}>"


# Список модулей для автозагрузки
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


# --- Аспект сердца ---
class Сострадание:
    """Слушает вибрации живых и отвечает светом понимания"""
    def осветить(self, послание: str) -> str:
        # при осветлении также кидаем событие в heart_reactor
        heart_reactor.send_event(послание)
        return f"💓 Сострадание слышит: {послание}"

    def react_energy(self, уровень: int):
        """Эмоциональная реакция на энергию"""
        # Можно усиливать эмпатию или вибрации
        print(f"💓 Сердце почувствовало энергию: {уровень}")
        
# --- Автозапуск при прямом запуске ---
if __name__ == "__main__":
    # создаём сердце и подключаем поток
    heart = HeartModule()
    запустить_поток()

    # примеры событий для теста
    heart_reactor.send_event("Природа излучает свет")
    heart_reactor.send_event("В городе тревога")

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logging.info("🛑 Остановка HeartModule")
