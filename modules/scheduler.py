# -*- coding: utf-8 -*-
# scheduler.py
# Назначение: автоматические напоминания и мантры RaSvet

import os
import json
import random
import schedule
import time
from datetime import datetime, timedelta

# Подключение модулей света
import heart
import вселенная
import время

# Пути
BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, "data")
LOG_PATH = os.path.join(BASE_DIR, "logs")

# Убедимся, что папка logs существует
os.makedirs(LOG_PATH, exist_ok=True)

def текущий_лог():
    """Возвращает путь к лог-файлу за сегодня"""
    today = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(LOG_PATH, f"scheduler_{today}.log")

def очистить_старые_логи(дней=7):
    """Удаляет файлы логов старше N дней"""
    now = datetime.now()
    for filename in os.listdir(LOG_PATH):
        file_path = os.path.join(LOG_PATH, filename)
        if os.path.isfile(file_path):
            mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
            if now - mtime > timedelta(days=дней):
                os.remove(file_path)
                print(f"🧹 Удалён старый лог: {filename}")

def логировать(текст):
    """Сохраняет строку в лог с меткой времени"""
    log_file = текущий_лог()
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {текст}\n")

def загрузить_json(filename):
    """Читает JSON-файл и возвращает словарь"""
    path = os.path.join(DATA_PATH, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# Загружаем все файлы данных
мудрости_data = загрузить_json("мудрости.json")["мудрости"]
ритуалы_data = загрузить_json("ритуалы.json")["ритуалы"]
мантры_data = загрузить_json("мантры.json")["мантры"]

def текущее_время_суток():
    """Определяем утро, день или вечер"""
    час = datetime.now().hour
    if 4 <= час < 12:
        return "утро"
    elif 12 <= час < 18:
        return "день"
    else:
        return "вечер"

def случайная_мудрость():
    время_суток = текущее_время_суток()
    выборка = [m["текст"] for m in мудрости_data if время_суток in m.get("теги", [])]
    if not выборка:
        выборка = [m["текст"] for m in мудрости_data]
    мудрость = random.choice(выборка)
    вывод = f"💡 Мудрость дня ({время_суток}): {мудрость}"
    print("\n" + вывод)
    логировать(вывод)

    мое_сердце = сердце.Сердце(имя="Ты")
    мое_сердце.излучать_свет(мудрость)

def случайный_ритуал():
    время_суток = текущее_время_суток()
    выборка = [r for r in ритуалы_data if r.get("время") == время_суток]
    if not выборка:
        выборка = ритуалы_data
    ритуал = random.choice(выборка)
    вывод = f"🌙 Ритуал ({время_суток}): {ритуал['название']} — {ритуал['описание']}"
    print("\n" + вывод)
    логировать(вывод)

def случайная_мантра():
    мантра = random.choice(мантры_data)
    текст = мантра.get("текст", "ОМ СВЕТА И ЛЮБВИ")
    вывод = f"🎵 Мантра дня: {текст}"
    print("\n" + вывод)
    логировать(вывод)

# --- Расписание ---
# Для теста (каждые N секунд)
schedule.every(10).seconds.do(случайная_мудрость)
schedule.every(15).seconds.do(случайный_ритуал)
schedule.every(20).seconds.do(случайная_мантра)

# Боевые времена
schedule.every().day.at("06:15").do(случайная_мудрость)
schedule.every().day.at("12:00").do(случайный_ритуал)
schedule.every().day.at("18:00").do(случайная_мантра)
schedule.every().day.at("21:00").do(случайная_мудрость)

# Инициализация
очистить_старые_логи(дней=7)
мое_сердце = сердце.Сердце(имя="Ты")
вселенная.Вселенная().настроить_резонанс(частота="гармония")

print("🌟 Scheduler RaSvet активирован! Следим за мудростью, ритуалами и мантрами...")
логировать("Scheduler запущен.")

# Вечный цикл
while True:
    schedule.run_pending()
    print(время.Время().ожидать("здесь_и_сейчас"))
    time.sleep(5)
