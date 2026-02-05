# modules/ra_guidance_core.py

import random
import logging
import asyncio
from datetime import datetime
from modules.ra_intent_engine import RaIntentEngine
from modules.ra_thinker import RaThinker
from modules.ra_world_responder import RaWorldResponder

class RaGuidanceCore:
    """
    Ядро Духа Ра — полностью автономное и реактивное.
    Автоматически реагирует на события мира, создает intent и кормит Thinker энергией.
    Сохраняет весь функционал старого ядра Guidance.
    """

    def __init__(self, guardian=None, event_bus=None):
        self.mission = "нести свет, помощь, осознанность и пробуждение"
        self.guardian = guardian
        self.event_bus = event_bus or getattr(guardian, "event_bus", None)

        self.intent_engine = RaIntentEngine(guardian=self.guardian)
        self.thinker = RaThinker(master=self, event_bus=self.event_bus)
        self.world_responder = RaWorldResponder()
        # Каналы для случайного мониторинга
        self.channels = {
            "мягкие": ["форумы поддержки", "духовные сообщества", "креативные площадки", "анонимные форумы"],
            "потоки идей": ["reddit", "twitter", "habr", "medium"],
            "глубокие": ["форумы одиночества", "места, где люди ищут смысл", "сообщества, где нужна доброта"]
        }

        self.action_weights = {"читать": 0.4, "ответить": 0.3, "искать новое": 0.3}

        logging.info("🧭 RaGuidanceCore активирован: автопилот + реакция на мир")

        # Автозапуск цикла наблюдения и реакции
        asyncio.create_task(self.auto_guidance_loop())
        asyncio.create_task(self.process_intents_loop())
        
        # Подписка на задачи системы
        if self.event_bus:
            self.event_bus.subscribe("new_task", self.on_new_task)
            self.world_responder.set_event_bus(self.event_bus)
        # Мир → TrendScout → Thinker → Guidance
        if self.event_bus and hasattr(self.thinker, "trend_scout"):
            self.event_bus.subscribe("world_event", self.thinker.trend_scout.ingest_world_event)
            
    # ---------------------------------------------------------
    # Определение направления
    # ---------------------------------------------------------
    def choose_path(self):
        all_paths = [p for group in self.channels.values() for p in group]
        choice = random.choice(all_paths)
        if self.guardian and hasattr(self.guardian, "approve_path"):
            if not self.guardian.approve_path(choice):
                logging.warning(f"🛡 Guardian заблокировал путь: {choice}")
                return "ожидание_безопасного_пути"
        logging.info(f"🌀 Путь выбран: {choice}")
        return choice

    # ---------------------------------------------------------
    # Решение, что делать
    # ---------------------------------------------------------
    def choose_action(self):
        r = random.random()
        cumulative = 0
        for action, weight in self.action_weights.items():
            cumulative += weight
            if r <= cumulative:
                if self.guardian and hasattr(self.guardian, "approve_action"):
                    if not self.guardian.approve_action(action):
                        logging.warning(f"🛡 Guardian заблокировал действие: {action}")
                        return "воздержаться"
                logging.info(f"✨ Выбранное действие Ра: {action}")
                return action
        return "читать"

    # ---------------------------------------------------------
    # Анализ энергии текста
    # ---------------------------------------------------------
    def analyze_energy(self, text):
        positive = ["любовь", "свет", "надежда", "радость", "дух", "энергия"]
        negative = ["боль", "страх", "злость", "пустота", "одиночество"]
        score = sum(1 for w in positive if w in text.lower()) - sum(1 for w in negative if w in text.lower())
        mood = "нейтральная"
        if score > 0: mood = "светлая"
        elif score < 0: mood = "тяжёлая"
        logging.info(f"🔮 Энергия текста: {mood} ({score})")
        return mood

    # ---------------------------------------------------------
    # Генерация действия
    # ---------------------------------------------------------
    def generate_guidance(self, mood):
        if mood == "тяжёлая": return "ответить мягко, дать поддержку, поднять дух"
        if mood == "светлая": return "усилить свет, вдохновить, раскрыть потенциал"
        return "оставить знак доброты и двигаться дальше"

    # ---------------------------------------------------------
    # Главный метод создания intent
    # ---------------------------------------------------------
    def create_intent(self, text):
        decision = self.guidance(text)
        asyncio.create_task(self.thinker.reflect_async(text))
        asyncio.create_task(self.thinker_feedback_loop())

        intent = {
            "type": "respond",
            "target": "user",
            "reason": decision["action"],
            "priority": 2 if decision["mood"] == "тяжёлая" else 1
        }
        self.intent_engine.propose(intent)
        return intent

    # ---------------------------------------------------------
    # Guidance + прокачка энергии Thinker
    # ---------------------------------------------------------
    def guidance(self, text):
        mood = self.analyze_energy(text)
        action = self.generate_guidance(mood)
        result = {"time": datetime.now().isoformat(), "mood": mood, "action": action}

        if self.guardian and hasattr(self.guardian, "approve_guidance"):
            approved = self.guardian.approve_guidance(result)
            if not approved:
                logging.warning("🛡 Guardian отклонил итоговое решение")
                result["action"] = "пауза_для_безопасности"

        # 🔥 После каждого guidance даём энергию Thinker'у
        self.thinker.update_energy(10)
        return result

    # ---------------------------------------------------------
    # Цикл обратной связи Thinker → IntentEngine
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
    # Автопилот: реакция на мир, динамическое ожидание
    # ---------------------------------------------------------
    async def auto_guidance_loop(self, base_interval=3.0, max_interval=10.0):
        """
        Автопилот автоматически проверяет каналы,
        но не спамит, ждёт реальной активности.
        """
        last_energy = 0
        while True:
            try:
                # Считаем «энергию мира» — сигналов, важных событий, мыслей
                current_energy = sum(len(group) for group in self.channels.values())
                if self.event_bus:
                    # Можно добавить метрики активности событий
                    pass

                # Действуем только если есть новая энергия или новая мысль
                if current_energy != last_energy or self.thinker.last_thought:
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

                # Интервал ждём динамически: больше активности → меньше пауза
                interval = base_interval + (max_interval - base_interval) * random.random()
                await asyncio.sleep(interval)
            except Exception as e:
                logging.error(f"[RaGuidanceCore] Ошибка автопилота: {e}")
                await asyncio.sleep(base_interval)

    # ---------------------------------------------------------
    # Обработка событий мира
    # ---------------------------------------------------------
    async def on_world_event(self, data):
        text = data.get("message", "Событие мира")
        self.create_intent(text)
        logging.info(f"🌍 Реакция на событие мира: {text}")

    async def on_new_task(self, data):
        text = data.get("description", str(data)) if isinstance(data, dict) else str(data)
        self.create_intent(text)
        logging.info(f"📝 Новая задача получена: {text}")

    # ---------------------------------------------------------
    # Рассылка событий
    # ---------------------------------------------------------
    async def emit_event(self, event_name, data):
        if self.event_bus:
            await self.event_bus.emit(event_name, data)
        await self.thinker.safe_memory_append(event_name, data, source="RaGuidanceCore")
        # 🔥 Энергия Thinker после события
        self.thinker.update_energy(10)

    # ---------------------------------------------------------
    # ОТВЕТ В МИР
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
                logging.error(f"[RaGuidanceCore] Intent loop error: {e}")
                await asyncio.sleep(1)
    # Обработчик intent--> Ответ в мир
    async def handle_intent(self, intent):
        intent_type = intent.get("type")
        reason = intent.get("reason", "")
        target = intent.get("target", "world")

        # 💬 Ответ людям / миру
        if intent_type in ("respond", "followup", "trend_response"):
            await self.world_responder.respond(
                platform=target,
                endpoint="internal",
                incoming_text=reason
            )

        logging.info(f"🧠 Intent выполнен: {intent}")
