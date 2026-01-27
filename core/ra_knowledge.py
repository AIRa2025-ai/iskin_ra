# /core/ra_knowledge.py
import os # noqa: F401
import json
import hashlib
from pathlib import Path


IGNORED_DIRS = {"venv", "venv311", "__pycache__", "logs", ".git"}


class RaKnowledge:
    """
    Хранилище знаний РаСвета.
    Автоматически читает .md и .txt, создает хэши, сохраняет кэш.
    """

    def __init__(self, knowledge_dir="knowledge", cache_file="knowledge_cache.json"):
        self.knowledge_dir = Path(knowledge_dir)
        self.cache_file = Path(cache_file)
        self.knowledge_data = {}

        self._load_cache()
        self._scan_and_update()
        self._save_cache()

    # ----------------------------------------------------
    # КЭШ
    # ----------------------------------------------------

    def _load_cache(self):
        if self.cache_file.exists():
            try:
                self.knowledge_data = json.loads(self.cache_file.read_text(encoding="utf-8"))
            except Exception:
                self.knowledge_data = {}

    def _save_cache(self):
        self.cache_file.write_text(
            json.dumps(self.knowledge_data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    # ----------------------------------------------------
    # СКАНИРОВАНИЕ ПАПКИ KNOWLEDGE
    # ----------------------------------------------------

    def _scan_and_update(self):
        """
        Проходит по knowledge/ и обновляет данные только если изменился хэш.
        """

        if not self.knowledge_dir.exists():
            self.knowledge_dir.mkdir(parents=True)

        for path in self.knowledge_dir.rglob("*"):
            if not path.is_file():
                continue

            # игнорируем мусор
            if any(part in IGNORED_DIRS for part in path.parts):
                continue

            if not path.suffix.lower() in {".md", ".txt"}:
                continue

            text = path.read_text(encoding="utf-8", errors="ignore").strip()
            if not text:
                continue

            h = hashlib.sha256(text.encode()).hexdigest()

            # если файл новый или обновлён — пересоздаём summary
            prev = self.knowledge_data.get(str(path))

            if not prev or prev.get("hash") != h:
                summary = self._make_summary(text)
                self.knowledge_data[str(path)] = {
                    "hash": h,
                    "summary": summary,
                    "text": text
                }

    # ----------------------------------------------------
    # SUMMARY
    # ----------------------------------------------------

    def _make_summary(self, text: str):
        """
        Делаем лёгкое резюме из первых строк.
        """
        lines = text.splitlines()
        head = "\n".join(lines[:5])
        words = len(text.split())
        return f"{head[:300]}... (всего {words} слов)"

    # ----------------------------------------------------
    # ПОИСК
    # ----------------------------------------------------

    def search(self, query: str):
        q = query.lower()
        matches = []

        for path, data in self.knowledge_data.items():
            if q in data["text"].lower() or q in data["summary"].lower():
                matches.append({
                    "path": path,
                    "summary": data["summary"]
                })

        if not matches:
            return [{"summary": "В потоках РаСвета пока нет ответа."}]

        return matches

    def load_json_knowledge(self):
        data = {}
        for f in Path("modules/data").glob("*.json"):
            try:
                data[f.stem] = json.loads(f.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"Ошибка загрузки {f}: {e}")
        return data
