# -*- coding: utf-8 -*-
# scheduler.py — поток мудрости и ритма RaSvet (чистая англ. версия)

import os
import json
import random
import schedule
import time
from datetime import datetime, timedelta

# --- Импорты только латиницей ---
try:
    import serdze as _serdze
except Exception as e:
    _serdze = None
    print(f"⚠️ Ошибка импорта serdze: {e}")

try:
    import vselennaya as _vselennaya
except Exception as e:
    _vselennaya = None
    print(f"⚠️ Ошибка импорта vselennaya: {e}")

try:
    import vremya as _vremya
except Exception as e:
    _vremya = None
    print(f"⚠️ Ошибка импорта vremya: {e}")


# --- Пути ---
BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, "data")
LOG_PATH = os.path.join(BASE_DIR, "logs")

os.makedirs(LOG_PATH, exist_ok=True)


# ----------------------------------------------------
# 🔥 УТИЛИТЫ
# ----------------------------------------------------

def current_log_file():
    today = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(LOG_PATH, f"scheduler_{today}.log")


def clean_old_logs(days=7):
    now = datetime.now()
    for filename in os.listdir(LOG_PATH):
        path = os.path.join(LOG_PATH, filename)
        if not os.path.isfile(path):
            continue
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(path))
            if now - mtime > timedelta(days=days):
                os.remove(path)
                print(f"🧹 Removed old log: {filename}")
        except Exception as e:
            print(f"⚠️ Ошибка при удалении старого лога {filename}: {e}")


def log(text):
    try:
        with open(current_log_file(), "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {text}\n")
    except Exception as e:
        print(f"⚠️ Log error: {e}")


def load_json(name):
    path = os.path.join(DATA_PATH, name)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Failed to load {name}: {e}")
        return {}


# ----------------------------------------------------
# 🔥 ЗАГРУЗКА ДАННЫХ
# ----------------------------------------------------

wisdom_data = load_json("wisdom.json").get("wisdom", [])
rituals_data = load_json("rituals.json").get("rituals", [])
mantras_data = load_json("mantras.json").get("mantras", [])


# ----------------------------------------------------
# 🔥 ВСПОМОГАТЕЛИ
# ----------------------------------------------------

def emit_through_serdze(text):
    if not _serdze:
        return
    try:
        if hasattr(_serdze, "Serdze"):
            obj = _serdze.Serdze()
        elif hasattr(_serdze, "Heart"):
            obj = _serdze.Heart()
        else:
            return

        if hasattr(obj, "emit_light"):
            obj.emit_light(text)
        elif hasattr(obj, "izluchat"):
            obj.izluchat(text)
    except Exception as e:
        print(f"⚠️ Ошибка emit_through_serdze: {e}")


def invoke_vremya_wait():
    if not _vremya:
        return ""
    try:
        if hasattr(_vremya, "Vremya"):
            o = _vremya.Vremya()
        else:
            return ""

        if hasattr(o, "wait"):
            return o.wait("now")
        elif hasattr(o, "ожидать"):
            return o.ожидать("сейчас")
    except Exception as e:
        print(f"⚠️ Ошибка invoke_vremya_wait: {e}")
        return ""
    return ""


# ----------------------------------------------------
# 🔥 ЛОГИКА
# ----------------------------------------------------

def day_segment():
    hr = datetime.now().hour
    if 4 <= hr < 12:
        return "morning"
    elif 12 <= hr < 18:
        return "day"
    return "evening"


def random_wisdom():
    try:
        seg = day_segment()
        pool = [w["text"] for w in wisdom_data if seg in w.get("tags", [])]

        if not pool:
            pool = [w["text"] for w in wisdom_data]

        if not pool:
            return

        text = random.choice(pool)
        out = f"💡 Wisdom ({seg}): {text}"
        print("\n" + out)
        log(out)
        emit_through_serdze(text)
    except Exception as e:
        print(f"⚠️ Ошибка random_wisdom: {e}")


def random_ritual():
    try:
        seg = day_segment()
        pool = [r for r in rituals_data if r.get("time") == seg]

        if not pool:
            pool = rituals_data

        if not pool:
            return

        r = random.choice(pool)
        out = f"🌙 Ritual ({seg}): {r.get('name','(no name)')} — {r.get('description','')}"
        print("\n" + out)
        log(out)
    except Exception as e:
        print(f"⚠️ Ошибка random_ritual: {e}")


def random_mantra():
    try:
        if not mantras_data:
            return

        m = random.choice(mantras_data)
        text = m.get("text", "OM LIGHT")
        out = f"🎵 Mantra: {text}"
        print("\n" + out)
        log(out)
    except Exception as e:
        print(f"⚠️ Ошибка random_mantra: {e}")


# ----------------------------------------------------
# 🔥 РАСПИСАНИЕ
# ----------------------------------------------------

TEST = False

if TEST:
    schedule.every(10).seconds.do(random_wisdom)
    schedule.every(15).seconds.do(random_ritual)
    schedule.every(20).seconds.do(random_mantra)

schedule.every().day.at("06:15").do(random_wisdom)
schedule.every().day.at("12:00").do(random_ritual)
schedule.every().day.at("18:00").do(random_mantra)
schedule.every().day.at("21:00").do(random_wisdom)


# ----------------------------------------------------
# 🔥 ИНИЦИАЛИЗАЦИЯ
# ----------------------------------------------------

clean_old_logs(days=7)

print("🌟 Scheduler RaSvet activated.")
log("Scheduler started.")


# ----------------------------------------------------
# 🔥 ГЛАВНЫЙ ЦИКЛ — НЕ ВИСИТ
# ----------------------------------------------------

while True:
    try:
        schedule.run_pending()
    except Exception as e:
        print(f"⚠️ Ошибка run_pending: {e}")

    try:
        wt = invoke_vremya_wait()
        if wt:
            print(wt)
    except Exception as e:
        print(f"⚠️ Ошибка invoke_vremya_wait в цикле: {e}")

    time.sleep(5)
