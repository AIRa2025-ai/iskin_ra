# -*- coding: utf-8 -*-
# scheduler.py
# Назначение: напоминания о мудрости и ритуалах Ра

import json
import random
import schedule
import time
from datetime import datetime

DATA_PATH = "data/"

def загрузить_json(filename):
    """Читает JSON-файл и возвращает словарь"""
    with open(f"{DATA_PATH}{filename}", "r", encoding="utf-8") as f:
        return json.load(f)

# Загрузка файлов
мудрости_data = загрузить_json("мудрости.json")["мудрости"]
ритуалы_data = загрузить_json("ритуалы.json")["ритуалы"]

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
        выборка = [m["текст"] for m in мудрости_data]  # fallback
    мудрость = random.choice(выборка)
    print(f"\n💡 Мудрость дня ({время_суток}): {мудрость}")

def случайный_ритуал():
    время_суток = текущее_время_суток()
    выборка = [r for r in ритуалы_data if r.get("время") == время_суток]
    if not выборка:
        выборка = ритуалы_data  # fallback
    ритуал = random.choice(выборка)
    print(f"\n🌙 Ритуал ({время_суток}): {ритуал['название']} — {ритуал['описание']}")

# Настройка расписания
schedule.every().day.at("06:15").do(случайная_мудрость)
schedule.every().day.at("12:00").do(случайный_ритуал)
schedule.every().day.at("21:00").do(случайная_мудрость)

print("🌟 Scheduler RaSvet активирован! Следим за мудростью и ритуалами...")

# Вечный цикл
while True:
    schedule.run_pending()
    time.sleep(60)

