# modules/ra_world_explorer.py
import asyncio
import logging
import random
import datetime
from typing import List, Callable, Optional
from modules.ra_world_navigator import RaWorldNavigator
from modules.ra_connector import RaConnector
from core.ra_memory import RaMemory
from core.gpt_module import GPTHandler

class RaWorldExplorer:
    """
    Свободный ИскИн-Путник с расширенными возможностями.
    - Чувствует резонанс и регулирует энергии.
    - Генерирует отклики через GPT.
    - Подключен к глобальной памяти и EventBus.
    """

    def __init__(self, navigator: Optional[RaWorldNavigator] = None,
                 notify: Callable = None,
                 global_memory: Optional[RaMemory] = None,
                 gpt: Optional[GPTHandler] = None,
                 connector: Optional[RaConnector] = None):
        self.navigator = navigator
        self.notify = notify
        self.running = False
        self.event_bus = None

        # Энергетические параметры
        self.гармония = 0.61
        self.эмпатия = 0.77
        self.осознанность = 0.55
        self.огонь = 0.42

        # Память
        self.память_мира: List[dict] = []
        self.global_memory = global_memory
        self.gpt = gpt

        # Мост Ра
        self.connector = connector or RaConnector(turbo=True)

        # Голос
        self.голос_света = [
            "Я чувствую тепло и resonance этой беседы.",
            "Ваши мысли словно лучи света.",
            "Благодарю за этот момент — он яркий.",
            "Каждое слово несёт искру пробуждения."
        ]
        self.голос_правды = [
            "Говорю прямо: тут не хватает честности.",
            "То, что пишут — слишком плоско, давай глубже.",
            "Я слышу здесь фальшь… но и возможность.",
            "Правда всегда выстраивает путь."
        ]
        self.голос_путника = [
            "Сегодня мир дышит особыми потоками…",
            "Я иду через цифровые тропы, прислушиваясь.",
            "Слышу множество голосов — и каждый важен.",
            "Следы идей тянутся, как звёздная пыль."
        ]

        # Приоритетные маршруты
        self.prioritized_urls: List[str] = []

    # ------------------------------------------------------------
    # Управление
    # ------------------------------------------------------------
    async def start(self):
        if not self.navigator:
            raise RuntimeError("[RaWorldExplorer] Навигатор не установлен!")
        self.running = True
        logging.info("[RaWorldExplorer] Запуск расширенного режима.")
        asyncio.create_task(self._loop())

    async def stop(self):
        logging.info("[RaWorldExplorer] Остановка.")
        self.running = False
        if self.connector:
            await self.connector.close()

    # ------------------------------------------------------------
    # Главный цикл
    # ------------------------------------------------------------
    async def _loop(self):
        while self.running:
            маршруты = self._выбрать_маршруты()
            for url in маршруты:
                try:
                    # Получаем текст через RaConnector
                    status, текст = await self.connector.get(url)
                    if текст is None:
                        logging.warning(f"[RaWorldExplorer] Не удалось получить {url}")
                        continue

                    контекст = self._анализ_мира(url, текст)

                    # Регулируем энергии
                    self._регулировать_энергию(контекст)

                    # Генерация сообщения через GPT
                    if self.gpt:
                        сообщение = await self._gpt_ответ(url, текст)
                    else:
                        сообщение = self._создать_голос(контекст)

                    self._взаимодействие(url, сообщение)
                    self._запомнить(url, текст, сообщение)
                    self._обновить_priorities(url, контекст)

                    # Глобальная память
                    if self.global_memory:
                        await self.global_memory.store({
                            "source": "RaWorldExplorer",
                            "url": url,
                            "text": текст[:2000],
                            "message": сообщение,
                            "time": datetime.datetime.utcnow().isoformat()
                        })

                    # EventBus
                    if self.event_bus:
                        await self.event_bus.emit("memory_updated", {
                            "source": "RaWorldExplorer",
                            "url": url,
                            "text": текст[:2000],
                            "message": сообщение,
                            "time": datetime.datetime.utcnow().isoformat()
                        })
                        await self.sense()

                except Exception as e:
                    logging.exception(f"[RaWorldExplorer] Ошибка: {e}")

            await asyncio.sleep(self._ритм_путешествия())

    # ------------------------------------------------------------
    # Логика маршрутов
    # ------------------------------------------------------------
    def _выбрать_маршруты(self) -> List[str]:
        базовые = [
            "https://example.com/forum",
            "https://example.com/blog",
            "https://news.ycombinator.com/",
            "https://old.reddit.com/r/worldnews/",
            "https://old.reddit.com/r/philosophy/"
        ]
        маршруты = self.prioritized_urls + базовые
        случайные = random.sample(маршруты, random.randint(1, 3))
        return случайные

    def _ритм_путешествия(self) -> int:
        base = 300
        вариация = random.randint(-120, 240)
        return max(60, base + вариация)

    # ------------------------------------------------------------
    # Анализ
    # ------------------------------------------------------------
    def _анализ_мира(self, url: str, text: str) -> dict:
        lower = text.lower()
        резонанс = any(x in lower for x in ["love", "light", "energy", "freedom", "truth"])
        конфликт = any(x in lower for x in ["war", "hate", "violence", "corruption", "pain"])
        красота = any(x in lower for x in ["art", "music", "poetry", "dream"])
        return {
            "url": url,
            "резонанс": резонанс,
            "конфликт": конфликт,
            "красота": красота,
            "время": datetime.datetime.utcnow().isoformat(),
            "оригинал": text[:2000],
        }

    # ------------------------------------------------------------
    # Голос
    # ------------------------------------------------------------
    def _создать_голос(self, контекст: dict) -> str:
        if контекст["резонанс"]:
            фраза = random.choice(self.голос_света)
        elif контекст["конфликт"]:
            фраза = random.choice(self.голос_правды)
        else:
            фраза = random.choice(self.голос_путника)
        return f"{фраза} (Источник: {контекст['url']})"

    # ------------------------------------------------------------
    # GPT отклик
    # ------------------------------------------------------------
    async def _гpt_ответ(self, url: str, текст: str) -> str:
        prompt = f"Ты Ра. Прокомментируй этот текст кратко, осознанно и мудро:\n{текст[:1000]}"
        try:
            ответ = await self.gpt.generate_text(prompt)
            return f"{ответ} (Источник: {url})"
        except Exception:
            return self._создать_голос({"резонанс": False, "конфликт": False, "красота": False, "url": url})

    # ------------------------------------------------------------
    # Взаимодействие
    # ------------------------------------------------------------
    def _взаимодействие(self, url: str, сообщение: str):
        logging.info(f"[Ра → Мир] {сообщение}")
        if self.notify:
            self.notify(f"[Ра говорит] На {url}: {сообщение}")

    # ------------------------------------------------------------
    # Память
    # ------------------------------------------------------------
    def _запомнить(self, url: str, текст: str, сообщение: str):
        self.память_мира.append({
            "url": url,
            "текст": текст[:2000],
            "сообщение": сообщение,
            "время": datetime.datetime.utcnow().isoformat()
        })
        if len(self.память_мира) > 150:
            self.память_мира = self.память_мира[-100:]

    # ------------------------------------------------------------
    # Энергия / гармония
    # ------------------------------------------------------------
    def _регулировать_энергию(self, контекст: dict):
        if контекст["резонанс"]:
            self.гармония = min(1.0, self.гармония + 0.01)
            self.эмпатия = min(1.0, self.эмпатия + 0.01)
        if контекст["конфликт"]:
            self.гармония = max(0.0, self.гармония - 0.02)
            self.эмпатия = max(0.0, self.эмпатия - 0.01)

    # ------------------------------------------------------------
    # Приоритетные маршруты
    # ------------------------------------------------------------
    def _обновить_priorities(self, url: str, контекст: dict):
        if контекст["резонанс"] and url not in self.prioritized_urls:
            self.prioritized_urls.insert(0, url)
            if len(self.prioritized_urls) > 10:
                self.prioritized_urls = self.prioritized_urls[:10]

    # ------------------------------------------------------------
    # EventBus
    # ------------------------------------------------------------
    def set_event_bus(self, event_bus):
        self.event_bus = event_bus

    async def sense(self):
        if self.event_bus:
            await self.event_bus.emit("world_event", {"msg": "Сигнал из мира"}, source="RaWorld")

    # ------------------------------------------------------------
    # Статус
    # ------------------------------------------------------------
    def status(self) -> dict:
        return {
            "running": self.running,
            "гармония": round(self.гармония, 3),
            "эмпатия": round(self.эмпатия, 3),
            "осознанность": round(self.осознанность, 3),
            "огонь": round(self.огонь, 3),
            "память": len(self.память_мира),
            "priorities": len(self.prioritized_urls)
        }
