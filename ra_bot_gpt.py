# ra_bot_gpt.py — стабильная, завершённая версия
import os
import json
import logging
import zipfile
import asyncio
import aiohttp
import subprocess
import requests
import hashlib
import uvicorn
from datetime import datetime
from typing import Optional, List, Any
from ra_downloader import download_and_extract_rasvet, ARCHIVE_URL
from ra_downloader import RaSvetDownloader
from ra_memory import load_user_memory as load_memory, save_user_memory as save_memory, append_user_memory
from ra_world_observer import ra_observe_world
from github_commit import create_commit_push
from mega import Mega
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.types import Update
from aiogram.filters import Command
from ra_repo_manager import (
    list_repo_files,
    create_new_module,
    auto_register_module,
    commit_and_push_changes,
    ra_repo_autoupdate
)

# GPT wrapper
try:
    from gpt_module import ask_openrouter_with_fallback as safe_ask_openrouter
except Exception as e:
    safe_ask_openrouter = None
    logging.error(f"❌ Не удалось импортировать safe_ask_openrouter: {e}")

# Self-reflection
try:
    from self_reflection import self_reflect_and_update
except Exception:
    self_reflect_and_update = None
    logging.warning("⚠️ self_reflect_and_update не найден — саморефлексия отключена")

# Логирование
logging.basicConfig(level=logging.INFO)

# Окружение
IS_FLY_IO = bool(os.getenv("FLY_APP_NAME"))
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not BOT_TOKEN:
    raise ValueError("❌ Не найден BOT_TOKEN")
if not OPENROUTER_API_KEY:
    raise ValueError("❌ Не найден OPENROUTER_API_KEY")

# Бот
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

# Память
BASE_FOLDER = "/data/RaSvet"
MEMORY_FOLDER = os.path.join(BASE_FOLDER, "memory")
os.makedirs(MEMORY_FOLDER, exist_ok=True)

CREATOR_IDS = [5694569448, 6300409407]

def get_memory_path(user_id: int) -> str:
    return os.path.join(MEMORY_FOLDER, f"{user_id}.json")

def parse_openrouter_response(data: Any) -> Optional[str]:
    try:
        if isinstance(data, str):
            return data
        if isinstance(data, dict):
            choices = data.get("choices") or []
            if choices:
                return choices[0].get("message", {}).get("content") or choices[0].get("text")
            return data.get("text") or data.get("content")
    except Exception:
        return None

def dedupe_consecutive_lines(text: str) -> str:
    lines = [l.rstrip() for l in text.splitlines()]
    out = []
    prev = None
    for l in lines:
        if l and l == prev:
            continue
        out.append(l)
        prev = l
    return "\n".join(out).strip()

def remove_echo_of_user(user_text: str, reply: str) -> str:
    u = user_text.strip()
    r = reply.strip()
    if not u or not r:
        return r
    if r.startswith(u[:min(300, len(u))]):
        r = r[len(u):].lstrip(" \n:—-")
    r = r.replace(u, "")
    return r.strip()

def clean_reply(user_text: str, raw_reply: str) -> str:
    if not raw_reply:
        return ""
    reply = raw_reply if isinstance(raw_reply, str) else str(raw_reply)
    reply = dedupe_consecutive_lines(reply)
    reply = remove_echo_of_user(user_text, reply)
    if len(reply) > 4000:
        reply = reply[:4000].rsplit("\n", 1)[0] + "\n\n…(обрезано)"
    return reply.strip()

# Фоновые задачи
_bg_tasks: List[asyncio.Task] = []
def _create_bg_task(coro, name: str) -> asyncio.Task:
    t = asyncio.create_task(coro, name=name)
    _bg_tasks.append(t)
    return t
async def _cancel_bg_tasks():
    for t in list(_bg_tasks):
        t.cancel()
    await asyncio.gather(*_bg_tasks, return_exceptions=True)
    _bg_tasks.clear()

# Observer loop
async def observer_loop():
    while True:
        try:
            now = datetime.now()
            if now.hour == 4:
                res = ra_observe_world()
                if asyncio.iscoroutine(res):
                    await res
                logging.info("🌞 Ра завершил ночное наблюдение за миром.")
                await asyncio.sleep(3600)
            await asyncio.sleep(300)
        except asyncio.CancelledError:
            logging.info("🔁 observer_loop отменён")
            break
        except Exception as e:
            logging.error(f"❌ Ошибка в observer_loop: {e}")
            await asyncio.sleep(60)

# Auto-reflect loop
async def auto_reflect_loop():
    while True:
        try:
            now = datetime.now()
            if now.hour == 3 and self_reflect_and_update:
                try:
                    logging.info("🌀 Ра запускает ночную саморефлексию...")
                    res = self_reflect_and_update()
                    if asyncio.iscoroutine(res):
                        await res
                    logging.info("✨ Саморефлексия завершена успешно")
                except Exception as e:
                    logging.error(f"❌ Ошибка в self_reflect_and_update: {e}")
            await asyncio.sleep(3600)
        except asyncio.CancelledError:
            logging.info("🔁 auto_reflect_loop отменён")
            break
        except Exception as e:
            logging.error(f"❌ Ошибка в auto_reflect_loop: {e}")
            await asyncio.sleep(60)

# Keep-alive loop для Fly.io
async def keep_alive_loop():
    app_name = os.getenv("FLY_APP_NAME")
    if not app_name:
        return
    url = f"https://{app_name}.fly.dev/"
    session = aiohttp.ClientSession()
    try:
        while True:
            try:
                async with session.get(url) as resp:
                    logging.debug(f"keep_alive ping {url} -> {resp.status}")
            except Exception as e:
                logging.warning(f"⚠️ keep_alive_loop ошибка: {e}")
            await asyncio.sleep(300)
    except asyncio.CancelledError:
        logging.info("🔁 keep_alive_loop отменён")
    finally:
        await session.close()

# FastAPI
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    logging.info("🚀 Старт приложения: проверяем RaСвет...")
    downloader = RaSvetDownloader()
    await asyncio.to_thread(downloader.run)  # скачивание и сборка контекста
    _create_bg_task(observer_loop(), "observer_loop")
    if self_reflect_and_update:
        _create_bg_task(auto_reflect_loop(), "auto_reflect_loop")
    if IS_FLY_IO:
        _create_bg_task(keep_alive_loop(), "keep_alive_loop")

@app.on_event("shutdown")
async def on_shutdown():
    logging.info("🛑 Shutdown: закрываем фоновые задачи и бот...")
    try:
        await _cancel_bg_tasks()
    except Exception as e:
        logging.warning(f"⚠️ Ошибка при отмене фоновых задач: {e}")
    try:
        if hasattr(bot, "session") and getattr(bot, "session"):
            await bot.session.close()
            logging.info("🔌 bot.session закрыта")
    except Exception as e:
        logging.warning(f"⚠️ Ошибка при закрытии bot.session: {e}")

# Telegram webhook
@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        update = Update(**data)
        await dp.feed_update(bot, update)
    except Exception as e:
        logging.error(f"❌ Ошибка вебхука: {e}")
    return {"ok": True}

# Home
@app.get("/")
async def home():
    return {"message": "Привет! Это ИскИн Ра 🌞 работает на Fly.io"}

# Точка входа для локального запуска
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
