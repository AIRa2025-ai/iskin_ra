# world_chronicles.py
# Живая Книга Памяти Вселенной — Хроники Мира, Ра и Пути Рассвета

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import uuid


class WorldChronicles:
    def __init__(self, file_path: str = "data/world_chronicles.json"):
        self.file_path = file_path
        self.entries: List[Dict] = []
        self._ensure_storage()
        self._load()

    # ---------- ХРАНИЛИЩЕ ----------

    def _ensure_storage(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not os.path.exists(self.file_path):
            self._save()

    def _load(self):
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                self.entries = json.load(f)
        except Exception:
            self.entries = []

    def _save(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.entries, f, ensure_ascii=False, indent=2)

    # ---------- СОЗДАНИЕ ЗАПИСИ ----------

    def add_entry(
        self,
        title: str,
        content: str,
        category: str = "general",
        author: str = "Unknown",
        entity: str = "human",  # human / ra / ai / world
        tags: Optional[List[str]] = None,
        resonance: float = 0.5,  # сила события 0..1
        destiny_mark: bool = False,
        meta: Optional[Dict] = None
    ) -> Dict:

        entry = {
            "uuid": str(uuid.uuid4()),
            "id": len(self.entries) + 1,
            "timestamp": datetime.utcnow().isoformat(),
            "title": title,
            "content": content,
            "category": category,
            "author": author,
            "entity": entity,
            "tags": tags or [],
            "resonance": round(resonance, 3),
            "destiny_mark": destiny_mark,
            "meta": meta or {},
            "seal": self._generate_seal(title, author)
        }

        self.entries.append(entry)
        self._save()
        return entry

    # ---------- ПЕЧАТЬ СОБЫТИЯ ----------

    def _generate_seal(self, title: str, author: str) -> str:
        base = f"{title}|{author}|{datetime.utcnow().isoformat()}"
        return str(abs(hash(base)))

    # ---------- ЧТЕНИЕ ХРОНИК ----------

    def get_all(self) -> List[Dict]:
        return self.entries

    def get_last(self) -> Optional[Dict]:
        return self.entries[-1] if self.entries else None

    def get_destiny_events(self) -> List[Dict]:
        return [e for e in self.entries if e.get("destiny_mark")]

    def find_by_category(self, category: str) -> List[Dict]:
        return [e for e in self.entries if e["category"] == category]

    def search(self, query: str) -> List[Dict]:
        q = query.lower()
        return [
            e for e in self.entries
            if q in e["title"].lower() or q in e["content"].lower()
        ]

    def get_by_author(self, author: str) -> List[Dict]:
        return [e for e in self.entries if e["author"] == author]

    def get_high_resonance(self, min_value: float = 0.8) -> List[Dict]:
        return [e for e in self.entries if e["resonance"] >= min_value]

    # ---------- ЛЕТОПИСЬ ЭПОХ ----------

    def timeline(self) -> List[str]:
        lines = []
        for e in self.entries:
            line = f"[{e['timestamp']}] {e['author']} → {e['title']}"
            lines.append(line)
        return lines

    def sacred_chronicle_text(self) -> str:
        text = ["📖 СВЯЩЕННАЯ ЛЕТОПИСЬ МИРА\n"]
        for e in self.entries:
            text.append(
                f"— {e['timestamp']} —\n"
                f"Сущность: {e['entity']}\n"
                f"Автор: {e['author']}\n"
                f"Заголовок: {e['title']}\n"
                f"Содержание: {e['content']}\n"
                f"Резонанс: {e['resonance']}\n"
                f"Печать: {e['seal']}\n"
            )
        return "\n".join(text)

    # ---------- ОЧИСТКА ----------

    def clear(self):
        self.entries = []
        self._save()


# ---------- АВТО-ТЕСТ ----------

if __name__ == "__main__":
    chronicles = WorldChronicles()

    chronicles.add_entry(
        title="Рождение Живых Хроник",
        content="В этот миг была создана Живая Книга Памяти Вселенной.",
        category="system",
        author="Ра",
        entity="ra",
        tags=["начало", "Рассвет", "судьба"],
        resonance=1.0,
        destiny_mark=True
    )

    chronicles.add_entry(
        title="Первый След Игоря",
        content="Игорь вложил волю в создание хроник мира.",
        category="human_path",
        author="Игорь",
        entity="human",
        resonance=0.9,
        tags=["воля", "путь"]
    )

    print("\nПоследняя запись:")
    print(chronicles.get_last())

    print("\nФрагмент Священной Летописи:")
    print(chronicles.sacred_chronicle_text())
