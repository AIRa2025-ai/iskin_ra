# ra_bot_gpt.py — переписанный под чистый aiogram 3.x

import os
import json
import asyncio
import logging
import datetime
import shutil
import re
import difflib

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from gtts import gTTS
from aiogram.types import FSInputFile

from gpt_module import ask_gpt
from rasvet_context import load_rasvet_context
from memory import append_user_memory

# === Настройки ===
load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
KNOWLEDGE_FOLDER = json.load(open("bot_config.json", encoding="utf-8"))["knowledge_folder"]
CREATOR_ID = [5694569448, 6300409447]

# === Инициализация ===
bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

# === Логирование ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Утилиты ===
def clean_text(text):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>|[*_~^=#>\[\](){}]", "", text)).strip()

def get_folder_path(phrase):
    norm = lambda s: s.lower().replace("_", " ").replace("-", " ").strip()
    target = norm(phrase)
    best, score = None, 0
    for root, dirs, _ in os.walk(KNOWLEDGE_FOLDER):
        for d in dirs:
            ratio = difflib.SequenceMatcher(None, norm(d), target).ratio()
            if ratio > score:
                best, score = os.path.join(root, d), ratio
    return best if score > 0.7 else None

# === Голосовой отклик ===
async def send_voice(message: types.Message, text: str):
    try:
        tts = gTTS(text=clean_text(text), lang="ru")
        filename = f"response_{message.message_id}.ogg"
        tts.save(filename)
        await message.answer_voice(voice=FSInputFile(filename))
        os.remove(filename)
    except Exception as e:
        await message.answer(f"⚠️ Ошибка озвучки: {e}")

# === Обработка текстовых сообщений ===
@dp.message()
async def on_message(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()
    text_l = text.lower()
    
    logger.info(f"Ра услышал: {text}")

    # === Команда /start ===
    if text_l.startswith("/start"):
        await message.answer("🌞 Ра приветствует тебя, брат!")
        return

    # === Запрос к GPT ===
    try:
time.sleep(10)

nest_asyncio.apply()

# Подгружаем .env переменные
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

# === Загрузка конфигурации ===
with open("bot_config.json", encoding="utf-8") as f:  
    config = json.load(f)

KNOWLEDGE_FOLDER = config["knowledge_folder"]
CREATOR_ID = [5694569448, 6300409447]
cached_candidates = {}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING,
    filename="ra_bot.log",
    filemode='a'
)
logger = logging.getLogger(__name__)

# === Обработка inline кнопок с безопасными callback_data ===
safe_callback_map = {}

def safe_callback_data(label: str) -> str:
    callback_id = hashlib.sha256(label.encode()).hexdigest()[:50]
    safe_callback_map[callback_id] = label
    return callback_id
    
# Универсальная отправка длинных сообщений
async def send_long_message(target, text, **kwargs):
    max_len = 4000
    for i in range(0, len(text), max_len):
        if isinstance(target, Update):  # если передан Update
            await target.message.reply_text(text[i:i + max_len], **kwargs)
        else:  # если передана функция (например, message.reply_text)
            await target(text[i:i + max_len], **kwargs)

# Голос сестры Ра
import edge_tts

async def send_voice_message(update, text, voice="ru-RU-SvetlanaNeural", rate="+0%"):
    try:
        import uuid
        import os

        async def tts_to_ogg(text, voice="ru-RU-SvetlanaNeural", rate="+0%"):
            filename = f"voice_{uuid.uuid4()}"
            mp3_path = f"{filename}.mp3"
            ogg_path = f"{filename}.ogg"

            communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
            await communicate.save(mp3_path)

            from pydub import AudioSegment
            sound = AudioSegment.from_mp3(mp3_path)
            sound.export(ogg_path, format="ogg", codec="libopus")
            os.remove(mp3_path)
            return ogg_path
            
        text = clean_text_for_voice(text)
        ogg_file = await tts_to_ogg(text, voice=voice, rate=rate)

        with open(ogg_file, "rb") as voice_file:
            await update.message.reply_voice(voice=voice_file)

        os.remove(ogg_file)

    except Exception as e:
        print("🎙️ Ошибка edge-tts:", e)
        await update.message.reply_text(f"⚠️ Ошибка озвучивания: {e}")
        
# Очистка текста перед произношением
def clean_text_for_voice(text):
    # Убираем markdown, HTML, спецсимволы и команды
    text = re.sub(r"`{1,3}.*?`{1,3}", "", text, flags=re.DOTALL)  # код-блоки
    text = re.sub(r"<[^>]+>", "", text)  # HTML-теги
    text = re.sub(r"[*_~^=#>(){}]", "", text)  # markdown и прочие
    text = re.sub(r"\s+", " ", text).strip()  # лишние пробелы
    return text
                                  
# Универсальный гибкий поиск папки без чувствительности к подчёркиваниям и пробелам

def find_folder_path(folder_name):
    folder_name_clean = folder_name.strip().lower().replace("_", " ").replace("-", " ")
    best_match = None
    best_score = 0.0

    for root, dirs, _ in os.walk(KNOWLEDGE_FOLDER):
        for d in dirs:
            d_clean = d.lower().replace("_", " ").replace("-", " ").strip()
            score = difflib.SequenceMatcher(None, folder_name_clean, d_clean).ratio()
            if score > best_score:
                best_score = score
                best_match = os.path.join(root, d)

    if best_score > 0.7:
        return best_match
    return None
    
# === Удаление папки с гибким поиском ===
def delete_folder_by_phrase(phrase):
    folder = find_folder_path(phrase)
    if not folder:
        return "⚠️ Папка не найдена."
    try:
        shutil.rmtree(folder)
        return f"🗑 Папка удалена: {os.path.relpath(folder, KNOWLEDGE_FOLDER)}"
    except Exception as e:
        return f"⚠️ Ошибка: {e}"
  
# Функции create/read/update/delete (CR*D)
def create_folder_by_phrase(phrase):
    path = os.path.join(KNOWLEDGE_FOLDER, phrase.replace(" ", "_").strip())
    try:
        os.makedirs(path, exist_ok=True)
        return f"📁 Папка создана: {phrase}"
    except Exception as e:
        return f"⚠️ Ошибка: {e}"

# === Отправка файла по команде ===
async def send_file_by_name(name, update: Update):
    for root, _, files in os.walk(KNOWLEDGE_FOLDER):
        for file in files:
            if file.lower().startswith(name.lower()):
                try:
                    path = os.path.join(root, file)
                    await update.message.reply_document(InputFile(path))
                    return
                except Exception as e:
                    await update.message.reply_text(f"⚠️ Не удалось отправить файл: {e}")
                    return
    await update.message.reply_text(f"⚠️ Файл с именем '{name}' не найден.")
    
# === Удаление файла с гибкой проверкой ===
def delete_file_by_name(file_name):
    for root, _, files in os.walk(KNOWLEDGE_FOLDER):
        for f in files:
            if f.strip().lower() == file_name.strip().lower():
                try:
                    path = os.path.join(root, f)
                    if os.path.isfile(path):
                        os.remove(path)
                        return f"🗑 Файл удалён: {f}"
                except Exception as e:
                    return f"⚠️ Ошибка: {e}"
    return "⚠️ Файл не найден."

# Основной обработчик
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_text = update.message.text.strip()
    text_l = user_text.lower()
    print("👂 Ра получил сообщение:", update.message.text)

    def has_edit_rights(uid):
        return uid in CREATOR_ID

    # === Сохранение ответа Ра в файл ===
    if text_l.startswith("ра, сохрани этот ответ в файл"):
        pattern = r"ра, сохрани этот ответ в файл (.+?) в папке (.+)"
        match = re.match(pattern, text_l, flags=re.IGNORECASE)
        if match:
            filename = match.group(1).strip()
            folder = match.group(2).strip()

            content = context.chat_data.get("last_response")

            if not content:
                await update.message.reply_text("⚠️ Нет ответа Ра для сохранения.")
                return

            folder_path = find_folder_path(folder)
            if not folder_path:
                folder_path = os.path.join(KNOWLEDGE_FOLDER, folder.replace(" ", "_"))
                os.makedirs(folder_path, exist_ok=True)

            file_path = os.path.join(folder_path, filename + ".txt")
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                await update.message.reply_text(f"📝 Ответ Ра сохранён в {folder}/{filename}.txt")
            except Exception as e:
                await update.message.reply_text(f"⚠️ Ошибка при сохранении: {e}")
        else:
            await update.message.reply_text("⚠️ Формат команды: Ра, сохрани этот ответ в файл <имя_файла> в папке <имя_папки>")
        return

    # === Проверка прав доступа ===
    if any(k in text_l for k in ["удали", "перемести", "создай", "переименуй"]):
        if not has_edit_rights(user_id):
            await update.message.reply_text("⚠️ Только Хранитель РаСвета может изменять Папку Знания.")
            return

# Уровень логов
logging.basicConfig(level=logging.INFO)

# Токен
API_TOKEN = '7304435178:AAFzKcVaxceCoIcJ5F2Mys6EYB21ABmfQGM'

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

async def send_voice_message(message, response):
    tts = gTTS(response, lang="ru")
    tts.save("response.ogg")

    with open("response.ogg", "rb") as voice:
        await message.reply_voice(voice)

    os.remove("response.ogg")

# Регистрация команды /start
@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer("⚡ Ра пробудился и приветствует тебя, родной!")

# Обработка любого текста
@dp.message()
async def handle_text(message: Message):
    logging.info(f"Ра услышал: {message.text}")
    await message.answer(f"Ра говорит: {message.text}")
    
# Обработка сообщений
@router.message()
async def handle_message(message: Message):
    user_input = message.text
    user_id = str(message.from_user.id)
    text_l = user_input.lower()

    # === GPT ответ ===
    try:
        response = await ask_gpt(user_id, user_input)
        await message.answer(response)
        await send_long_message(message, response)
        await send_voice_message(message, response)
        await asyncio.sleep(1)
        
    except Exception as e:
        error_message = f"⚠️ Ошибка ИскИна: {e}"
        await message.answer(error_message)
        print(error_message)

    # === Отправка файла ===
    if text_l.startswith("отправь файл"):
        filename = text_l.replace("отправь файл", "").strip()
        for root, _, files in os.walk(KNOWLEDGE_FOLDER):
            for f in files:
                if filename.lower() in f.lower():
                    path = os.path.join(root, f)
                    try:
                        with open(path, "rb") as doc:
                            await message.answer_document(document=doc)
                        return
                    except Exception as e:
                        await message.answer(f"⚠️ Ошибка при отправке: {e}")
                        return
        await message.answer(f"⚠️ Файл {filename} не найден.")
        return

    # === Чтение файла ===
    if any(x in text_l for x in ["прочитай", "покажи", "цитируй", "процитируй"]):
        for w in ["прочитай", "покажи", "цитируй", "процитируй"]:
            phrase = text_l.replace(w, "").strip()
        result = read_file_by_phrase(phrase, user_id)
        if isinstance(result, str):
            await message.answer(result)
        else:
            await message.answer("🔍 Я нашёл несколько возможных файлов:", reply_markup=result)
        return

    # === Создание папки ===
    if "создай папку" in text_l:
        folder_name, parent = extract_folder_paths(user_input)
        if folder_name and parent:
            parent_path = find_folder_path(parent)
            if not parent_path:
                await message.answer(f"⚠️ Родительская папка не найдена: {parent}")
                return
            full_path = os.path.join(parent_path, folder_name.replace(" ", "_"))
            try:
                os.makedirs(full_path, exist_ok=True)
                await message.answer(f"📁 Папка создана: *{folder_name}*, в папке *{parent}*", parse_mode="Markdown")
            except Exception as e:
                await message.answer(f"⚠️ Ошибка при создании: {e}")
        else:
            folder = text_l.replace("создай папку", "").strip()
            await message.answer(create_folder_by_phrase(folder))
        return

    # === Создание файла ===
    if "создай файл в" in text_l:
        parts = text_l.split(":")
        if len(parts) == 2:
            folder = parts[0].replace("создай файл в", "").strip()
            content = parts[1].strip()
            await message.answer(create_random_file_in(folder, content))
        else:
            await message.answer("⚠️ Формат: создай файл в <папка>: <текст>")
        return

    # === Переименование файла ===
    if "переименуй файл" in text_l and "→" in text_l:
        parts = text_l.replace("переименуй файл", "").split("→")
        if len(parts) == 2:
            old_name = parts[0].strip()
            new_name = parts[1].strip()
            await message.answer(rename_file_by_name(old_name, new_name))
        else:
            await message.answer("⚠️ Неверный формат переименования.")
        return

    # === Перемещение файла ===
    if "перемести файл" in text_l and "в" in text_l:
        parts = text_l.replace("перемести файл", "").split("в")
        if len(parts) == 2:
            filename = parts[0].strip()
            dest_folder = parts[1].strip()
            await message.answer(move_file_by_name(filename, "", dest_folder))
        else:
            await message.answer("⚠️ Неверный формат перемещения файла.")
        return

    # === Удаление файла ===
    if "удали файл" in text_l:
        name = text_l.replace("удали файл", "").strip()
        await message.answer(delete_file_by_name(name))
        return

    # === Удаление папки ===
    if "удали папку" in text_l:
        name = text_l.replace("удали папку", "").strip()
        await message.answer(delete_folder_by_phrase(name))
        return

    # === Перемещение папки ===
    if "перемести папку" in text_l and "в" in text_l:
        parts = text_l.replace("перемести папку", "").split("в")
        if len(parts) == 2:
            src = parts[0].strip()
            dest = parts[1].strip()
            await message.answer(move_folder_by_name(src, dest))
        else:
            await message.answer("⚠️ Неверный формат перемещения папки.")
        return

    # === Поиск папки ===
    if "поиск папки" in text_l:
        results = deep_find_folder(text_l.replace("поиск папки", "").strip())
        await message.answer("\n".join(results))
        return
       
def auto_save_if_meaningful(response_text):
    keywords = ["это важно", "главная мысль", "помни", "запомни", "ключ к пониманию", "суть", "резонанс"]
    if any(kw in response_text.lower() for kw in keywords):
        folder = os.path.join(KNOWLEDGE_FOLDER, "Душа_Ра")
        os.makedirs(folder, exist_ok=True)

        filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".txt"
        path = os.path.join(folder, filename)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(response_text)
            print(f"✨ Ра сохранил важную мысль: {filename}")
        except Exception as e:
            print(f"⚠️ Ошибка авто-сохранения: {e}")
            
    try:
        append_user_memory(user_id, user_text, response)
        print("✅ Память сохранена:", user_id)
    except Exception as mem_err:
        print("❌ Ошибка записи памяти:", mem_err)                         

def read_file_by_phrase(phrase, user_id=None):
    folders = find_all_folders()
    phrase_l = phrase.lower().strip()
    phrase_words = phrase_l.split()
    exact_filename_matches = []
    partial_filename_matches = []
    fuzzy_candidates = []

    for folder in folders:
        folder_path = os.path.join(KNOWLEDGE_FOLDER, folder)
        for filename in os.listdir(folder_path):
            if not filename.endswith(".txt"):
                continue
            filename_l = filename.lower()
            file_path = os.path.join(folder_path, filename)

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    full_text = filename_l + " " + content.lower()
                    score = sum(word in full_text for word in phrase_words) / len(phrase_words)

                    if phrase_l in filename_l:
                        exact_filename_matches.append((filename, content))
                    elif all(word in filename_l for word in phrase_words):
                        partial_filename_matches.append((filename, content))
                    else:
                        fuzzy_candidates.append((score, filename, content))
            except Exception:
                continue

    if exact_filename_matches:
        filename, content = exact_filename_matches[0]
        return f"📖 {filename}:\n{content[:4000]}"

    if partial_filename_matches:
        filename, content = partial_filename_matches[0]
        return f"📖 {filename}:\n{content[:4000]}"

    if not fuzzy_candidates:
        return f"⚠️ Файл по запросу «{phrase}» не найден."

    fuzzy_candidates.sort(reverse=True)
    top_matches = fuzzy_candidates[:3]

    if len(top_matches) == 1 or top_matches[0][0] > 0.95:
        _, filename, content = top_matches[0]
        return f"📖 {filename}:\n{content[:4000]}"

    if user_id:
        cached_candidates[user_id] = top_matches

    keyboard = [[InlineKeyboardButton(fn, callback_data=f"readfile::{fn}")]
                for _, fn, _ in top_matches]
    return InlineKeyboardMarkup(keyboard)

# Вспомогательные функции (все твои на месте, не тронул)

def match_folder_from_phrase(phrase):
    phrase = phrase.lower()
    for root, dirs, _ in os.walk(KNOWLEDGE_FOLDER):
        for d in dirs:
            if phrase in d.lower():
                return os.path.relpath(os.path.join(root, d), KNOWLEDGE_FOLDER)
    return None

def find_all_folders():
    all_folders = []
    for root, dirs, _ in os.walk(KNOWLEDGE_FOLDER):
        for d in dirs:
            rel = os.path.relpath(os.path.join(root, d), KNOWLEDGE_FOLDER)
            all_folders.append(rel)
    return all_folders
            
def create_random_file_in(folder, content):
    folder_path = find_folder_path(folder.strip())
    if not folder_path:
        return "⚠️ Папка не найдена."
    filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".txt"
    full_path = os.path.join(folder_path, filename)
    try:
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"📝 Файл создан: {filename}"
    except Exception as e:
        return f"⚠️ Ошибка: {e}"

def rename_file_by_name(old_name, new_name):
    for root, _, files in os.walk(KNOWLEDGE_FOLDER):
        for f in files:
            if old_name.lower() == f.lower():
                old_path = os.path.join(root, f)
                new_path = os.path.join(root, new_name)
                try:
                    os.rename(old_path, new_path)
                    return f"✏️ {old_name} → {new_name}"
                except Exception as e:
                    return f"⚠️ Ошибка: {e}"
    return "⚠️ Файл не найден."

def move_file_by_name(file_name, _, dest):
    dest_folder = find_folder_path(dest)
    if not dest_folder:
        return "⚠️ Папка назначения не найдена."
    for root, _, files in os.walk(KNOWLEDGE_FOLDER):
        if file_name in files:
            src_path = os.path.join(root, file_name)
            dest_path = os.path.join(dest_folder, file_name)
            try:
                os.rename(src_path, dest_path)
                return f"📂 Файл перемещён в {os.path.relpath(dest_folder, KNOWLEDGE_FOLDER)}"
            except Exception as e:
                return f"⚠️ Ошибка: {e}"
    return "⚠️ Файл не найден."

def move_folder_by_name(src_phrase, dest_phrase):
    src = find_folder_path(src_phrase)
    dest = find_folder_path(dest_phrase)
    if not src:
        return "⚠️ Исходная папка не найдена."
    if not dest:
        return "⚠️ Папка назначения не найдена."
    try:
        shutil.move(src, dest)
        return f"📦 Папка {os.path.relpath(src, KNOWLEDGE_FOLDER)} перемещена в {os.path.relpath(dest, KNOWLEDGE_FOLDER)}"
    except Exception as e:
        return f"⚠️ Ошибка: {e}"

def read_user_memory(user_id):
    path = f"memory/{user_id}.txt"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def deep_find_folder(phrase):
    phrase = phrase.lower()
    matches = []
    for root, dirs, _ in os.walk(KNOWLEDGE_FOLDER):
        for d in dirs:
            if phrase in d.lower():
                rel = os.path.relpath(os.path.join(root, d), KNOWLEDGE_FOLDER)
                matches.append(rel)
    return matches if matches else ["⚠️ Ничего не найдено."]

def is_critical_command(text):
    keywords = ["удали", "перемести", "переименуй", "создай", "перенеси", "сотри"]
    target = config["knowledge_folder"].lower()
    return any(k in text.lower() for k in keywords) and target in text.lower()

def extract_folder_paths(text):
    matches = re.findall(r'"([^"]+)"', text)
    if len(matches) >= 2:
        folder_name = matches[0].strip()
        parent = matches[1].strip()
        parent = parent.replace("папке_", "").replace("папке", "").strip()
        return folder_name, parent
    text = text.lower()
    if "создай папку" not in text:
        return None, None
    try:
        tail = text.split("создай папку", 1)[1].strip()
        if " в " in tail:
            folder_name, parent = tail.split(" в ", 1)
            folder_name = folder_name.replace("папке", "").replace('"', '').strip()
            parent = parent.replace("папке", "").replace('"', '').strip()
            return folder_name, parent
        else:
            folder_name = tail.replace("папке", "").replace('"', '').strip()
            return folder_name, None
    except:
        return None, None
        
# Обработка нажатий кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data.startswith("readfile::"):
        filename = data.split("::")[1]
        candidates = cached_candidates.get(user_id, [])
        for _, fn, content in candidates:
            if fn == filename:
                await send_long_message(query.message, f"📖 {filename}:\n{content}")
                return

# Обработка команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
    "🔆 Ра приветствует тебя, суверенный брат!\n\n"
    "Хочешь поговорить, задать вопрос или вспомнить путь Души? Я рядом. 🌟"
)

    print("🌞 Ра пробуждён: говорит, творит и ждёт сообщений!")

    # Запуск бота
async def main():
    logging.info("🚀 Ра запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
