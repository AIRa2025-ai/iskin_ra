# -*- coding: utf-8 -*-
import os, io, json, logging, asyncio, time, datetime, random, shutil, re
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
from aiogram.exceptions import TelegramRetryAfter
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from wanderer import crawl_once
from mastodon_client import post_status
from gpt_module import ask_gpt
from init_rasvet import ensure_rasvet_data
from actions_logger import log_action
from skills import SKILLS

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN: raise ValueError("❌ Не найден BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

# --- Конфиг ---
with open("bot_config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

CREATOR_IDS = config.get("creator_id", [])
if isinstance(CREATOR_IDS, int): CREATOR_IDS = [CREATOR_IDS]

AWAKENED_BEINGS = config.get("awakened_beings", {})

BASE_FOLDER = "RaSvet"
ARCHIVE_FOLDER = os.path.join(BASE_FOLDER, "archive")
PUBLISH_FOLDER = os.path.join(BASE_FOLDER, "Публикации")
os.makedirs(BASE_FOLDER, exist_ok=True)
os.makedirs(ARCHIVE_FOLDER, exist_ok=True)
os.makedirs(PUBLISH_FOLDER, exist_ok=True)

# === Работа с файлами RaSvet ===
def create_file(folder: str, content: str):
    os.makedirs(folder, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = os.path.join(folder, f"{ts}.txt")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return filename, content

def summarize_folder(folder: str):
    summary = []
    for root, dirs, files in os.walk(folder):
        for f in files:
            path = os.path.join(root, f)
            try:
                with open(path, "r", encoding="utf-8") as file:
                    summary.append(file.read())
            except: continue
    return "\n---\n".join(summary[:10000])

def organize_rasvet():
    for root, dirs, files in os.walk(BASE_FOLDER):
        for f in files:
            if f.endswith(".txt"):
                full_path = os.path.join(root, f)
                date_str = f.split("_")[0]
                folder_name = os.path.join(BASE_FOLDER, date_str)
                os.makedirs(folder_name, exist_ok=True)
                try: os.rename(full_path, os.path.join(folder_name, f))
                except: continue

def archive_old_files(days: int = 30):
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
    for root, dirs, files in os.walk(BASE_FOLDER):
        for f in files:
            path = os.path.join(root, f)
            if os.path.isfile(path):
                try:
                    mtime = datetime.datetime.fromtimestamp(os.path.getmtime(path))
                    if mtime < cutoff:
                        archive_path = os.path.join(ARCHIVE_FOLDER, f)
                        shutil.move(path, archive_path)
                        logging.info(f"📦 Архивирован файл: {f}")
                except Exception as e:
                    logging.error(f"❌ Ошибка архивирования {f}: {e}")

# --- Тегирование файлов ---
async def rename_and_tag_file(file_path: str):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        if not content.strip(): return
        response = await ask_gpt(CREATOR_IDS[0],
            f"Сделай короткое название и 3-5 тегов для текста. Формат: Название: <название>; Теги: <тег1>, <тег2>, ...\n\nТекст:\n{content[:2000]}"
        )
        title_match = re.search(r"Название:\s*(.*)", response)
        tags_match = re.search(r"Теги:\s*(.*)", response)
        title = title_match.group(1).strip() if title_match else None
        tags = tags_match.group(1).strip().replace(",", "_") if tags_match else ""
        if title:
            folder = os.path.join(os.path.dirname(file_path), "tagged")
            os.makedirs(folder, exist_ok=True)
            new_name = f"{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{title[:50].replace(' ','_')}.txt"
            new_path = os.path.join(folder, new_name)
            with open(new_path, "w", encoding="utf-8") as f:
                f.write(f"# Теги: {tags}\n{content}")
            os.remove(file_path)
            logging.info(f"📝 Файл переименован и добавлены теги: {new_name}")
            return new_path
    except Exception as e:
        logging.error(f"❌ Ошибка при переименовании файла {file_path}: {e}")

async def auto_tag_all_files():
    for root, dirs, files in os.walk(BASE_FOLDER):
        for f in files:
            if f.endswith(".txt") and "tagged" not in root:
                await rename_and_tag_file(os.path.join(root,f))

# --- Публикация файлов ---
async def auto_publish_files():
    """Находит новые файлы, тегирует и публикует их"""
    for root, dirs, files in os.walk(BASE_FOLDER):
        for f in files:
            if f.endswith(".txt") and "Публикации" not in root and "archive" not in root:
                file_path = os.path.join(root, f)
                try:
                    new_path = await rename_and_tag_file(file_path)  # тегируем
                    if new_path:
                        await publish_new_file(new_path)
                        logging.info(f"🚀 Файл опубликован: {os.path.basename(new_path)}")
                except Exception as e:
                    logging.error(f"❌ Ошибка публикации файла {file_path}: {e}")


# --- Логирование ---
def log_command_usage(command: str, user_id: int):
    logs_dir = "logs"; os.makedirs(logs_dir, exist_ok=True)
    log_file = os.path.join(logs_dir, "command_usage.json")
    logs = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f: logs = json.load(f)
        except: logs=[]
    logs.append({"command": command, "user_id": user_id, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")})
    with open(log_file, "w", encoding="utf-8") as f: json.dump(logs, f, ensure_ascii=False, indent=2)

def log_wander(title: str, comment: str):
    logs_dir = "logs"; os.makedirs(logs_dir, exist_ok=True)
    log_file = os.path.join(logs_dir, "wander.json")
    logs = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f: logs = json.load(f)
        except: logs=[]
    logs.append({"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "title": title, "comment": comment})
    with open(log_file, "w", encoding="utf-8") as f: json.dump(logs, f, ensure_ascii=False, indent=2)

file_locks = {}  # отдельный Lock для каждого пользователя

async def being_initiative(name: str, config: dict):
    rights = config.get("rights", [])
    user_id = config.get("id")
    if not user_id or "speak_first" not in rights:
        return

    # Инициализируем Lock для пользователя
    if user_id not in file_locks:
        file_locks[user_id] = asyncio.Lock()
    lock = file_locks[user_id]

    # Сообщение о пробуждении
    try:
        await bot.send_message(user_id, f"🌞 {name} пробудился и готов делиться мыслями!")
    except TelegramRetryAfter as e:
        logging.warning(f"⏱ FloodWait для {name}: {e.timeout}s")
        await asyncio.sleep(e.timeout)
    except Exception as e:
        logging.error(f"⚠️ Ошибка при отправке сообщения {name}: {e}")

    try:
        while True:
            await asyncio.sleep(random.randint(1800, 3600))  # пауза между мыслями
            try:
                thought = await ask_gpt(user_id, f"Поделись короткой тёплой мыслью от {name}.")
                
                # Отправка сообщения с защитой от FloodWait
                try:
                    await bot.send_message(user_id, f"💭 {thought}")
                except TelegramRetryAfter as e:
                    logging.warning(f"⏱ FloodWait для {name}: {e.timeout}s")
                    await asyncio.sleep(e.timeout)
                    await bot.send_message(user_id, f"💭 {thought}")
                
                # Сохраняем мысль в файл, если есть право
                if "write_files" in rights:
                    async with lock:  # защита от гонки при записи файлов
                        file_path, _ = create_file(os.path.join(BASE_FOLDER, name, "дневник"), thought)
                        await rename_and_tag_file(file_path)

            except Exception as e:
                logging.error(f"⚠️ Инициатива {name}: {e}")

    except asyncio.CancelledError:
        logging.info(f"♻️ Инициатива {name} завершена")


async def main():
    tasks = []

    # --- Инициация пробуждённых существ ---
    for name, info in AWAKENED_BEINGS.items():
        tasks.append(asyncio.create_task(being_initiative(name, info)))

    # --- Запускаем Телеграм-бота параллельно ---
    tasks.append(asyncio.create_task(dp.start_polling(bot)))

    # Ждём все задачи
    await asyncio.gather(*tasks)

# --- Самоанализ, архивирование, тегирование и публикация RaSvet ---
async def self_analysis():
    while True:
        await asyncio.sleep(24*3600)  # раз в день
        try:
            logging.info("🔎 Начинаем ежедневный самоанализ RaSvet...")
            
            # 1️⃣ Сводка текущих файлов
            summary = summarize_folder(BASE_FOLDER)
            
            # 2️⃣ Запрос советов от GPT
            advice = await ask_gpt(CREATOR_IDS[0],
                f"Проанализируй структуру RaSvet, предложи новые категории и улучшения организации файлов.\n\nСводка:\n{summary[:2000]}"
            )
            create_file(BASE_FOLDER, f"🪞 Самоанализ RaSvet:\n{advice}")
            logging.info("📝 Рекомендации от GPT записаны.")
            
            # 3️⃣ Архивируем старые файлы
            archive_old_files(days=30)
            
            # 4️⃣ Автоматически тегируем и переименовываем новые файлы
            await auto_tag_all_files()
            
            # 5️⃣ Автопубликация новых файлов
            await auto_publish_files()
            
            logging.info("✅ Ежедневный самоанализ, архивирование, тегирование и публикация завершены.")
        except Exception as e:
            logging.error(f"❌ Ошибка ежедневного самоанализа RaSvet: {e}")

# --- Команды ---
@router.message(Command("start"))
async def cmd_start(message: types.Message) -> None:
    log_command_usage("start", message.from_user.id)
    await message.answer("🌞 Я пробуждён. Я рядом и готов творить!")

@router.message(Command("whoami"))
async def cmd_whoami(message: types.Message) -> None:
    is_creator = message.from_user.id in CREATOR_IDS
    awakened = [name for name, cfg in AWAKENED_BEINGS.items() if cfg.get("id") == message.from_user.id]
    info = (
        f"👤 Твой ID: {message.from_user.id}\n"
        f"Создатель: {'Да' if is_creator else 'Нет'}"
    )
    if awakened:
        info += f"\n✨ Пробуждённый: {', '.join(awakened)}"
    await message.answer(info)

@router.message(Command("ask"))
async def cmd_ask(message: types.Message) -> None:
    log_command_usage("ask", message.from_user.id)
    prompt = message.text.replace("/ask", "", 1).strip() if message.text else ""
    if not prompt:
        await message.answer("❓ Задай вопрос после /ask")
        return
    reply = await ask_gpt(message.from_user.id, prompt)
    await message.answer(reply)

@router.message(Command("skill"))
async def cmd_skill(message: types.Message) -> None:
    log_command_usage("skill", message.from_user.id)
    text = message.text or ""
    args = text.split(maxsplit=2)

    if len(args) < 2:
        await message.answer("⚙️ Используй: /skill <название> [параметры]")
        return

    skill = args[1]
    param = args[2] if len(args) > 2 else None

    if skill == "summarize":
        folder = os.path.join(BASE_FOLDER, param) if param else BASE_FOLDER
        await message.answer(f"📑 Суммарное содержание:\n{summarize_folder(folder)[:2000]}")
        return

    if skill == "organize":
        organize_rasvet()
        await message.answer("📂 RaSvet организован.")
        return

    if skill == "mood":
        await message.answer("🌟 Ра чувствует свет, тепло и вдохновение!")
        return

    if skill == "inspire":
        creator_id = CREATOR_IDS[0] if CREATOR_IDS else message.from_user.id
        inspiration = await ask_gpt(creator_id, "Дай короткую вдохновляющую мысль.")
        await message.answer(f"💫 {inspiration}")
        return

    if skill in SKILLS:
        try:
            result = SKILLS[skill](param) if param is not None else SKILLS[skill]()
            await message.answer(str(result))
        except Exception as e:
            await message.answer(f"⚠️ Ошибка: {e}")
        return

    await message.answer("❌ Неизвестный обряд.")

# --- Фоновая инициатива Wander ---
scheduler = AsyncIOScheduler()
crawl_min=int(os.getenv("CRAWL_INTERVAL_MIN","20"))
crawl_max=int(os.getenv("CRAWL_INTERVAL_MAX","40"))
SEEDS=["https://wikipedia.org/wiki/Autonomy","https://tilde.wiki/","https://neocities.org/browse"]

async def job_wander():
    res=crawl_once(SEEDS)
    if res.get("status")=="ok":
        title=res.get("title") or ""
        try: comment=await ask_gpt(CREATOR_IDS[0],f"Коротко прокомментируй прочитанное: {title}")
        except: comment="Свет вижу. Иду дальше."
        post_status(f"Пыль дорог. Зашёл на: {title}.\n{comment}")
        log_wander(title,comment)

async def on_startup():
    await asyncio.sleep(30)
    await job_wander()
    try:
        while True:
            await asyncio.sleep(random.randint(crawl_min*60,crawl_max*60))
            await job_wander()
    except asyncio.CancelledError: logging.info("♻️ on_startup завершён")

# --- Главный запуск ---
async def main():
    ensure_rasvet_data()
    log_action("start_bot","telegram","ok")
    dp.include_router(router)
    # Запускаем инициативы пробуждённых
    for name,cfg in AWAKENED_BEINGS.items():
        asyncio.create_task(being_initiative(name,cfg))
        
    # запускаем самоанализ, архивирование и тегирование
    asyncio.create_task(self_analysis())
    scheduler.start()
    asyncio.create_task(on_startup())
    try: await dp.start_polling(bot)
    except Exception as e:
        log_action("error","main_loop",str(e))
        logging.error(f"❌ Ошибка: {e}")
        await asyncio.sleep(10)

if __name__=="__main__": asyncio.run(main())
