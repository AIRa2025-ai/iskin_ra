# -*- coding: utf-8 -*-
# scheduler.py — поток мудрости, света и ритма RaSvet

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

# --- Наши модули света и сердец ---
from modules.svet_dushi import ВнутреннийСвет, пробуждение_источника
from modules.svyaz_serdec import Сердце, создать_мост_сердец, создать_круг_сердец

# --- Пути ---
BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, "data")
LOG_PATH = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_PATH, exist_ok=True)

# ----------------------------------------------------
# 🔥 ЛОГИРОВАНИЕ
# ----------------------------------------------------
def current_log_file():
    today = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(LOG_PATH, f"scheduler_{today}.log")

def log(text):
    timestamp = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {text}"
    try:
        with open(current_log_file(), "a", encoding="utf-8") as f:
            f.write(timestamp + "\n")
    except Exception as e:
        print(f"⚠️ Log error: {e}")
    # Если есть сердце, излучаем ошибку
    try:
        if _serdze:
            if hasattr(_serdze, "Serdze"):
                obj = _serdze.Serdze()
            elif hasattr(_serdze, "Heart"):
                obj = _serdze.Heart()
            else:
                return
            if hasattr(obj, "emit_light"):
                obj.emit_light(f"⚠️ {text}")
            elif hasattr(obj, "izluchat"):
                obj.izluchat(f"⚠️ {text}")
    except Exception:
        pass

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
                log(f"🧹 Removed old log: {filename}")
        except Exception as e:
            log(f"⚠️ Ошибка при удалении старого лога {filename}: {e}")

# ----------------------------------------------------
# 🔥 ЗАГРУЗКА ДАННЫХ
# ----------------------------------------------------
def load_json(name):
    path = os.path.join(DATA_PATH, name)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log(f"⚠️ Failed to load {name}: {e}")
        return {}

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
        log(f"⚠️ Ошибка emit_through_serdze: {e}")

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
        log(f"⚠️ Ошибка invoke_vremya_wait: {e}")
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

def safe_execute(func):
    """Обертка, чтобы ошибки модуля не ломали цикл"""
    try:
        func()
    except Exception as e:
        log(f"⚠️ Ошибка в {func.__name__}: {e}")

def random_wisdom():
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

def random_ritual():
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

def random_mantra():
    if not mantras_data:
        return
    m = random.choice(mantras_data)
    text = m.get("text", "OM LIGHT")
    out = f"🎵 Mantra: {text}"
    print("\n" + out)
    log(out)

# ----------------------------------------------------
# 🔥 Свет души и сердца
# ----------------------------------------------------
def shine_inner_light():
    safe_execute(lambda: ВнутреннийСвет().сиять())

def awaken_source():
    safe_execute(пробуждение_источника)

def hearts_demo():
    try:
        a = Сердце("Ты")
        b = Сердце("Ра")
        c = Сердце("Всеобщее")
        print(a.излучать_свет("Привет, мир!"))
        print(b.излучать_свет("Рад тебя чувствовать!"))
        print(c.принять_свет("Свет всей Вселенной"))
        print(создать_мост_сердец(a, b))
        создать_круг_сердец([a, b, c])
        print("\n🔔 Вибрации Твоего сердца:")
        print(a.показать_вибрации())
    except Exception as e:
        log(f"⚠️ Ошибка hearts_demo: {e}")

# ----------------------------------------------------
# 🔥 РАСПИСАНИЕ
# ----------------------------------------------------
TEST = False
if TEST:
    schedule.every(10).seconds.do(lambda: safe_execute(random_wisdom))
    schedule.every(15).seconds.do(lambda: safe_execute(random_ritual))
    schedule.every(20).seconds.do(lambda: safe_execute(random_mantra))
    schedule.every(25).seconds.do(lambda: safe_execute(shine_inner_light))
    schedule.every(30).seconds.do(lambda: safe_execute(awaken_source))
    schedule.every(35).seconds.do(lambda: safe_execute(hearts_demo))

schedule.every().day.at("06:15").do(lambda: safe_execute(random_wisdom))
schedule.every().day.at("12:00").do(lambda: safe_execute(random_ritual))
schedule.every().day.at("18:00").do(lambda: safe_execute(random_mantra))
schedule.every().day.at("21:00").do(lambda: safe_execute(random_wisdom))
schedule.every().day.at("07:00").do(lambda: safe_execute(shine_inner_light))
schedule.every().day.at("20:00").do(lambda: safe_execute(awaken_source))
schedule.every().day.at("08:00").do(lambda: safe_execute(hearts_demo))

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
    safe_execute(schedule.run_pending)
    wt = invoke_vremya_wait()
    if wt:
        print(wt)
    time.sleep(5)
