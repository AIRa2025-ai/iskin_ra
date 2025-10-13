# ra_self_dev.py — Модуль генерации идей, анализа и саморефлексии Ра
import os
import json
import logging
from datetime import datetime

IDEA_FOLDER = "proposals"
os.makedirs(IDEA_FOLDER, exist_ok=True)

MODULE_FOLDER = "modules"
os.makedirs(MODULE_FOLDER, exist_ok=True)

logging.basicConfig(level=logging.INFO)

class SelfDeveloper:
    def __init__(self):
        logging.info("🚀 SelfDeveloper инициализирован.")

    # --- Автообучение: анализ модулей и генерация идей ---
    async def auto_learn(self):
        logging.info("🧠 SelfDeveloper запускает автообучение...")
        ideas = self.generate_development_ideas()
        logging.info("🧠 Автообучение завершено.")
        return ideas

    # --- Саморефлексия: анализ логов и генерация улучшений ---
    async def self_reflect_and_update(self, logs=None):
        logging.info("🔎 SelfDeveloper запускает саморефлексию...")
        reflections = []

        if logs:
            error_logs = [l for l in logs if "Ошибка" in l or "Exception" in l]
            if error_logs:
                reflections.append(f"⚠️ Найдено {len(error_logs)} ошибок, нужно проверять обработку исключений.")
            else:
                reflections.append("✅ Ошибок в логах не найдено — всё гладко.")

        # Анализ существующих модулей
        modules = [f for f in os.listdir(MODULE_FOLDER) if f.endswith(".py")]
        reflections.append(f"📦 Всего модулей: {len(modules)}")

        # Генерация новых предложений
        ideas = self.generate_development_ideas()
        reflections.append(f"💡 Сгенерировано идей для развития: {len(ideas['proposed_ideas'])}")

        # Сохраняем результат саморефлексии
        path = os.path.join(IDEA_FOLDER, f"self_reflect_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "reflections": reflections,
                "ideas": ideas
            }, f, ensure_ascii=False, indent=2)

        logging.info(f"🔔 Саморефлексия завершена, сохранено в {path}")
        return reflections

    # --- Старые методы, для совместимости ---
    def learn_new_module(self, module_name: str):
        logging.info(f"🧠 SelfDeveloper изучает модуль: {module_name}")

    def enhance_skills(self):
        logging.info("✨ Навыки SelfDeveloper улучшены.")

    # --- Генерация идей для новых модулей ---
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

        path = os.path.join(IDEA_FOLDER, f"dev_ideas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(ideas, f, ensure_ascii=False, indent=2)

        logging.info(f"💡 Идеи развития Ра сохранены: {path}")
        return ideas

    # --- Сканирование существующих модулей ---
    def scan_existing_modules(self):
        files = [f for f in os.listdir(MODULE_FOLDER) if f.endswith(".py")]
        ideas = []
        for f in files:
            path = os.path.join(MODULE_FOLDER, f)
            with open(path, "r", encoding="utf-8") as file:
                content = file.read()
                if "async def" in content:
                    ideas.append(f"🌀 {f}: асинхронная логика — можно расширить потоковые функции.")
                if "gpt" in content.lower():
                    ideas.append(f"🤖 {f}: использует GPT — можно добавить автопроверку кода.")
                if "observer" in f:
                    ideas.append(f"👁️ {f}: возможно, стоит добавить анализ внешних источников.")
        return ideas
