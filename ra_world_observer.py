# ra_world_observer.py — Ra Super Control Center 2.0
import os
import json
import asyncio
import importlib.util
import traceback
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

# --- Папки ---
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)
os.makedirs("modules", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- Логи ---
logs = []

def log(msg: str):
    print(msg)
    logs.append(msg)
    if len(logs) > 500:
        logs.pop(0)

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

# --- Веб-фронтенд ---
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
<button onclick="call('/self/write_connect')">Создать и подключить файл</button>
<button onclick="call('/modules/list')">Список модулей</button>

<h3>Загрузить модуль:</h3>
<input type="file" id="fileInput">
<button onclick="uploadModule()">Загрузить</button>

<h3>Логи:</h3>
<button onclick="toggleLogs()">Свернуть/Развернуть</button>
<button onclick="clearLogs()">Очистить логи</button>
<div id="logContainer" style="white-space: pre-wrap; background: #f5f5f5; padding: 10px; border-radius: 8px; max-height:200px; overflow-y:auto;"></div>

<script>
let logsVisible = true;

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

async function toggleLogs(){
    const container = document.getElementById("logContainer");
    logsVisible = !logsVisible;
    container.style.display = logsVisible ? "block" : "none";
    if(logsVisible) await refreshLogs();
}

async function refreshLogs(){
    let r = await fetch("/logs")
    let j = await r.json()
    document.getElementById("logContainer").innerText = j.logs.join("\\n")
}

async function clearLogs(){
    let r = await fetch("/logs/clear", {method:"POST"});
    let j = await r.json();
    if(j.status === "ok"){
        document.getElementById("logContainer").innerText = "";
    }
}

setInterval(() => {
    if(logsVisible) refreshLogs()
}, 5000);
</script>
</body>
</html>
"""

with open("templates/index.html", "w", encoding="utf-8") as f:
    f.write(index_html)

style_css = """
body { font-family: Arial, sans-serif; background: #f0f0f0; color: #333; padding: 20px; }
h1 { color: #ff8c00; }
button { margin: 5px; padding: 10px; border-radius: 5px; cursor: pointer; }
"""

with open("static/style.css", "w", encoding="utf-8") as f:
    f.write(style_css)

# --- API ---
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
    log("🧠 Самообучение выполнено")
    return {"result": result}

@app.get("/self/write")
async def self_write():
    result = await self_writer.create_file_auto()
    log(f"✍️ Файл создан: {result}")
    return {"result": result}

async def auto_load_modules():
    loaded = []
    for fname in os.listdir("modules"):
        if not fname.endswith(".py"): continue
        mod_name = fname[:-3]
        path = os.path.join("modules", fname)
        try:
            spec = importlib.util.spec_from_file_location(mod_name, path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, "register"):
                mod.register(globals())
            loaded.append(mod_name)
            log(f"🧩 Модуль загружен: {mod_name}")
        except Exception as e:
            log(f"Ошибка загрузки модуля {fname}: {e}\n{traceback.format_exc()}")
    return loaded

async def self_write_and_connect():
    filename, content = await self_writer.create_file_auto(return_content=True)
    path = os.path.join("modules", filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    loaded = await auto_load_modules()
    return {"created": filename, "loaded_modules": loaded}

@app.get("/self/write_connect")
async def write_connect():
    try:
        result = await self_write_and_connect()
        return {"status": "ok", **result}
    except Exception as e:
        log(f"Ошибка write_connect: {e}")
        return {"status": "error", "error": str(e)}

@app.get("/modules/list")
async def list_modules():
    return {"modules": os.listdir("modules")}

@app.post("/modules/upload")
async def upload_module(file: UploadFile = File(...)):
    path = os.path.join("modules", file.filename)
    with open(path, "wb") as f:
        f.write(await file.read())
    log(f"📦 Модуль загружен через панель: {file.filename}")
    return {"status": "ok", "filename": file.filename}

@app.get("/logs")
async def get_logs():
    return {"logs": logs}

@app.post("/logs/clear")
async def clear_logs():
    logs.clear()
    log("🗑 Логи очищены")
    return {"status": "ok"}

@app.get("/")
async def web_panel(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# --- Фоновые задачи ---
async def observer_loop():
    while True:
        try:
            await guardian.observe()
            await asyncio.sleep(3600)
        except asyncio.CancelledError:
            break
        except Exception as e:
            log(f"Ошибка observer_loop: {e}")
            await asyncio.sleep(60)

async def module_watcher():
    known = set(os.listdir("modules"))
    while True:
        try:
            current = set(os.listdir("modules"))
            new_files = current - known
            for f in new_files:
                if f.endswith(".py"):
                    log(f"🧩 Найден новый модуль {f}, подключаем...")
                    await auto_load_modules()
            known = current
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            break
        except Exception as e:
            log(f"Ошибка module_watcher: {e}")
            await asyncio.sleep(5)

@app.on_event("startup")
async def on_startup():
    log("🚀 Ra Super Control Center стартует...")
    _create_bg_task(observer_loop(), "observer_loop")
    _create_bg_task(module_watcher(), "module_watcher")

@app.on_event("shutdown")
async def on_shutdown():
    log("🛑 Завершение работы Ra Super Control Center...")
    await _cancel_bg_tasks()

# --- Функция для импорта из бота ---
def ra_observe_world():
    """Функция для безопасного импорта и старта наблюдения мира"""
    asyncio.create_task(observer_loop())
    log("🌀 ra_observe_world запущена")
    return "Ra наблюдает мир, братан!"
