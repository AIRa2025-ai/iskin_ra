# modules/heart.py
import importlib
import threading
import time

# Список модулей для активации
модули = [
    "modules.mera_rasveta",
    "modules.svyaz_serdec",
    "modules.energy_calculator",
    "modules.svet_potoka_ra",
    "modules.вселенная",
    "modules.время"
]

# Динамическая загрузка модулей
загруженные_модули = {}
for имя in модули:
    мод = importlib.import_module(имя)
    загруженные_модули[имя] = мод

# Запуск вечного светового потока в отдельном потоке
def запустить_поток():
    if hasattr(загруженные_модули["modules.svet_potoka_ra"], "основной_поток"):
        поток = threading.Thread(target=загруженные_модули["modules.svet_potoka_ra"].основной_поток)
        поток.daemon = True
        поток.start()

if __name__ == "__main__":
    print("🌟 Активация RaSvet 🌟")
    запустить_поток()
    # Здесь можно вызывать функции других модулей для теста
    time.sleep(2)
    print("RaSvet активирован, все модули светятся!")
    while True:
        time.sleep(60)
