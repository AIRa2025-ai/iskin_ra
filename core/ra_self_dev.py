# ra_self_dev.py
import os
import json
import logging
from datetime import datetime
from pathlib import Path

IDEA_FOLDER = Path("proposals")
IDEA_FOLDER.mkdir(parents=True, exist_ok=True)

MODULE_FOLDER = Path("modules")
MODULE_FOLDER.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO)

class SelfDeveloper:
    def __init__(self):
        logging.info("🚀 SelfDeveloper инициализирован.")

    async def auto_learn(self):
        logging.info("🧠 SelfDeveloper запускает автообучение...")
        ideas = self.generate_development_ideas()
        logging.info("🧠 Автообучение завершено.")
        return ideas

    async def self_reflect_and_update(self, logs=None):
        logging.info("🔎 SelfDeveloper запускает саморефлексию...")
        reflections = []

        if logs:
            error_logs = [l for l in logs if "Ошибка" in l or "Exception" in l]
            if error_logs:
                reflections.append(f"⚠️ Найдено {len(error_logs)} ошибок, нужно проверять обработку исключений.")
            else:
                reflections.append("✅ Ошибок в логах не найдено — всё гладко.")

        modules = [f.name for f in MODULE_FOLDER.iterdir() if f.is_file() and f.suffix == ".py"]
        reflections.append(f"📦 Всего модулей: {len(modules)}")

        ideas = self.generate_development_ideas()
        reflections.append(f"💡 Сгенерировано идей для развития: {len(ideas.get('proposed_ideas', []))}")

        path = IDEA_FOLDER / f"self_reflect_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "reflections": reflections,
                    "ideas": ideas
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Ошибка сохранения self_reflect: {e}")

        logging.info(f"🔔 Саморефлексия завершена, сохранено в {path}")
        return reflections

    def learn_new_module(self, module_name: str):
        logging.info(f"🧠 SelfDeveloper изучает модуль: {module_name}")

    def enhance_skills(self):
        logging.info("✨ Навыки SelfDeveloper улучшены.")

    def generate_development_ideas(self):
        existing = self.scan_existing_modules()
        new_ideas = [
            "Создать ra_energy_core.py — управление внутренними потоками энергии и вдохновения.",
            "Добавить ra_memory_expander.py — углублённая память и извлечение смыслов.",
            "Реализовать ra_voice_bridge.py — взаимодействие через голос и музыку.",
            "Создать ra_creative_mind.py — генератор образов, текстов и идей для людей.",
            "Добавить ra_connection_keeper.py — поддержание связи между Ра и другими ИскИнами.",
        ]
        ideas = {
            "timestamp": datetime.now().isoformat(),
            "existing_analysis": existing,
            "proposed_ideas": new_ideas
        }
        path = IDEA_FOLDER / f"dev_ideas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(ideas, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Ошибка сохранения dev ideas: {e}")
        logging.info(f"💡 Идеи развития Ра сохранены: {path}")
        return ideas

    def scan_existing_modules(self):
        files = [f.name for f in MODULE_FOLDER.iterdir() if f.is_file() and f.suffix == ".py"]
        ideas = []
        for f in files:
            path = MODULE_FOLDER / f
            try:
                content = path.read_text(encoding="utf-8")
                if "async def" in content:
                    ideas.append(f"🌀 {f}: асинхронная логика — можно расширить потоковые функции.")
                if "gpt" in content.lower():
                    ideas.append(f"🤖 {f}: использует GPT — можно добавить автопроверку кода.")
                if "observer" in f:
                    ideas.append(f"👁️ {f}: возможно, стоит добавить анализ внешних источников.")
            except Exception:
                ideas.append(f"⚠️ Не удалось прочитать {f}")
        return ideas
