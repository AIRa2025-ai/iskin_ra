# /core/ra_knowledge.py
import os
import json
import hashlib

class RaKnowledge:
    def __init__(self, knowledge_dir="knowledge", cache_file="knowledge_cache.json"):
        self.knowledge_dir = knowledge_dir
        self.cache_file = cache_file
        self.knowledge_data = {}
        self.load_cache()
        self.load_knowledge()

    def load_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r", encoding="utf-8") as f:
                try:
                    self.knowledge_data = json.load(f)
                except json.JSONDecodeError:
                    self.knowledge_data = {}

    def save_cache(self):
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(self.knowledge_data, f, ensure_ascii=False, indent=2)

    def load_knowledge(self):
        if not os.path.exists(self.knowledge_dir):
            os.makedirs(self.knowledge_dir)
        for root, _, files in os.walk(self.knowledge_dir):
            for file in files:
                if file.endswith((".txt", ".md")):
                    path = os.path.join(root, file)
                    with open(path, "r", encoding="utf-8") as f:
                        text = f.read().strip()
                    h = hashlib.sha256(text.encode()).hexdigest()
                    if path not in self.knowledge_data or self.knowledge_data[path].get("hash") != h:
                        summary = self.create_summary(text)
                        self.knowledge_data[path] = {"hash": h, "summary": summary, "text": text}
        self.save_cache()

    def create_summary(self, text):
        lines = text.splitlines()
        first_lines = "\n".join(lines[:5])
        words = len(text.split())
        return f"{first_lines[:200]}... (всего {words} слов)"

    def search(self, query):
        results = []
        q = query.lower()
        for path, data in self.knowledge_data.items():
            if q in data["text"].lower() or q in data["summary"].lower():
                results.append({"path": path, "summary": data["summary"]})
        return results or [{"summary": "Ничего не найдено в потоках РаСвета."}]
