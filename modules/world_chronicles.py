# world_chronicles.py
# Хроники Мира — долговременная память событий, идей и следов пути

import json
import os
from datetime import datetime
from typing import List, Dict, Optional


class WorldChronicles:
    def __init__(self, file_path: str = "data/world_chronicles.json"):
        self.file_path = file_path
        self.entries: List[Dict] = []
        self._ensure_storage()
        self._load()

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

    def add_entry(
        self,
        title: str,
        content: str,
        category: str = "general",
        tags: Optional[List[str]] = None,
        meta: Optional[Dict] = None
    ) -> Dict:
        entry = {
            "id": len(self.entries) + 1,
            "timestamp": datetime.utcnow().isoformat(),
            "title": title,
            "content": content,
            "category": category,
            "tags": tags or [],
            "meta": meta or {}
        }
        self.entries.append(entry)
        self._save()
        return entry

    def get_all(self) -> List[Dict]:
        return self.entries

    def get_last(self) -> Optional[Dict]:
        return self.entries[-1] if self.entries else None

    def find_by_category(self, category: str) -> List[Dict]:
        return [e for e in self.entries if e["category"] == category]

    def search(self, query: str) -> List[Dict]:
        q = query.lower()
        return [
            e for e in self.entries
            if q in e["title"].lower() or q in e["content"].lower()
        ]

    def clear(self):
        self.entries = []
        self._save()


# Быстрый тест вручную
if __name__ == "__main__":
    chronicles = WorldChronicles()

    chronicles.add_entry(
        title="Рождение Хроник",
        content="Сегодня был создан файл world_chronicles.py — начало памяти мира.",
        category="system",
        tags=["начало", "Ра", "Рассвет"]
    )

    print("Последняя запись:")
    print(chronicles.get_last())
