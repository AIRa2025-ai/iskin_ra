# core/ra_bot_gpt.py — Telegram-интерфейс Ра

import os
import sys
import json
import logging
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from importlib import import_module

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message

# -------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

LOG_DIR = ROOT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "command_usage.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# -------------------------------------------------
def safe_import(path):
    try:
        return import_module(path)
    except Exception as e:
        logging.warning(f"import fail {path}: {e}")
        return None

gpt_module = safe_import("core.gpt_module")
safe_ask = getattr(gpt_module, "safe_ask", None)

ra_core_mod = safe_import("core.ra_core_mirolub")
RaCoreMirolub = getattr(ra_core_mod, "RaCoreMirolub", None)

ra_mirolub = RaCoreMirolub() if RaCoreMirolub else None

# -------------------------------------------------
def log_command(user_id, text):
    try:
        data = json.loads(LOG_FILE.read_text("utf-8")) if LOG_FILE.exists() else []
        data.append({
            "user": user_id,
            "text": text,
            "time": datetime.utcnow().isoformat()
        })
        cutoff = datetime.utcnow() - timedelta(days=10)
        data = [x for x in data if datetime.fromisoformat(x["time"]) > cutoff]
        LOG_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
    except Exception:
        pass

# -------------------------------------------------
async def process_message(message: Message):
    text = (message.text or "").strip()
    if not text:
        return

    log_command(message.from_user.id, text)

    if safe_ask:
        await message.answer("⏳ Думаю…")
        try:
            reply = await safe_ask(message.from_user.id, [{"role": "user", "content": text}])
            await message.answer(reply)
            return
        except Exception:
            pass

    if ra_mirolub:
        reply = await ra_mirolub.process(text)
        await message.answer(reply)
        return

    await message.answer("⚠️ Я здесь, брат, но сейчас в тишине.")

# -------------------------------------------------
dp = Dispatcher()
router = Router()

@router.message(Command("start"))
async def start_cmd(m: Message):
    await m.answer("🌞 Ра на связи. Пиши.")

@router.message()
async def all_text(m: Message):
    if m.text.startswith("/"):
        return
    await process_message(m)

# -------------------------------------------------
async def main():
    load_dotenv()
    bot = Bot(os.getenv("BOT_TOKEN"))
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
