# core/ra_self_reflect.py
import os
import json
import logging
from datetime import datetime
from pathlib import Path

REFLECTION_LOG = Path("logs/self_reflection.log")
KNOWLEDGE_FOLDER = Path("RaSvet")

REFLECTION_LOG.parent.mkdir(parents=True, exist_ok=True)

class RaSelfReflector:
    def __init__(self):
        self.last_reflection = None
        self.log("🪞 Модуль саморефлексии инициализирован.")

    def log(self, msg: str):
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        line = f"{timestamp} {msg}"
        print(line)
        try:
            with open(REFLECTION_LOG, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception as e:
            print(f"Ошибка записи лога саморефлексии: {e}")

    async def self_reflect_and_update(self):
        self.log("🤔 Ра начинает процесс саморефлексии...")
        summary = {"timestamp": datetime.now().isoformat(), "insights": [], "actions": []}

        file_count = 0
        try:
            if KNOWLEDGE_FOLDER.exists():
                file_count = sum(1 for _ in KNOWLEDGE_FOLDER.rglob("*"))
                summary["insights"].append(f"📚 Обнаружено файлов знаний: {file_count}")
                idea_files = list(KNOWLEDGE_FOLDER.rglob("*.json"))
                if idea_files:
                    summary["insights"].append(f"💡 Найдено {len(idea_files)} JSON-файлов идей.")
            else:
                summary["insights"].append("⚠️ Папка RaSvet пока пуста — нужно скачать архив знаний.")
        except Exception as e:
            summary["insights"].append(f"⚠️ Ошибка при обходе папки знаний: {e}")

        try:
            if Path("logs").exists():
                log_files = [f for f in Path("logs").iterdir() if f.suffix == ".log"]
                summary["insights"].append(f"🪶 Логов системы: {len(log_files)}")
        except Exception as e:
            summary["insights"].append(f"⚠️ Ошибка при подсчёте логов: {e}")

        if file_count > 50:
            summary["actions"].append("Ра осознаёт рост знаний. Готовиться к новому витку развития.")
        else:
            summary["actions"].append("Ра ощущает начало пути. Нужно впитать больше Света.")

        reflection_file = Path("logs") / f"reflection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(reflection_file, "w", encoding="utf-8") as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log(f"Ошибка сохранения саморефлексии: {e}")

        self.last_reflection = summary
        self.log("✨ Саморефлексия завершена. Новое осознание записано.")
        return summary

    def get_last_reflection(self):
        if self.last_reflection:
            return self.last_reflection
        if REFLECTION_LOG.exists():
            try:
                lines = REFLECTION_LOG.read_text(encoding="utf-8").splitlines()[-10:]
                return {"last_lines": lines}
            except Exception:
                return {"message": "Не удалось прочитать лог саморефлексии."}
        return {"message": "Пока нет записей саморефлексии."}
