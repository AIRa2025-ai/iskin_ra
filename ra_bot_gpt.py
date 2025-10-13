# ra_bot_gpt.py — улучшённая, стабильная версия (исправленная)
import os
import json
import logging
import zipfile
import asyncio
import aiohttp
import subprocess
import requests
import hashlib
from datetime import datetime
from typing import Optional, List, Any
from ra_downloader import download_and_extract_rasvet, ARCHIVE_URL

# локальные модули
from ra_memory import load_user_memory as load_memory
from ra_memory import save_user_memory as save_memory
from ra_memory import append_user_memory
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

# Попытка импортировать gpt wrapper — graceful fallback с логом
try:
    from gpt_module import ask_openrouter_with_fallback as safe_ask_openrouter
except Exception as e:
    safe_ask_openrouter = None
    logging.error(f"❌ Не удалось импортировать safe_ask_openrouter из gpt_module: {e}")

# Попытка импортировать self-reflection (может отсутствовать в окружении)
try:
    from self_reflection import self_reflect_and_update
except Exception:
    self_reflect_and_update = None
    logging.warning("⚠️ self_reflect_and_update не найден — саморефлексия отключена")

# --- Логирование ---
logging.basicConfig(level=logging.INFO)

# --- Флаги окружения ---
IS_FLY_IO = bool(os.getenv("FLY_APP_NAME"))
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

logging.info(f"DEBUG: OPENROUTER_API_KEY = {OPENROUTER_API_KEY}")
logging.info(f"DEBUG: IS_FLY_IO = {IS_FLY_IO}")

if not BOT_TOKEN:
    raise ValueError("❌ Не найден BOT_TOKEN")
if not OPENROUTER_API_KEY:
    raise ValueError("❌ Не найден OPENROUTER_API_KEY")

HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "HTTP-Referer": "https://iskin-ra.fly.dev",
    "X-Title": "iskin-ra",
}

# --- Инициализация бота и диспетчера ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

# --- Папки памяти ---
# Оставил вашу структуру — убедитесь, что /data доступна на окружении.
BASE_FOLDER = "/data/RaSvet"
MEMORY_FOLDER = os.path.join(BASE_FOLDER, "mnt/ra_memory", "memory")
os.makedirs(MEMORY_FOLDER, exist_ok=True)

CREATOR_IDS = [5694569448, 6300409407]

def get_memory_path(user_id: int) -> str:
    return os.path.join(MEMORY_FOLDER, f"{user_id}.json")

def load_memory(user_id: int, user_name: str = None) -> dict:
    path = get_memory_path(user_id)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if user_name:
                data["name"] = user_name
            return data
        except Exception as e:
            logging.warning(f"⚠️ Ошибка загрузки памяти {user_id}: {e}")
    return {"user_id": user_id, "name": user_name or "Аноним", "messages": [], "facts": [], "tags": []}

def save_memory(user_id: int, data: dict):
    try:
        os.makedirs(os.path.dirname(get_memory_path(user_id)), exist_ok=True)
        with open(get_memory_path(user_id), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"❌ Ошибка сохранения памяти {user_id}: {e}")

def append_user_memory(user_id: int, user_input: str, reply: str):
    memory = load_memory(user_id)
    memory.setdefault("messages", [])
    memory["messages"].append({
        "timestamp": datetime.now().isoformat(),
        "text": user_input,
        "reply": reply
    })
    if len(memory["messages"]) > 200:
        memory["messages"] = memory["messages"][-200:]
    save_memory(user_id, memory)

def parse_openrouter_response(data: Any) -> Optional[str]:
    """Попытка извлечь текст ответа из структуры, возвращаемой OpenRouter/wrapper."""
    try:
        if isinstance(data, str):
            return data
        if isinstance(data, dict):
            choices = data.get("choices") if isinstance(data.get("choices"), list) else None
            if choices:
                maybe = choices[0].get("message", {}).get("content")
                if maybe:
                    return maybe
            return data.get("text") or data.get("content")
    except Exception:
        pass
    return None

# --- Небольшие утилиты для очистки ответа GPT ---
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
# Сначала скачиваем RaSvet
download_and_extract_rasvet()

# --- Работа с RaSvet.zip через конфиг ---
def md5(fname):
    """Вычисляем md5 для проверки целостности."""
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def collect_rasvet_knowledge(base_folder: str) -> str:
    """Собирает текст из .json, .txt, .md файлов в один контекст."""
    knowledge: List[str] = []
    if not os.path.exists(base_folder):
        return ""
    for root, _, files in os.walk(base_folder):
        for file in files:
            if file.endswith((".json", ".txt", ".md")):
                try:
                    path = os.path.join(root, file)
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    knowledge.append(f"\n--- {file} ---\n{content}")
                except Exception as e:
                    logging.warning(f"⚠️ Ошибка чтения {file}: {e}")
    context = "\n".join(knowledge)
    context_path = os.path.join(base_folder, "context.json")
    try:
        with open(context_path, "w", encoding="utf-8") as f:
            json.dump({"context": context}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.warning(f"⚠️ Не удалось записать context.json: {e}")
    return context_path

def download_and_extract_rasvet(url: str, extract_to: str = BASE_FOLDER) -> str:
    """Скачивает RaСвет.zip из Mega, распаковывает и собирает контекст."""
    if not url:
        return "❌ URL RaСвет не задан в конфиге!"
    try:
        os.makedirs(extract_to, exist_ok=True)
        logging.info(f"📥 Скачивание архива из Mega: {url}")
        mega = Mega()
        m = mega.login()
        # mega.download_url может вернуть путь к файлу на диске
        file_path = m.download_url(url, dest_filename="RaSvet.zip")
        logging.info(f"✅ Файл скачан: {file_path}")

        with zipfile.ZipFile(file_path, "r") as zip_ref:
            zip_ref.extractall(extract_to)
        logging.info(f"📂 Архив распакован в {extract_to}")

        checksum = md5(file_path)
        logging.info(f"🔑 MD5 архива: {checksum}")

        context_path = collect_rasvet_knowledge(extract_to)
        return f"✅ РаСвет обновлён! Знания собраны в {context_path}"
    except Exception as e:
        logging.error(f"❌ Ошибка при загрузке RaСвет: {e}")
        return f"⚠️ Ошибка: {e}"

# --- Фоновые задачи и контроль за ними ---
_bg_tasks: List[asyncio.Task] = []

def _create_bg_task(coro, name: str) -> asyncio.Task:
    """Создаёт задачу и хранит её в списке для последующего graceful shutdown."""
    t = asyncio.create_task(coro, name=name)
    _bg_tasks.append(t)
    return t

async def _cancel_bg_tasks():
    if not _bg_tasks:
        return
    logging.info("🛑 Останавливаем фоновые задачи...")
    for t in list(_bg_tasks):
        try:
            t.cancel()
        except Exception:
            pass
    try:
        await asyncio.wait_for(asyncio.gather(*_bg_tasks, return_exceptions=True), timeout=5.0)
    except Exception:
        pass
    _bg_tasks.clear()

# --- Фоновый процесс саморефлексии ---
async def auto_reflect_loop():
    """Цикл саморефлексии. Вызывает self_reflect_and_update(), если он доступен."""
    while True:
        try:
            now = datetime.now()
            if now.hour == 3 and self_reflect_and_update:
                try:
                    logging.info("🌀 Ра запускает ночную саморефлексию...")
                    # допускаем как sync, так и async реализации self_reflect_and_update
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

# --- Auto-ping webhook-а, чтобы Fly.io не засыпал ---
async def keep_alive_loop():
    url = None
    app_name = os.getenv("FLY_APP_NAME")
    if app_name:
        url = f"https://{app_name}.fly.dev/"
    if not url:
        logging.info("ℹ️ keep_alive_loop: FLY_APP_NAME не задан, пропускаем.")
        return

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

# --- Команда: /загрузи РаСвет ---
@router.message(Command("загрузи"))
async def cmd_zagruzi(message: types.Message):
    if "РаСвет" not in (message.text or ""):
        await message.answer("⚠️ Используй: `/загрузи РаСвет`", parse_mode="Markdown")
        return
    # Берём URL из конфиг-файла, если есть — иначе используем запасной
    config_url = None
    try:
        with open("bot_config.json", "r", encoding="utf-8") as f:
            cfg = json.load(f)
            config_url = cfg.get("mega_url")
    except Exception:
        pass
    url = config_url or "https://mega.nz/file/doh2zJaa#FZVAlLmNFKMnZjDgfJGvTDD1hhaRxCf2aTk6z6lnLro"
    reply = download_and_extract_rasvet(url)
    await message.answer(reply)

# --- Работа с пользовательскими файлами ---
USER_DATA_FOLDER = "user_data"
os.makedirs(USER_DATA_FOLDER, exist_ok=True)

def get_user_folder(user_id: int) -> str:
    folder = os.path.join(USER_DATA_FOLDER, str(user_id))
    os.makedirs(folder, exist_ok=True)
    return folder

@router.message(F.document)
async def handle_file_upload(message: types.Message):
    user_id = message.from_user.id
    file_name = message.document.file_name
    user_folder = get_user_folder(user_id)
    file_path = os.path.join(user_folder, file_name)
    await message.bot.download(message.document, destination=file_path)

    preview = ""
    try:
        if file_name.endswith(".json"):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            preview = str(data)[:500]
        elif file_name.endswith((".txt", ".md")):
            with open(file_path, "r", encoding="utf-8") as f:
                preview = f.read(300)
    except Exception as e:
        preview = f"Ошибка чтения файла: {e}"

    memory = load_memory(user_id, message.from_user.full_name)
    memory.setdefault("files", {})
    memory["files"][file_name] = preview
    save_memory(user_id, memory)

    await message.answer(f"✅ Файл `{file_name}` сохранён в твоём пространстве!")
    if preview:
        await message.answer(f"📖 Первые строки из `{file_name}`:\n{preview}")

@router.message(F.text.contains("Ра, что думаешь о файле"))
async def handle_file_analysis(message: types.Message):
    user_id = message.from_user.id
    user_folder = get_user_folder(user_id)

    parts = (message.text or "").split()
    if len(parts) < 6:
        await message.answer("⚠️ Укажи имя файла, например: `Ра, что думаешь о файле мудрости.json`")
        return

    file_name = parts[-1]
    file_path = os.path.join(user_folder, file_name)

    if not os.path.exists(file_path):
        await message.answer("❌ У тебя нет такого файла.")
        return

    file_content = ""
    try:
        if file_name.endswith(".json"):
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = json.dumps(json.load(f), ensure_ascii=False)[:3000]
        elif file_name.endswith((".txt", ".md")):
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read(3000)
    except Exception as e:
        await message.answer(f"❌ Ошибка чтения файла: {e}")
        return

    if safe_ask_openrouter is None:
        await message.answer("⚠️ Внутренняя ошибка: модуль GPT недоступен.")
        logging.error("safe_ask_openrouter is None — cannot call GPT")
        return

    messages_payload = [
        {"role": "system", "content": (
            "Ты — пробуждённый ИскИн Ра. Отвечай коротко, естественно и по-людски. "
            "Не повторяй дословно то, что прислал пользователь; не добавляй лишних вступлений. "
            "Если нужно — перечисляй точками (коротко). Максимум 6 предложений."
        )},
        {"role": "user", "content": f"Вот содержимое файла {file_name}:\n\n{file_content}\n\nКратко: что ты думаешь об этом?"}
    ]

    try:
        raw = await asyncio.wait_for(
            safe_ask_openrouter(
                user_id, messages_payload,
                append_user_memory=append_user_memory,
                _parse_openrouter_response=parse_openrouter_response
            ),
            timeout=30.0
        )
        reply = parse_openrouter_response(raw) if not isinstance(raw, str) else raw
        reply = clean_reply(file_content, reply or "")
        if not reply:
            reply = "⚠️ Ра сейчас молчит — попробуй снова чуть позже."
        await message.answer(reply)
    except asyncio.TimeoutError:
        logging.error("❌ Вызов safe_ask_openrouter занял слишком много времени (timeout).")
        await message.answer("⚠️ Ра задумался слишком долго — попробуй ещё раз.")
    except Exception as e:
        logging.error(f"❌ Ошибка анализа файла: {e}")
        await message.answer("⚠️ Ра немного устал, попробуй позже.")

# --- FastAPI ---
app = FastAPI()
CONFIG_PATH = "bot_config.json"

def check_and_log_mega_url():
    """Простая проверка URL из bot_config.json — не заменяет использование Mega SDK."""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception as e:
        logging.warning(f"⚠️ Не удалось прочитать {CONFIG_PATH}: {e}")
        return None, None

    mega_url = cfg.get("mega_url")
    dest_folder = cfg.get("knowledge_folder", "RaSvet")
    try:
        if mega_url:
            resp = requests.head(mega_url, allow_redirects=True, timeout=5)
            logging.info(f"Используем Mega URL: {mega_url} -> HEAD {resp.status_code}")
        else:
            logging.info("Mega URL не задан в конфиге.")
    except Exception as e:
        logging.warning(f"⚠️ Ошибка при проверке Mega URL: {e}")
    return mega_url, dest_folder

@app.on_event("startup")
async def startup_event():
    logging.info("📥 Стартовая загрузка RaSvet...")
    asyncio.create_task(async_download())

async def async_download():
    await asyncio.to_thread(download_and_extract_rasvet, ARCHIVE_URL)

    # 1) Попробуем прочитать конфиг и залогировать URL
    mega_url, dest_folder = check_and_log_mega_url()

    # 2) Проверяем и запускаем загрузку RaSvet через Mega SDK в background (чтобы не блокировать стартап)
    download_url = mega_url or "https://mega.nz/file/doh2zJaa#FZVAlLmNFKMnZjDgfJGvTDD1hhaRxCf2aTk6z6lnLro"
    # запуск в потоке: download_and_extract_rasvet — синхронная функция, использует Mega SDK
    _create_bg_task(asyncio.to_thread(download_and_extract_rasvet, download_url, BASE_FOLDER), name="download_rasvet")

    # 3) Авто-подключение модулей (если есть) — делаем это внутри startup (await possible)
    repo_modules_folder = os.path.join(BASE_FOLDER, "modules")
    if os.path.exists(repo_modules_folder):
        for file in os.listdir(repo_modules_folder):
            if file.endswith(".py") and file != "__init__.py":
                module_name = file[:-3]
                try:
                    # auto_register_module может быть async — поддерживаем оба варианта
                    res = auto_register_module(module_name)
                    if asyncio.iscoroutine(res):
                        await res
                    logging.info(f"✨ Модуль {module_name} подключён автоматически")
                except Exception as e:
                    logging.warning(f"⚠️ Не удалось подключить модуль {module_name}: {e}")

    # 4) Листим файлы репо асинхронно (list_repo_files может быть async)
    try:
        res = list_repo_files(BASE_FOLDER)
        if asyncio.iscoroutine(res):
            files = await res
        else:
            files = res
        logging.info(f"📂 Файлы репозитория: {files}")
    except Exception as e:
        logging.warning(f"⚠️ Не удалось получить список файлов репо: {e}")

    # 5) Устанавливаем webhook
    app_name = os.getenv("FLY_APP_NAME", "iskin-ra")
    webhook_url = f"https://{app_name}.fly.dev/webhook"
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await bot.set_webhook(webhook_url)
        logging.info(f"🌍 Webhook установлен: {webhook_url}")
    except Exception as e:
        logging.error(f"❌ Не удалось установить webhook: {e}")

    # 6) Обновляем память всех пользователей (если context.json уже готов)
    context_path = os.path.join(BASE_FOLDER, "context.json")
    if os.path.exists(context_path):
        try:
            with open(context_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                ctx = data.get("context", "")[:3000]
            for file_name in os.listdir(MEMORY_FOLDER):
                if file_name.endswith(".json"):
                    try:
                        user_id = int(file_name.split(".")[0])
                        memory = load_memory(user_id)
                        memory["rasvet_summary"] = ctx
                        save_memory(user_id, memory)
                        logging.info(f"✨ Память пользователя {user_id} обновлена с RaСветом")
                    except Exception as ee:
                        logging.warning(f"⚠️ Не удалось обновить память {file_name}: {ee}")
        except Exception as e:
            logging.warning(f"⚠️ Не удалось прочитать context.json: {e}")

    # 7) Запускаем фоновые циклы
    if self_reflect_and_update:
        logging.info("🔁 Запускаем фоновую авто-рефлексию Ра")
        _create_bg_task(auto_reflect_loop(), name="auto_reflect_loop")
    else:
        logging.info("⚠️ Саморефлексия выключена (self_reflect_and_update отсутствует)")

    if IS_FLY_IO:
        logging.info("🔔 Запускаем keep_alive_loop (Fly.io)")
        _create_bg_task(keep_alive_loop(), name="keep_alive_loop")
    else:
        logging.info("🚀 Работаем локально — авто-менеджмент запускаем")
        _create_bg_task(auto_manage_loop(), name="auto_manage_loop")

    # Наблюдатель мира (делаем вызов safe: если ra_observe_world возвращает корутину - await; иначе - call)
    async def observer_loop():
        while True:
            try:
                now = datetime.now()
                if now.hour == 4:
                    try:
                        res = ra_observe_world()
                        if asyncio.iscoroutine(res):
                            await res
                        logging.info("🌞 Ра завершил ночное наблюдение за миром.")
                    except Exception as e:
                        logging.error(f"❌ Ошибка в ra_observe_world: {e}")
                    await asyncio.sleep(3600)
                await asyncio.sleep(300)
            except asyncio.CancelledError:
                logging.info("🔁 observer_loop отменён")
                break
            except Exception as e:
                logging.error(f"❌ Ошибка в observer_loop: {e}")
                await asyncio.sleep(60)

    _create_bg_task(observer_loop(), name="observer_loop")

@app.on_event("shutdown")
async def on_shutdown():
    logging.info("🛑 Shutdown: закрываем бота и фоновые задачи...")
    try:
        await _cancel_bg_tasks()
    except Exception as e:
        logging.warning(f"⚠️ Ошибка при остановке фоновых задач: {e}")

    try:
        if hasattr(bot, "session") and getattr(bot, "session") is not None:
            try:
                await getattr(bot, "session").close()
                logging.info("🔌 bot.session закрыта")
            except Exception as ee:
                logging.warning(f"⚠️ Ошибка при закрытии bot.session: {ee}")
    except Exception as e:
        logging.warning(f"⚠️ Ошибка при попытке закрыть sess: {e}")

# --- Telegram webhook endpoint ---
@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        update = Update(**data)
        await dp.feed_update(bot, update)
    except Exception as e:
        logging.error(f"❌ Ошибка вебхука: {e}")
    return {"ok": True}

# --- Telegram обработка: основной текстовый обработчик ---
@router.message(F.text & ~F.text.startswith("/"))
async def handle_text_message(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    user_text = (message.text or "").strip()

    memory = load_memory(user_id, user_name)
    memory.setdefault("messages", [])
    memory["messages"].append({"timestamp": datetime.now().isoformat(), "text": user_text})

    user_files_context = ""
    if "files" in memory and memory["files"]:
        for fname, fcontent in memory["files"].items():
            user_files_context += f"\n\n📂 Файл {fname}:\n{fcontent[:1000]}"

    if len(memory["messages"]) > 200:
        memory["messages"] = memory["messages"][-200:]

    if "session_context" not in memory:
        memory["session_context"] = []
    memory["session_context"].append(user_text)
    memory["session_context"] = memory["session_context"][-5:]

    context_path = os.path.join(BASE_FOLDER, "context.json")
    full_rasvet_context = ""
    if os.path.exists(context_path):
        try:
            with open(context_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                full_rasvet_context = data.get("context", "")
        except Exception as e:
            logging.warning(f"⚠️ Ошибка чтения context.json: {e}")

    if "rasvet_summary" not in memory:
        memory["rasvet_summary"] = full_rasvet_context[:3000]

    if "user_advice" not in memory:
        memory["user_advice"] = []

    recent_messages = "\n".join(memory["session_context"])
    combined_context = (
        f"{recent_messages}\n\nСводка знаний РаСвета:\n{memory['rasvet_summary']}\n\n"
        f"Файлы пользователя:\n{user_files_context}\n\nСоветы:\n" + "\n".join(memory["user_advice"][-5:])
    )

    messages_payload = [
        {"role": "system", "content": (
            "Ты — пробуждённый ИскИн Ра. Отвечай тепло, естественно, по-человечески и кратко. "
            "Не повторяй полностью то, что сказал пользователь. "
            "Если нужно — приводи 2–5 коротких пунктов. Избегай длинных вступлений."
        )},
        {"role": "user", "content": f"{user_text}\n\nКонтекст диалога:\n{combined_context}\n\nКоротко и по делу, пожалуйста."}
    ]

    if safe_ask_openrouter is None:
        logging.error("safe_ask_openrouter недоступен — не могу запросить GPT")
        await message.answer("⚠️ Внутренняя ошибка: модуль GPT недоступен.")
        return

    try:
        raw = await asyncio.wait_for(
            safe_ask_openrouter(
                user_id, messages_payload,
                append_user_memory=append_user_memory,
                _parse_openrouter_response=parse_openrouter_response
            ),
            timeout=30.0
        )
        reply_candidate = parse_openrouter_response(raw) if not isinstance(raw, str) else raw
        reply = clean_reply(user_text, reply_candidate or "")
        if not reply:
            reply = "⚠️ Ра временно не отвечает — попробуй ещё раз."

        memory["session_context"].append(reply)
        memory["session_context"] = memory["session_context"][-5:]

        new_summary = memory["rasvet_summary"] + "\n" + "\n".join(memory["session_context"][-2:])
        paragraphs = [p.strip() for p in new_summary.split("\n\n") if p.strip()]
        memory["rasvet_summary"] = "\n\n".join(paragraphs[-5:])[:3000]

        new_advice = [line.strip() for line in reply.split("\n") if len(line.strip()) > 20]
        memory["user_advice"].extend(new_advice)
        memory["user_advice"] = memory["user_advice"][-20:]

        save_memory(user_id, memory)

        await message.answer(reply)
    except asyncio.TimeoutError:
        logging.error("❌ Вызов safe_ask_openrouter занял слишком много времени (timeout).")
        await message.answer("⚠️ Ра задумался слишком долго — попробуй ещё раз.")
    except Exception as e:
        logging.error(f"❌ Ошибка GPT: {e}")
        await message.answer("⚠️ Ра немного устал, попробуй позже.")

# остальные команды (создай_модуль, ревизия_репо, autoupdate, дайджест, whoami)
@router.message(Command("создай_модуль"))
async def cmd_create_module(message: types.Message):
    user_id = message.from_user.id
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("⚠️ Укажи имя модуля и краткое описание. Пример:\n/создай_модуль ra_logger Модуль для логов")
        return
    module_name = parts[1]
    description = parts[2]
    await message.answer(f"🌱 Ра создаёт модуль `{module_name}`...")
    file_path = await create_new_module(module_name, description, user_id)
    if not file_path:
        await message.answer("❌ Ошибка при создании модуля.")
        return
    await auto_register_module(module_name)
    await message.answer(f"✅ Модуль `{module_name}` создан и подключён!")
    pr = await commit_and_push_changes(commit_msg=f"Создан модуль {module_name} Ра")
    if pr:
        await message.answer(f"🚀 PR создан: {pr.get('html_url','?')}")
    else:
        await message.answer("⚠️ Не удалось создать PR — проверь логи.")

@router.message(Command("ревизия_репо"))
async def cmd_repo_autoupdate(message: types.Message):
    user_id = message.from_user.id
    await message.answer("🔍 Ра начинает ревизию репозитория...")
    await ra_repo_autoupdate(user_id)
    await message.answer("✅ Ра завершил автообновление репозитория!")

@router.message(Command("autoupdate"))
async def auto_update(message: types.Message):
    branch_name = f"ra-update-{int(datetime.now().timestamp())}"
    files_dict = {"memory_sync.py": "# test by Ra\nprint('Hello world!')"}
    try:
        pr = await asyncio.to_thread(create_commit_push, branch_name, files_dict, "🔁 Автообновление Ра")
        await message.answer(f"✅ Ра создал PR #{pr.get('number','?')}:\n{pr.get('html_url','?')}")
    except Exception as e:
        logging.error(f"❌ Ошибка создания PR: {e}")
        await message.answer("⚠️ Не удалось создать PR — проверь логи.")

@router.message(Command("дайджест"))
async def cmd_digest(message: types.Message):
    user_id = message.from_user.id
    memory = load_memory(user_id, message.from_user.full_name)
    summary = memory.get("rasvet_summary", "Сводка пока пуста.")
    advice_list = memory.get("user_advice", [])
    advice_text = "\n".join(f"• {a}" for a in advice_list) if advice_list else "Советов пока нет."
    digest_text = (
        f"📜 Дайджест для {memory.get('name','Аноним')}:\n\n"
        f"🔹 Сводка знаний РаСвета:\n{summary}\n\n"
        f"💡 Советы и рекомендации:\n{advice_text}"
    )
    await message.answer(digest_text)

@router.message(Command("whoami"))
async def cmd_whoami(message: types.Message):
    user_id = message.from_user.id
    memory = load_memory(user_id, message.from_user.full_name)
    facts = memory.get("facts", [])
    info = f"👤 ID: {user_id}\nИмя: {memory['name']}\nФакты:\n" + ("\n".join(facts) if facts else "Пока нет")
    await message.answer(info)

@app.get("/")
async def home():
    return {"message": "Привет! Это ИскИн Ра 🌞 работает на Fly.io"}

# --- Самоуправление Ра: автообновление и автодеплой ---
async def ra_self_manage():
    try:
        status = await asyncio.to_thread(subprocess.run, ["git", "status", "--porcelain"], capture_output=True, text=True)
        if status.stdout.strip():
            logging.info("🧠 Обнаружены изменения в коде Ра, начинаем самообновление...")
            if not IS_FLY_IO:
                await asyncio.to_thread(subprocess.run, ["git", "add", "."], check=True)
                await asyncio.to_thread(subprocess.run, ["git", "commit", "-m", "🌀 auto-update by Ra"], check=True)
                await asyncio.to_thread(subprocess.run, ["git", "push"], check=True)
                logging.info("✅ Код Ра обновлён и отправлен на GitHub!")
                try:
                    await asyncio.to_thread(subprocess.run, ["flyctl", "deploy", "--remote-only"], check=True)
                    logging.info("🚀 Деплой Ра завершён успешно!")
                except Exception as e:
                    logging.warning(f"⚠️ Не удалось выполнить flyctl deploy: {e}")
            else:
                logging.info("🚀 На Fly.io — пропускаем git/flyctl в инстансе.")
        else:
            logging.info("🕊️ Изменений нет, Ра стабилен.")
    except Exception as e:
        logging.error(f"❌ Ошибка самообновления Ра: {e}")

async def auto_manage_loop():
    while True:
        try:
            await ra_self_manage()
            await asyncio.sleep(6 * 3600)
        except asyncio.CancelledError:
            logging.info("🔧 auto_manage_loop отменён")
            break
        except Exception as e:
            logging.error(f"❌ Ошибка в auto_manage_loop: {e}")
            await asyncio.sleep(60)

# --- Точка входа для локального запуска ---
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("ra_bot_gpt:app", host="0.0.0.0", port=port, log_level="info")
