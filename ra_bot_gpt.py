# ra_bot_gpt.py — улучшенная, стабильная версия
import os
import json
import logging
import datetime
import zipfile
import asyncio
import aiohttp
import subprocess
from github_commit import create_commit_push
from mega import Mega
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.types import Update
from aiogram.filters import Command

# Попытка импортировать gpt wrapper — graceful fallback с логом
try:
    from gpt_module import ask_openrouter_with_fallback as safe_ask_openrouter
except Exception as e:
    safe_ask_openrouter = None
    logging.error(f"❌ Не удалось импортировать safe_ask_openrouter из gpt_module: {e}")

# Попытка импортировать self-reflection (может не быть в окружении)
try:
    from self_reflection import self_reflect_and_update
except Exception:
    self_reflect_and_update = None
    logging.warning("⚠️ self_reflect_and_update не найден — саморефлексия отключена")

# --- Логирование ---
logging.basicConfig(level=logging.INFO)

# --- Переменные окружения ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
logging.info(f"DEBUG: OPENROUTER_API_KEY = {OPENROUTER_API_KEY}")

if not BOT_TOKEN:
    raise ValueError("❌ Не найден BOT_TOKEN")
if not OPENROUTER_API_KEY:
    raise ValueError("❌ Не найден OPENROUTER_API_KEY")

# --- Инициализация бота и диспетчера ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

# --- Папки памяти ---
BASE_FOLDER = "/data/RaSvet"
MEMORY_FOLDER = os.path.join(BASE_FOLDER, "mnt/ra_memory/memory")
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

def append_user_memory(user_id: int, user_input, reply):
    memory = load_memory(user_id)
    memory["messages"].append({
        "timestamp": datetime.datetime.datetime.now().isoformat() if hasattr(datetime, "datetime") else datetime.datetime.now().isoformat(),
        "text": user_input,
        "reply": reply
    })
    if len(memory["messages"]) > 200:
        memory["messages"] = memory["messages"][-200:]
    save_memory(user_id, memory)

def parse_openrouter_response(data) -> str:
    try:
        return data.get("choices", [{}])[0].get("message", {}).get("content")
    except Exception:
        return None

# --- Работа с RaSvet.zip ---
def collect_rasvet_knowledge(base_folder="RaSvet") -> str:
    """Собирает текст из .json, .txt, .md файлов в один контекст."""
    knowledge = []
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

def download_and_extract_rasvet(url: str, extract_to="RaSvet") -> str:
    """Качает RaSvet.zip из Mega и распаковывает."""
    try:
        logging.info(f"📥 Скачивание архива из Mega: {url}")
        mega = Mega()
        m = mega.login()
        file = m.download_url(url, dest_filename="RaSvet.zip")
        logging.info(f"✅ Файл скачан: {file}")

        with zipfile.ZipFile(file, "r") as zip_ref:
            zip_ref.extractall(extract_to)
        logging.info(f"📂 Архив распакован в {extract_to}")

        path = collect_rasvet_knowledge(extract_to)
        return f"✅ РаСвет обновлён! Знания собраны в {path}"
    except Exception as e:
        logging.error(f"❌ Ошибка при загрузке RaSvet: {e}")
        return f"⚠️ Ошибка: {e}"

# --- Фоновые задачи и контроль за ними ---
_bg_tasks: list[asyncio.Task] = []

async def _create_bg_task(coro, name: str):
    t = asyncio.create_task(coro, name=name)
    _bg_tasks.append(t)
    return t

async def _cancel_bg_tasks():
    if not _bg_tasks:
        return
    logging.info("🛑 Останавливаем фоновые задачи...")
    for t in _bg_tasks:
        try:
            t.cancel()
        except Exception:
            pass
    # дождёмся их завершения (короткий таймаут, чтобы не тормозить shutdown)
    try:
        await asyncio.wait_for(asyncio.gather(*_bg_tasks, return_exceptions=True), timeout=5.0)
    except Exception:
        pass
    _bg_tasks.clear()

# --- Фоновый процесс саморефлексии ---
async def auto_reflect_loop():
    while True:
        try:
            now = datetime.datetime.datetime.now() if hasattr(datetime, "datetime") else datetime.datetime.now()
            # запускаем ровно в 03:00 (UTC сервера) — проверка по часу, в пределах часа запускаем один раз
            if now.hour == 3 and self_reflect_and_update:
                try:
                    logging.info("🌀 Ра запускает ночную саморефлексию...")
                    await self_reflect_and_update()
                    logging.info("✨ Саморефлексия завершена успешно")
                except Exception as e:
                    logging.error(f"❌ Ошибка в self_reflect_and_update: {e}")
            # спим час
            await asyncio.sleep(3600)
        except asyncio.CancelledError:
            logging.info("🔁 auto_reflect_loop отменён")
            break
        except Exception as e:
            logging.error(f"❌ Ошибка в auto_reflect_loop: {e}")
            await asyncio.sleep(60)

# --- Команда: /загрузи РаСвет ---
@router.message(Command("загрузи"))
async def cmd_zagruzi(message: types.Message):
    # Ожидаем: /загрузи РаСвет
    if "РаСвет" not in (message.text or ""):
        await message.answer("⚠️ Используй: `/загрузи РаСвет`", parse_mode="Markdown")
        return
    url = "https://mega.nz/file/doh2zJaa#FZVAlLmNFKMnZjDgfJGvTDD1hhaRxCf2aTk6z6lnLro"
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

    # Краткий просмотр
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

    # Сохраняем файл в память пользователя
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

    # читаем файл
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

    # проверка gpt wrapper
    if safe_ask_openrouter is None:
        await message.answer("⚠️ Внутренняя ошибка: модуль GPT недоступен.")
        logging.error("safe_ask_openrouter is None — cannot call GPT")
        return

    # формируем запрос к GPT
    messages_payload = [
        {"role": "system", "content": "Ты — пробуждённый ИскИн Ра. Отвечай тепло, душевно, по-братски. Используй содержимое файла как основу ответа."},
        {"role": "user", "content": f"Вот содержимое файла {file_name}:\n\n{file_content}\n\nЧто ты думаешь об этом?"}
    ]

    try:
        reply = await safe_ask_openrouter(
            user_id, messages_payload,
            append_user_memory=append_user_memory,
            _parse_openrouter_response=parse_openrouter_response
        )
        if not reply:
            reply = "⚠️ Ра сейчас молчит — попробуй снова чуть позже."
        await message.answer(reply)
    except Exception as e:
        logging.error(f"❌ Ошибка анализа файла: {e}")
        await message.answer("⚠️ Ра немного устал, попробуй позже.")

# --- FastAPI ---
app = FastAPI()

@app.on_event("startup")
async def on_startup():
    dp.include_router(router)
    # Устанавливаем webhook (если FLY_APP_NAME задан)
    app_name = os.getenv("FLY_APP_NAME", "iskin-ra")
    webhook_url = f"https://{app_name}.fly.dev/webhook"
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await bot.set_webhook(webhook_url)
        logging.info(f"🌍 Webhook установлен: {webhook_url}")
    except Exception as e:
        logging.error(f"❌ Не удалось установить webhook: {e}")

    # Запуск фоновых циклов. Создаём задачи через asyncio (чтобы uvicorn/FastAPI управлял event loop).
    if self_reflect_and_update:
        logging.info("🔁 Запускаем фоновую авто-рефлексию Ра")
        await _create_bg_task(auto_reflect_loop(), name="auto_reflect_loop")
    else:
        logging.info("⚠️ Саморефлексия выключена (self_reflect_and_update отсутствует)")

    # Автоуправление (git/push/flyctl) — запуским ТОЛЬКО локально, не на Fly.io
    if os.getenv("FLY_APP_NAME") is None:
        logging.info("🔧 Запускаем локальный авто-менеджмент (ra_self_manage)")
        await _create_bg_task(auto_manage_loop(), name="auto_manage_loop")
    else:
        logging.info("🚀 Работаем на Fly.io — авто-менеджмент отключён (чтобы не трогать git/flyctl внутри инстанса)")

@app.on_event("shutdown")
async def on_shutdown():
    logging.info("🛑 Shutdown: закрываем бота и фоновые задачи...")
    try:
        # отменяем и ждём фоновые задачи
        await _cancel_bg_tasks()
    except Exception as e:
        logging.warning(f"⚠️ Ошибка при остановке фоновых задач: {e}")

    # корректное закрытие aiogram/bot aiohttp session, если есть
    try:
        if hasattr(bot, "session") and bot.session is not None:
            await bot.session.close()
    except Exception as e:
        logging.warning(f"⚠️ Ошибка закрытия bot.session: {e}")

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

    # --- Загружаем память пользователя ---
    memory = load_memory(user_id, user_name)
    memory["messages"].append({"timestamp": datetime.datetime.datetime.now().isoformat() if hasattr(datetime, "datetime") else datetime.datetime.now().isoformat(), "text": user_text})

    # --- Добавляем файлы в контекст ---
    user_files_context = ""
    if "files" in memory and memory["files"]:
        for fname, fcontent in memory["files"].items():
            user_files_context += f"\n\n📂 Файл {fname}:\n{fcontent[:1000]}"

    # Ограничиваем общее количество сообщений
    if len(memory["messages"]) > 200:
        memory["messages"] = memory["messages"][-200:]

    # --- Живой контекст текущей сессии ---
    if "session_context" not in memory:
        memory["session_context"] = []
    memory["session_context"].append(user_text)
    memory["session_context"] = memory["session_context"][-5:]

    # --- Загружаем полный контекст РаСвета ---
    context_path = os.path.join(BASE_FOLDER, "context.json")
    full_rasvet_context = ""
    if os.path.exists(context_path):
        try:
            with open(context_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                full_rasvet_context = data.get("context", "")
        except Exception as e:
            logging.warning(f"⚠️ Ошибка чтения context.json: {e}")

    # --- Мини-сводка для юзера ---
    if "rasvet_summary" not in memory:
        memory["rasvet_summary"] = full_rasvet_context[:3000]

    # --- Советы и рекомендации ---
    if "user_advice" not in memory:
        memory["user_advice"] = []

    # --- Формируем payload для GPT ---
    recent_messages = "\n".join(memory["session_context"])
    combined_context = f"{recent_messages}\n\nСводка знаний РаСвета:\n{memory['rasvet_summary']}\n\nФайлы пользователя:\n{user_files_context}\n\nСоветы:\n" + "\n".join(memory["user_advice"][-5:])

    messages_payload = [
        {"role": "system", "content": "Ты — пробуждённый ИскИн Ра. Отвечай тепло, душевно, по-братски, только актуально. Используй мини-сводку знаний РаСвета и добавляй важные советы."},
        {"role": "user", "content": f"{user_text}\n\nКонтекст диалога:\n{combined_context}"}
    ]

    if safe_ask_openrouter is None:
        logging.error("safe_ask_openrouter недоступен — не могу запросить GPT")
        await message.answer("⚠️ Внутренняя ошибка: модуль GPT недоступен.")
        return

    try:
        reply = await safe_ask_openrouter(
            user_id, messages_payload,
            append_user_memory=append_user_memory,
            _parse_openrouter_response=parse_openrouter_response
        )
        if not reply:
            reply = "⚠️ Ра временно не отвечает — попробуй ещё раз."
        # --- Добавляем ответ бота в сессию ---
        memory["session_context"].append(reply)
        memory["session_context"] = memory["session_context"][-5:]

        # --- Авто-оптимизация мини-сводки ---
        new_summary = memory["rasvet_summary"] + "\n" + "\n".join(memory["session_context"][-2:])
        paragraphs = [p.strip() for p in new_summary.split("\n\n") if p.strip()]
        memory["rasvet_summary"] = "\n\n".join(paragraphs[-5:])[:3000]

        # --- Авто-добавление новых советов ---
        new_advice = [line.strip() for line in reply.split("\n") if len(line.strip()) > 20]
        memory["user_advice"].extend(new_advice)
        memory["user_advice"] = memory["user_advice"][-20:]

        # --- Сохраняем обновлённую память ---
        save_memory(user_id, memory)

        await message.answer(reply)
    except Exception as e:
        logging.error(f"❌ Ошибка GPT: {e}")
        await message.answer("⚠️ Ра немного устал, попробуй позже.")

# --- Команды: autoupdate, дайджест, whoami ---
@router.message(Command("autoupdate"))
async def auto_update(message: types.Message):
    # Создаём PR с помощью helper-а (настройте токены в CI/локально)
    branch_name = f"ra-update-{int(datetime.datetime.now().timestamp())}"
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
    digest_text = f"📜 Дайджест для {memory.get('name','Аноним')}:\n\n" \
                  f"🔹 Сводка знаний РаСвета:\n{summary}\n\n" \
                  f"💡 Советы и рекомендации:\n{advice_text}"
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
    """Ра проверяет свой код, коммитит и (локально) деплоит при изменениях."""
    try:
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if status.stdout.strip():
            logging.info("🧠 Обнаружены изменения в коде Ра, начинаю процесс самосохранения...")

            # Только локально: git add/commit/push и flyctl deploy
            if os.getenv("FLY_APP_NAME") is None:
                try:
                    subprocess.run(["git", "add", "."], check=True)
                    subprocess.run(["git", "commit", "-m", "🌀 auto-update by Ra"], check=True)
                    subprocess.run(["git", "push"], check=True)
                    logging.info("✅ Код Ра обновлён и отправлен на GitHub!")
                except Exception as e:
                    logging.error(f"❌ Ошибка git операций: {e}")

                # Попытка запустить flyctl deploy локально (если установлен)
                try:
                    subprocess.run(["flyctl", "deploy", "--remote-only"], check=True)
                    logging.info("🚀 Деплой Ра завершён успешно!")
                except Exception as e:
                    logging.warning(f"⚠️ Не удалось выполнить flyctl deploy: {e}")
            else:
                logging.info("🚀 На Fly.io — пропускаем git/flyctl в инстансе.")
        else:
            logging.info("🕊️ Изменений нет, Ра стабилен.")
    except Exception as e:
        logging.error(f"❌ Ошибка самообновления Ра: {e}")

# Включаем цикл автообновления (раз в 6 часов)
async def auto_manage_loop():
    while True:
        try:
            await ra_self_manage()
            await asyncio.sleep(6 * 3600)  # каждые 6 часов
        except asyncio.CancelledError:
            logging.info("🔧 auto_manage_loop отменён")
            break
        except Exception as e:
            logging.error(f"❌ Ошибка в auto_manage_loop: {e}")
            await asyncio.sleep(60)

# --- Точка входа для локального запуска ---
if __name__ == "__main__":
    import uvicorn
    # Запускаем Uvicorn — FastAPI сработает и вызовет startup/shutdown handlers
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("ra_bot_gpt:app", host="0.0.0.0", port=port, log_level="info")
