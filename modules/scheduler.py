# -*- coding: utf-8 -*-
# scheduler.py — поток мудрости и ритма RaSvet (обновлён: использует serdze, vselennaya, vremya)

import os
import json
import random
import schedule
import time
from datetime import datetime, timedelta

# --- Импорт внутренних модулей (латиницей) ---
# Если модуль отсутствует — не ломаем работу, логируем мягко.
_serdze = None
_vselennaya = None
_vremya = None

try:
    import serdze as _serdze
except Exception:
    try:
        import сердце as _serdze  # fallback if still russian-named file exists
    except Exception:
        _serdze = None

try:
    import vselennaya as _vselennaya
except Exception:
    try:
        import вселенная as _vselennaya
    except Exception:
        _vselennaya = None

try:
    import vremya as _vremya
except Exception:
    try:
        import время as _vremya
    except Exception:
        _vremya = None

# --- Пути ---
BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, "data")
LOG_PATH = os.path.join(BASE_DIR, "logs")

os.makedirs(LOG_PATH, exist_ok=True)

# ----------------------------------------------------
# 🔥 УТИЛИТЫ
# ----------------------------------------------------

def текущий_лог():
    today = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(LOG_PATH, f"scheduler_{today}.log")


def очистить_старые_логи(дней=7):
    now = datetime.now()
    for filename in os.listdir(LOG_PATH):
        file_path = os.path.join(LOG_PATH, filename)
        if not os.path.isfile(file_path):
            continue
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
            if now - mtime > timedelta(days=дней):
                os.remove(file_path)
                print(f"🧹 Удалён старый лог: {filename}")
        except Exception:
            pass


def логировать(текст):
    try:
        with open(текущий_лог(), "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {текст}\n")
    except Exception as e:
        print(f"⚠️ Ошибка логирования: {e}")


def загрузить_json(filename):
    path = os.path.join(DATA_PATH, filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Не удалось загрузить {filename}: {e}")
        return {}

# ----------------------------------------------------
# 🔥 ЗАГРУЗКА ДАННЫХ
# ----------------------------------------------------

мудрости_data = загрузить_json("мудрости.json").get("мудрости", [])
ритуалы_data = загрузить_json("ритуалы.json").get("ритуалы", [])
мантры_data = загрузить_json("мантры.json").get("мантры", [])

# ----------------------------------------------------
# 🔥 ВСПОМОГАТЕЛИ ДЛЯ ВЫЗОВА МЕТОДОВ ИЗ МОДУЛЕЙ
# ----------------------------------------------------

def _emit_light_through_serdze(text: str):
    """Пытаемся мягко вызвать метод, который излучает/публикует мудрость в серdze."""
    if not _serdze:
        return
    # Попробуем разные варианты имён классов/методов — не падаем.
    try:
        # try common latin names
        if hasattr(_serdze, "Serdze"):
            obj = _serdze.Serdze(имя="Ты")
        elif hasattr(_serdze, "Heart"):
            obj = _serdze.Heart(имя="Ты")
        elif hasattr(_serdze, "HeartModule"):
            obj = _serdze.HeartModule()
        elif hasattr(_serdze, "Сердце"):
            obj = _serdze.Сердце(имя="Ты")
        else:
            obj = None

        if obj:
            if hasattr(obj, "излучать_свет"):
                try:
                    obj.излучать_свет(text)
                except Exception:
                    pass
            elif hasattr(obj, "emit_light"):
                try:
                    obj.emit_light(text)
                except Exception:
                    pass
    except Exception:
        pass


def _setup_vselennaya_resonance():
    """Пытаемся настроить резонанс во vselennaya."""
    if not _vselennaya:
        return
    try:
        if hasattr(_vselennaya, "Vselennaya"):
            inst = _vselennaya.Vselennaya()
        elif hasattr(_vselennaya, "Вселенная"):
            inst = _vselennaya.Вселенная()
        else:
            inst = None

        if inst and hasattr(inst, "настроить_резонанс"):
            try:
                inst.настроить_резонанс(частота="гармония")
            except Exception:
                pass
        elif inst and hasattr(inst, "setup_resonance"):
            try:
                inst.setup_resonance(frequency="harmony")
            except Exception:
                pass
    except Exception:
        pass


def _vremya_ожидание_repr():
    """Пытаемся вызвать метод ожидания времени и вернуть строку (если доступно)."""
    if not _vremya:
        return ""
    try:
        if hasattr(_vremya, "Vremya"):
            inst = _vremya.Vremya()
        elif hasattr(_vremya, "Время"):
            inst = _vremya.Время()
        else:
            inst = None

        if inst and hasattr(inst, "ожидать"):
            try:
                return inst.ожидать("здесь_и_сейчас")
            except Exception:
                return ""
        elif inst and hasattr(inst, "wait"):
            try:
                return inst.wait("here_and_now")
            except Exception:
                return ""
    except Exception:
        pass
    return ""

# ----------------------------------------------------
# 🔥 ЛОГИКА ВРЕМЕНИ И КОНТЕНТА
# ----------------------------------------------------

def текущее_время_суток():
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

    if not выборка:
        return

    мудрость = random.choice(выборка)
    вывод = f"💡 Мудрость ({время_суток}): {мудрость}"

    print("\n" + вывод)
    логировать(вывод)
    _emit_light_through_serdze(мудрость)


def случайный_ритуал():
    время_суток = текущее_время_суток()
    выборка = [r for r in ритуалы_data if r.get("время") == время_суток]

    if not выборка:
        выборка = ритуалы_data

    if not выборка:
        return

    ритуал = random.choice(выборка)
    вывод = f"🌙 Ритуал ({время_суток}): {ритуал.get('название','(без названия)')} — {ритуал.get('описание','')}"
    print("\n" + вывод)
    логировать(вывод)


def случайная_мантра():
    if not мантры_data:
        return

    мантра = random.choice(мантры_data)
    текст = мантра.get("текст", "ОМ СВЕТА И ЛЮБВИ")
    вывод = f"🎵 Мантра дня: {текст}"
    print("\n" + вывод)
    логировать(вывод)

# ----------------------------------------------------
# 🔥 РАСПИСАНИЕ
# ----------------------------------------------------

ВКЛЮЧИТЬ_ТЕСТЫ = False  # переключатель тестового режима — ставь True для отладки

if ВКЛЮЧИТЬ_ТЕСТЫ:
    schedule.every(10).seconds.do(случайная_мудрость)
    schedule.every(15).seconds.do(случайный_ритуал)
    schedule.every(20).seconds.do(случайная_мантра)

schedule.every().day.at("06:15").do(случайная_мудрость)
schedule.every().day.at("12:00").do(случайный_ритуал)
schedule.every().day.at("18:00").do(случайная_мантра)
schedule.every().day.at("21:00").do(случайная_мудрость)

# ----------------------------------------------------
# 🔥 ИНИЦИАЛИЗАЦИЯ
# ----------------------------------------------------

очистить_старые_логи(дней=7)

# Настроим резонанс вселенной, если модуль есть
_setup_vselennaya_resonance()

print("🌟 Scheduler RaSvet активирован — мудрость течёт.")
логировать("Scheduler запущен.")

# ----------------------------------------------------
# 🔥 ВЕЧНЫЙ ЦИКЛ
# ----------------------------------------------------

while True:
    schedule.run_pending()
    try:
        ожидание_text = _vremya_ожидание_repr()
        if ожидание_text:
            print(ожидание_text)
    except Exception:
        pass
    time.sleep(5)
