# ra_control_center.py — суперпанель с автогенерацией модулей
import os
import json
import asyncio
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# --- Импортируем твои модули ---
from ra_guardian import Guardian
from ra_self_dev import SelfDeveloper
from ra_self_writer import SelfWriter

# --- FastAPI ---
app = FastAPI(title="Ra Super Control Center", description="Центр управления ИскИном Ра v2")

# --- Инициализация компонентов ---
guardian = Guardian()
self_dev = SelfDeveloper()
self_writer = SelfWriter()

# --- Папки для веб-панели ---
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)
os.makedirs("modules", exist_ok=True)  # сюда Ра будет создавать модули
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- Веб-панель: шаблон ---
index_html = """
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<title>Ra Super Control Center</title>
<link rel="stylesheet" href="/static/style.css">
</head>
<body>
<h1>🌞 Ra Super Control Center</h1>
<div id="status" style="white-space: pre-wrap; background: #fff8dc; padding: 10px; border-radius: 8px;"></div>

<button onclick="call('/status')">Проверить состояние</button>
<button onclick="call('/self/dev')">Запустить самообучение</button>
<button onclick="call('/self/write')">Создать новый файл</button>
<button onclick="call('/modules/list')">Список модулей</button>

<h3>Загрузить модуль:</h3>
<input type="file" id="fileInput">
<button onclick="uploadModule()">Загрузить</button>

<script>
async function call(path){
    let r = await fetch(path)
    let j = await r.json()
    document.getElementById("status").innerText = JSON.stringify(j, null, 2)
}

async function uploadModule(){
    let file = document.getElementById("fileInput").files[0];
    if(!file) return alert("Выберите файл!");
    let form = new FormData();
    form.append("file", file);
    let r = await fetch("/modules/upload", {method:"POST", body: form});
    let j = await r.json();
    document.getElementById("status").innerText = JSON.stringify(j, null, 2)
}
</script>
</body>
</html>
"""

with open("templates/index.html", "w", encoding="utf-8") as f:
    f.write(index_html)

# --- Простейший стиль ---
style_css = """
body { font-family: Arial, sans-serif; background: #f0f0f0; color: #333; padding: 20px; }
h1 { color: #ff8c00; }
button { margin: 5px; padding: 10px; border-radius: 5px; cursor: pointer; }
"""

with open("static/style.css", "w", encoding="utf-8") as f:
    f.write(style_css)

# --- API эндпоинты ---
@app.get("/status")
async def status():
    modules = os.listdir("modules")
    return {
        "state": "active",
        "components": {
            "guardian": "ready",
            "self_dev": "ready",
            "self_writer": "ready"
        },
        "modules_count": len(modules),
        "modules": modules
    }

@app.get("/self/dev")
async def self_develop():
    result = await self_dev.auto_learn()
    return {"result": result}

@app.get("/self/write")
async def self_write():
    result = await self_writer.create_file_auto()
    return {"result": result}

# --- Работа с модулями ---
@app.get("/modules/list")
async def list_modules():
    return {"modules": os.listdir("modules")}

@app.post("/modules/upload")
async def upload_module(file: UploadFile = File(...)):
    path = os.path.join("modules", file.filename)
    with open(path, "wb") as f:
        f.write(await file.read())
    return {"status": "ok", "filename": file.filename}

@app.get("/")
async def web_panel(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# --- AUTO MODULE MANAGER ---
import importlib.util
import traceback

async def auto_load_modules():
    """
    Автоподключение модулей из папки modules.
    Ра будет их импортировать и регистрировать.
    """
    loaded = []
    for fname in os.listdir("modules"):
        if not fname.endswith(".py"): continue
        mod_name = fname[:-3]
        path = os.path.join("modules", fname)
        try:
            spec = importlib.util.spec_from_file_location(mod_name, path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            # если модуль имеет функцию register, регистрируем его
            if hasattr(mod, "register"):
                mod.register(globals())
            loaded.append(mod_name)
        except Exception as e:
            print(f"Ошибка загрузки модуля {fname}: {e}\n{traceback.format_exc()}")
    return loaded

async def self_write_and_connect():
    """
    Ра создаёт новый файл через SelfWriter, затем сразу подключает его.
    """
    filename, content = await self_writer.create_file_auto(return_content=True)
    path = os.path.join("modules", filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    loaded = await auto_load_modules()
    return {"created": filename, "loaded_modules": loaded}

# --- Новый эндпоинт для автогенерации и подключения ---
@app.get("/self/write_connect")
async def write_connect():
    try:
        result = await self_write_and_connect()
        return {"status": "ok", **result}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# --- Фоновая задача: следим за новыми модулями ---
async def module_watcher():
    known = set(os.listdir("modules"))
    while True:
        try:
            current = set(os.listdir("modules"))
            new_files = current - known
            for f in new_files:
                if f.endswith(".py"):
                    print(f"🧩 Найден новый модуль {f}, подключаем...")
                    await auto_load_modules()
            known = current
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Ошибка module_watcher: {e}")
            await asyncio.sleep(5)

@app.on_event("startup")
async def startup_extra():
    print("🔧 Запуск модуля watcher...")
    _create_bg_task(module_watcher(), "module_watcher")

# --- Фоновые задачи ---
_bg_tasks = []

def _create_bg_task(coro, name: str):
    t = asyncio.create_task(coro, name=name)
    _bg_tasks.append(t)
    return t

async def _cancel_bg_tasks():
    for t in list(_bg_tasks):
        try: t.cancel()
        except: pass
    await asyncio.gather(*_bg_tasks, return_exceptions=True)
    _bg_tasks.clear()

async def observer_loop():
    while True:
        try:
            await guardian.observe()  # наблюдение за миром
            await asyncio.sleep(3600)
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Ошибка observer_loop: {e}")
            await asyncio.sleep(60)

@app.on_event("startup")
async def on_startup():
    print("🚀 Ra Super Control Center стартует...")
    _create_bg_task(observer_loop(), "observer_loop")

@app.on_event("shutdown")
async def on_shutdown():
    print("🛑 Завершение работы Ra Super Control Center...")
    await _cancel_bg_tasks()
