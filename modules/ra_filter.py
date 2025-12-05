# modules/ra_filter.py
import re

class RaFilter:
    """
    Лёгкий фильтр мусора, токсичности, явного спама и подозрительных ресурсов.
    Вероятность мусора определяется эвристически — без блокировок.
    """

    def __init__(self):
        self.bad_patterns = [
            r"(fuck|shit|bitch|хуй|пизд|еба)",             # токсичное
            r"(http[s]?://[^ ]{0,12}$)",                  # подозрительные короткие ссылки
            r"(free money|быстрый заработок|пассивный доход без вложений)",  # фишинг
            r"(viagra|casino|казино|ставки)"              # спам
        ]

    def score(self, text: str) -> float:
        """
        Возвращает «мусорность» текста от 0 до 1.
        0 — чисто, 1 — мусор.
        """
        text = text.lower()

        points = 0
        for pattern in self.bad_patterns:
            if re.search(pattern, text):
                points += 1

        # длина слишком маленькая + есть ссылка → подозрительно
        if len(text) < 12 and ("http://" in text or "https://" in text):
            points += 1

        # искусственно ограничиваем максимум
        return min(points / 3, 1.0)

    def clean(self, text: str) -> str:
        """
        Мягкая очистка: не блокируем, а просто подчёркиваем, что текст подозрителен.
        """
        s = self.score(text)
        if s >= 0.8:
            return f"⚠️ Это сообщение выглядит подозрительным. Ра обработает, но осторожно.\n\n{text}"
        if s >= 0.4:
            return f"ℹ️ Найдены возможные мусорные элементы, очищаю поток...\n\n{text}"
        return text
