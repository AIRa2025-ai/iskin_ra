import aiohttp
import asyncio
import json
import logging
from bs4 import BeautifulSoup

class RaExplorer:
    """
    Ра-Исследователь — изучает сайты, статьи, тексты, форумы.
    Сохраняет найденную информацию в память data/ra_journal.json.
    """

    def __init__(self, memory_path="data/ra_journal.json"):
        self.memory_path = memory_path

    async def explore_url(self, url: str, limit_chars: int = 2000) -> dict:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=15) as resp:
                    text = await resp.text()
            soup = BeautifulSoup(text, "html.parser")
            content = soup.get_text().strip().replace("\n", " ")[:limit_chars]
            record = {"url": url, "summary": content[:limit_chars]}
            await self._save_record(record)
            return record
        except Exception as e:
            logging.error(f"[RaExplorer] Ошибка при чтении {url}: {e}")
            return {"error": str(e)}

    async def _save_record(self, record: dict):
        try:
            data = []
            try:
                with open(self.memory_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except FileNotFoundError:
                pass
            data.append(record)
            with open(self.memory_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"[RaExplorer] Не удалось сохранить запись: {e}")
