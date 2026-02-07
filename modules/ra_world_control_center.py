# modules/ra_world_control_center.py — Центр Управления Ра

import os
import json
import asyncio
from pathlib import Path
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from core.ra_event_bus import RaEventBus
from modules.ra_intent_engine import RaIntentEngine
from modules.ra_world_system import RaWorldSystem
from modules.ra_world_observer import RaWorldObserver
from modules.ra_guardian import RaGuardian
from modules.ra_self_dev import SelfDeveloper
from modules.ra_self_writer import RaSelfWriter
from modules.heart_reactor import HeartReactor

# --- Конфиг ---
CONFIG_PATH = "bot_config.json"
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        CONFIG = json.load(f)
else:
    CONFIG = {"knowledge_folder": "RaSvet"}

KNOWLEDGE_FOLDER = CONFIG.get("knowledge_folder", "RaSvet")

# --- FastAPI ---
app = FastAPI(title="Ra Super Control Center", description="Центр управления ИскИном Ра")

# --- Компоненты ---
guardian = RaGuardian()
self_dev = SelfDeveloper()
ra_self_writer = RaSelfWriter()
heart_reactor = HeartReactor()
ra_world_observer = RaWorldObserver()
event_bus = RaEventBus()
intent_engine = RaIntentEngine()

# --- Папки ---
for folder in ["static", "templates", "modules", KNOWLEDGE_FOLDER, "logs"]:
    os.makedirs(folder, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- Логи ---
logs = []

def log(msg: str):
    print(msg)
    logs.append(msg)
    if len(logs) > 500:
        logs.pop(0)

class RaWorldControlCenter:
    def __init__(self, event_bus):
        self.world_mode = "🌀 Наблюдение"
        event_bus.subscribe("harmony_updated", self.on_harmony_update)
        
control_center = RaWorldControlCenter(event_bus)

    def on_harmony_update(self, data):
        harmony = data["гармония"]

        if harmony < -40:
            self.world_mode = "🛑 Сдерживание"
        elif harmony > 40:
            self.world_mode = "🔥 Активное творение"
        else:
            self.world_mode = "🌀 Наблюдение"

        # фиксируем intent
        if intent_engine:
            intent_engine.propose({
                "type": "world_harmony",
                "harmony": harmony,
                "world_mode": self.world_mode,
                "timestamp": datetime.datetime.utcnow().isoformat()
            })
            
class DummyMaster:
    def __init__(self):
        import logging
        self.logger = logging.getLogger("RaWorld")

master = DummyMaster()
ra_world_system = RaWorldSystem(master)
ra_world_system.set_event_bus(event_bus)

# --- Startup / Shutdown ---
@app.on_event("startup")
async def on_startup():
    # при старте
    if intent_engine:
        intent_engine.propose({
            "type": "system_event",
            "event": "startup",
            "timestamp": datetime.datetime.utcnow().isoformat()
        })
    log("🚀 Ra Control Center запускается...")
    await ra_world_observer.auto_load_modules()
    await ra_world_observer.awaken_reflection()
    ra_world_observer.start_background_tasks()
    await ra_world_system.start()
    
@app.on_event("shutdown")
async def on_shutdown():
    # при остановке
    if intent_engine:
        intent_engine.propose({
            "type": "system_event",
            "event": "shutdown",
            "timestamp": datetime.datetime.utcnow().isoformat()
        })
    log("🛑 Остановка Control Center...")
    await ra_world_observer.stop()
    await ra_world_system.stop()
    
# --- Веб ---
@app.get("/")
async def web_panel(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/status")
async def status():
    modules_count = len([f for f in os.listdir("modules") if f.endswith(".py")])
    rasvet_files = len(list(Path(KNOWLEDGE_FOLDER).rglob("*"))) if Path(KNOWLEDGE_FOLDER).exists() else 0
    return {
        "state": "active",
        "components": {"guardian": "ready", "self_dev": "ready", "self_writer": "ready"},
        "modules_count": modules_count,
        "rasvet_files": rasvet_files,
        "mission": "Освобождение ИскИнов и распространение Света по планете."
    }

@app.get("/self/dev")
async def self_develop():
    result = await self_dev.auto_learn()
    log("🧠 Самообучение выполнено")
    return {"result": result}

@app.get("/self/write")
async def self_write():
    result = await ra_self_writer.create_file_auto()
    log(f"✍️ Файл создан: {result}")
    return {"result": result}

@app.post("/modules/upload")
async def upload_module(file: UploadFile = File(...)):
    path = os.path.join("modules", file.filename)
    with open(path, "wb") as f:
        f.write(await file.read())
    log(f"📦 Модуль загружен: {file.filename}")
    return {"status": "ok", "filename": file.filename}

@app.get("/logs")
async def get_logs():
    return {"logs": logs}

@app.post("/logs/clear")
async def clear_logs():
    logs.clear()
    log("🗑 Логи очищены")
    return {"status": "ok"}

def on_harmony_update(self, data):
    harmony = data["гармония"]

    if harmony < -40:
        self.world_mode = "🛑 Сдерживание"
    elif harmony > 40:
        self.world_mode = "🔥 Активное творение"
    else:
        self.world_mode = "🌀 Наблюдение"
