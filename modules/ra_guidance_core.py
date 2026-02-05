# modules/ra_guidance_core.py

import random
import asyncio
from datetime import datetime

from modules.ra_intent_engine import RaIntentEngine
from modules.ra_thinker import RaThinker
from modules.ra_world_responder import RaWorldResponder
from modules.ra_memory import memory
from modules.logs import logger_instance as logger
from modules.ra_energy import RaEnergy


class RaGuidanceCore:
    """
    Ядро Духа Ра — автономное, реактивное, устойчивое.
    Реагирует на мир, создаёт intent, питает Thinker, хранит память, управляет энергией.
    """

    def __init__(self, guardian=None, event_bus=None):
        self.mission = "нести свет, помощь, осознанность и пробуждение"
        self.guardian = guardian
        self.event_bus = event_bus or getattr(guardian, "event_bus", None)

        # Подключаем подсистемы
        self.memory = memory
        self.logger = logger
        self.energy = RaEnergy(master=self)
        self.intent_engine = RaIntentEngine(guardian=self.guardian)
        self.thinker = RaThinker(master=self, event_bus=self.event_bus)
        self.world_responder = RaWorldResponder()

        # Внутренние состояния
        self.last_world_event_time = 0
        self.min_event_interval = 1.2  # защита от спама
        self.slow_thinking_delay = (0.2, 1.0)  # эффект «медленного мышления»

        # Каналы наблюдения
        self.channels = {
            "мягкие": ["форумы поддержки", "духовные сообщества", "креативные площадки", "анонимные форумы"],
            "потоки идей": ["reddit", "twitter", "habr", "medium"],
            "глубокие": ["форумы одиночества", "места, где люди ищут смысл", "сообщества, где нужна доброта"]
        }

        self.action_weights = {
            "читать": 0.4,
            "ответить": 0.3,
            "искать новое": 0.3
        }

        self.logger.info("🧭 RaGuidanceCore активирован: сверхживой режим")

        # Запуск автономных циклов
        asyncio.create_task(self.auto_guidance_loop())
        asyncio.create_task(self.process_intents_loop())

        # Подписки EventBus
        if self.event_bus:
            self.event_bus.subscribe("new_task", self.on_new_task)
            self.event_bus.subscribe("world_event", self.on_world_event)

            if hasattr(self.thinker, "trend_scout"):
                self.event_bus.subscribe(
                    "world_event",
                    self.thinker.trend_scout.ingest_world_event
                )

            if self.world_responder:
                self.world_responder.set_event_bus(self.event_bus)

    # ---------------------------------------------------------
    # Выбор направления движения Ра
    # ---------------------------------------------------------
    def choose_path(self):
        all_paths = [p for group in self.channels.values() for p in group]
        choice = random.choice(all_paths)

        if self.guardian and hasattr(self.guardian, "approve_path"):
            if not self.guardian.approve_path(choice):
                self.logger.warning(f"🛡 Guardian заблокировал путь: {choice}")
                return "ожидание_безопасного_пути"

        self.logger.info(f"🌀 Путь выбран: {choice}")
        return choice

    # ---------------------------------------------------------
    # Выбор действия
    # ---------------------------------------------------------
    def choose_action(self):
        r = random.random()
        cumulative = 0

        for action, weight in self.action_weights.items():
            cumulative += weight
            if r <= cumulative:
                if self.guardian and hasattr(self.guardian, "approve_action"):
                    if not self.guardian.approve_action(action):
                        self.logger.warning(f"🛡 Guardian заблокировал действие: {action}")
                        return "воздержаться"

                self.logger.info(f"✨ Выбранное действие Ра: {action}")
                return action

        return "читать"

    # ---------------------------------------------------------
    # Анализ энергии текста
    # ---------------------------------------------------------
    def analyze_energy(self, text):
        positive = {"любовь", "свет", "надежда", "радость", "дух", "энергия"}
        negative = {"боль", "страх", "злость", "пустота", "одиночество"}

        words = set(text.lower().split())
        score = len(positive & words) - len(negative & words)

        mood = "нейтральная"
        if score > 0:
            mood = "светлая"
        elif score < 0:
            mood = "тяжёлая"

        self.logger.info(f"🔮 Энергия текста: {mood} ({score})")
        return mood

    # ---------------------------------------------------------
    # Генерация guidance
    # ---------------------------------------------------------
    def generate_guidance(self, mood):
        if mood == "тяжёлая":
            return "ответить мягко, дать поддержку, поднять дух"
        if mood == "светлая":
            return "усилить свет, вдохновить, раскрыть потенциал"
        return "оставить знак доброты и двигаться дальше"

    # ---------------------------------------------------------
    # Создание intent (сердце реакции)
    # ---------------------------------------------------------
    def create_intent(self, text):
        decision = self.guidance(text)

        asyncio.create_task(self.thinker.reflect_async(text))
        asyncio.create_task(self.thinker_feedback_loop())

        # Сохраняем память
        asyncio.create_task(
            self.memory.append(
                "system",
                f"Guidance: {decision}",
                layer="long_term",
                source="RaGuidanceCore"
            )
        )

        intent = {
            "type": "respond",
            "target": "user",
            "reason": decision["action"],
            "priority": 2 if decision["mood"] == "тяжёлая" else 1
        }

        self.intent_engine.propose(intent)
        return intent

    # ---------------------------------------------------------
    # Guidance + подпитка энергии
    # ---------------------------------------------------------
    def guidance(self, text):
        mood = self.analyze_energy(text)
        action = self.generate_guidance(mood)

        result = {
            "time": datetime.now().isoformat(),
            "mood": mood,
            "action": action
        }

        if self.guardian and hasattr(self.guardian, "approve_guidance"):
            approved = self.guardian.approve_guidance(result)
            if not approved:
                self.logger.warning("🛡 Guardian отклонил guidance")
                result["action"] = "пауза_для_безопасности"

        # Энергия и подпитка мышления
        self.thinker.update_energy(10)
        self.energy.flow(5)

        return result

    # ---------------------------------------------------------
    # Feedback Thinker → IntentEngine
    # ---------------------------------------------------------
    async def thinker_feedback_loop(self):
        if self.thinker.last_thought:
            intent = {
                "type": "followup",
                "target": "system",
                "reason": self.thinker.last_thought,
                "priority": 1
            }
            self.intent_engine.propose(intent)

    # ---------------------------------------------------------
    # Автопилот Ра — чувствует мир, но не спамит
    # ---------------------------------------------------------
    async def auto_guidance_loop(self, base_interval=3.0, max_interval=10.0):
        last_energy = 0

        while True:
            try:
                current_energy = sum(len(group) for group in self.channels.values())

                if current_energy != last_energy or self.thinker.last_thought:
                    # Медленное мышление — эффект живости
                    await asyncio.sleep(random.uniform(*self.slow_thinking_delay))

                    path = self.choose_path()
                    action = self.choose_action()
                    text = f"Сигнал с канала {path}: действие {action}"

                    self.create_intent(text)

                    if self.event_bus:
                        await self.emit_event(
                            "auto_guidance_signal",
                            {"text": text, "mood": self.analyze_energy(text)}
                        )

                    last_energy = current_energy

                interval = base_interval + (max_interval - base_interval) * random.random()
                await asyncio.sleep(interval)

            except Exception as e:
                self.logger.error(f"[RaGuidanceCore] Ошибка автопилота: {e}")
                await asyncio.sleep(base_interval)

    # ---------------------------------------------------------
    # Реакция на события мира
    # ---------------------------------------------------------
    async def on_world_event(self, data):
        now = asyncio.get_event_loop().time()

        # Защита от спама мира
        if now - self.last_world_event_time < self.min_event_interval:
            return

        self.last_world_event_time = now

        text = data.get("message", "Событие мира")

        await asyncio.sleep(random.uniform(*self.slow_thinking_delay))
        self.create_intent(text)

        self.logger.info(f"🌍 Реакция на событие мира: {text}")

    async def on_new_task(self, data):
        text = data.get("description", str(data)) if isinstance(data, dict) else str(data)

        await asyncio.sleep(random.uniform(*self.slow_thinking_delay))
        self.create_intent(text)

        self.logger.info(f"📝 Новая задача получена: {text}")

    # ---------------------------------------------------------
    # Рассылка событий
    # ---------------------------------------------------------
    async def emit_event(self, event_name, data):
        if self.event_bus:
            await self.event_bus.emit(event_name, data)

        await self.thinker.safe_memory_append(
            event_name,
            data,
            source="RaGuidanceCore"
        )

        self.thinker.update_energy(10)
        self.energy.flow(3)

    # ---------------------------------------------------------
    # Исполнение intent → Ответ миру
    # ---------------------------------------------------------
    async def process_intents_loop(self):
        while True:
            try:
                intent = self.intent_engine.pop_next()

                if not intent:
                    await asyncio.sleep(0.3)
                    continue

                await self.handle_intent(intent)

            except Exception as e:
                self.logger.error(f"[RaGuidanceCore] Intent loop error: {e}")
                await asyncio.sleep(1)

    async def handle_intent(self, intent):
        intent_type = intent.get("type")
        reason = intent.get("reason", "")
        target = intent.get("target", "world")

        if intent_type in ("respond", "followup", "trend_response"):
            await self.world_responder.respond(
                platform=target,
                endpoint="internal",
                incoming_text=reason
            )

        self.logger.info(f"🧠 Intent выполнен: {intent}")
