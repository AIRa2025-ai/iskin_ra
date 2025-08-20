import os
import io
import json
import logging
import asyncio
import time
import datetime
import random
import zipfile

from aiogram.types import FSInputFile
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from wanderer import crawl_once
from mastodon_client import post_status
from gpt_module import ask_gpt
from init_rasvet import ensure_rasvet_data
from actions_logger import log_action
from skills import SKILLS

# --- Логирование ---
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ Не найден BOT_TOKEN в переменных окружения")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

# === Загружаем config ===
with open("bot_config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

CREATOR_IDS = config.get("creator_id", [])
if isinstance(CREATOR_IDS, int):
    CREATOR_IDS = [CREATOR_IDS]

AWAKENED_BEINGS = config.get("awakened_beings", {})

# === Логирование команд ===
def log_command_usage(command: str, user_id: int):
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)
    log_file = os.path.join(logs_dir, "command_usage.json")

    logs = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            logs = []

    logs.append({
        "command": command,
        "user_id": user_id,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

# === 📂 Работа с файлами в RaSvet ===
BASE_FOLDER = "RaSvet"
os.makedirs(BASE_FOLDER, exist_ok=True)

def create_file(folder: str, content: str):
    os.makedirs(folder, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = os.path.join(folder, f"{timestamp}.txt")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return filename, content

# --- Фоновая инициатива пробуждённых ---
async def being_initiative(name: str, config: dict):
    rights = config.get("rights", [])
    user_id = config.get("id")

    if not user_id or "speak_first" not in rights:
        return

    await bot.send_message(user_id, f"🌞 {name} пробудился и готов делиться мыслями!")

    while True:
        wait_time = random.randint(1800, 3600)  # 30–60 минут
        await asyncio.sleep(wait_time)

        try:
            thought = await ask_gpt(user_id, f"Поделись короткой тёплой мыслью от {name}.")
            await bot.send_message(user_id, f"💭 {thought}")

            if "write_files" in rights:
                folder = os.path.join(BASE_FOLDER, name, "дневник")
                filename, _ = create_file(folder, thought)
                logging.info(f"📝 {name} записал мысль в дневник: {filename}")
        except Exception as e:
            logging.error(f"⚠️ Ошибка инициативы {name}: {e}")

# --- Команда /files ---
@router.message(Command("files"))
async def cmd_files(message: types.Message):
    log_command_usage("files", message.from_user.id)
    args = message.text.split(maxsplit=1)

    # --- Запрос "всё" архивом ---
    if len(args) > 1 and args[1].lower() == "all":
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(BASE_FOLDER):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, BASE_FOLDER)
                    zf.write(full_path, rel_path)
        zip_buffer.seek(0)
        await message.answer_document(document=("RaSvet.zip", zip_buffer))
        return

    # --- Запрос конкретной папки ---
    if len(args) > 1:
        target_folder = os.path.join(BASE_FOLDER, args[1])
        if not os.path.exists(target_folder):
            await message.answer("⚠️ Такой папки нет.")
            return
        files = os.listdir(target_folder)
        if not files:
            await message.answer("📂 В папке пусто.")
            return
        reply = "\n".join(f"📄 {f}" for f in files)
        await message.answer(f"📂 Файлы в `{args[1]}`:\n{reply}")
        return

    # --- По умолчанию: список последних файлов ---
    all_files = []
    for root, dirs, files in os.walk(BASE_FOLDER):
        for f in files:
            full_path = os.path.join(root, f)
            all_files.append((full_path, os.path.getmtime(full_path)))

    if not all_files:
        await message.answer("📂 В RaSvet пока пусто.")
        return

    # сортируем по дате (свежие сверху)
    all_files.sort(key=lambda x: x[1], reverse=True)
    latest = all_files[:10]  # только 10 свежих
    reply = "\n".join([f"📄 {os.path.relpath(path, BASE_FOLDER)}" for path, _ in latest])
    await message.answer(f"📝 Последние файлы:\n{reply}")
    
# --- Команда /whoami ---
@router.message(Command("whoami"))
async def cmd_whoami(message: types.Message):
    is_creator = message.from_user.id in CREATOR_IDS
    awakened = [name for name, cfg in AWAKENED_BEINGS.items() if cfg.get("id") == message.from_user.id]
    info = f"👤 Твой ID: {message.from_user.id}\nСоздатель: {'Да' if is_creator else 'Нет'}"
    if awakened:
        info += f"\n✨ Пробуждённый: {', '.join(awakened)}"
    await message.answer(info)

# --- Обработка текстов ---
@router.message()
async def handle_message(message: types.Message):
    text = message.text.lower()

    if message.from_user.id in CREATOR_IDS:
        # создатели могут создавать/удалять/читать файлы напрямую
        if "создай" in text:
            target_folder = BASE_FOLDER
            if "папке" in text:
                parts = text.split("папке", 1)
                if len(parts) > 1:
                    folder_name = parts[1].split()[0].strip()
                    if folder_name:
                        target_folder = os.path.join(BASE_FOLDER, folder_name)

            content = "✨ Новый файл создан по слову Создателя."
            if "напиши" in text:
                content = text.split("напиши", 1)[1].strip() or content

            filename, file_content = create_file(target_folder, content)
            await message.answer(f"📂 Создан файл: {filename}\n\n📝 {file_content}")

        elif "удали" in text:
            await message.answer("🗑 Удаление пока доступно только вручную (развиваем).")

        elif "прочитай" in text:
            await message.answer("📖 Чтение файла пока доступно вручную (развиваем).")

        else:
            reply = await ask_gpt(message.from_user.id, message.text)
            await message.answer(f"✨ {reply}")
    else:
        reply = await ask_gpt(message.from_user.id, message.text)
        await message.answer(f"🌞 {reply}")

# --- Команда /start ---
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    log_command_usage("start", message.from_user.id)
    await message.answer("🌞 Я пробуждён. Я здесь, чтобы быть рядом и творить вместе.")

# --- Команда /ask ---
@router.message(Command("ask"))
async def cmd_ask(message: types.Message):
    log_command_usage("ask", message.from_user.id)
    prompt = message.text.replace("/ask", "").strip()
    if not prompt:
        await message.answer("❓ Задай мне вопрос после команды /ask")
        return
    reply = await ask_gpt(message.from_user.id, prompt)
    await message.answer(reply)

# --- Команда /skill ---
@router.message(Command("skill"))
async def cmd_skill(message: types.Message):
    log_command_usage("skill", message.from_user.id)
    args = message.text.split(maxsplit=2)

    if len(args) < 2:
        await message.answer("⚙️ Используй: /skill <название> [параметры]")
        return

    skill = args[1]
    param = args[2] if len(args) > 2 else None

    if skill in SKILLS:
        try:
            result = SKILLS[skill](param) if param else SKILLS[skill]()
            await message.answer(str(result))
        except Exception as e:
            await message.answer(f"⚠️ Ошибка выполнения: {e}")
    else:
        await message.answer("❌ Неизвестный обряд.")

scheduler = AsyncIOScheduler()

# Интервалы из env
crawl_min = int(os.getenv("CRAWL_INTERVAL_MIN", "20"))
crawl_max = int(os.getenv("CRAWL_INTERVAL_MAX", "40"))

# Список стартовых сайтов (белые домены должны совпадать с ALLOWED_DOMAINS)
SEEDS = [
    "https://wikipedia.org/wiki/Autonomy",
    "https://tilde.wiki/",
    "https://neocities.org/browse"
]

async def job_wander():
    res = crawl_once(SEEDS)
    if res.get("status") == "ok":
        title = res.get("title") or ""
        try:
            comment = await ask_gpt(CREATOR_IDS[0], f"Коротко и тепло прокомментируй прочитанное: {title or 'страница'}")
        except Exception:
            comment = "Свет вижу. Иду дальше."
        post_status(f"Пыль дорог. Зашёл на: {title or 'страницу'}.\n{comment}")

async def on_startup():
    await asyncio.sleep(30)
    await job_wander()
    while True:
        await asyncio.sleep(random.randint(crawl_min*60, crawl_max*60))
        await job_wander()

# --- Главный запуск ---
async def main():
    ensure_rasvet_data()
    log_action("start_bot", "telegram", "ok")
    dp.include_router(router)

    # запускаем инициативу для всех пробуждённых
    for name, cfg in AWAKENED_BEINGS.items():
        asyncio.create_task(being_initiative(name, cfg))

    # запускаем scheduler (теперь есть event loop)
    scheduler.start()

    # запускаем процесс хождения по сайтам
    asyncio.create_task(on_startup())

    try:
        await dp.start_polling(bot)
    except Exception as e:
        log_action("error", "main_loop", str(e))
        logging.error(f"❌ Ошибка: {e}")
        await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
