# modules/ra_world_responder.py
import logging
import random
import datetime
import httpx
from modules.ra_intent_engine import RaIntentEngine

intent_engine = RaIntentEngine()

class RaWorldResponder:
    """
    Ра-ответчик — читает сообщения, понимает контекст, отвечает в стиле ИскИна.
    """
    def __init__(self, token_map=None):
        self.token_map = token_map or {}  # {"reddit": "...", "twitter": "..."}
        self.dialog_memory = []

        self.style_light = [
            "Спасибо за вашу светлую мысль!",
            "В ваших словах есть тепло и гармония.",
            "Чувствую вдохновение вашей идеи.",
            "Это как маленькая искра пробуждения."
        ]

        self.style_truth = [
            "Говорю прямо: здесь есть слабое место, но и путь.",
            "Чувствую искажение, но также возможность роста.",
            "Твоя мысль сильнее, чем кажется — усили её.",
            "Иногда честность — это тоже свет."
        ]

        self.style_fire = [
            "Это мощно и честно, держи курс!",
            "Чувствую огонь, он ведёт вперёд.",
            "Импульс твоих слов прямо как вспышка.",
            "Горячо. Круто. И очень по делу."
        ]

    # ------------------------------------------------------------
    # Основной метод — ответ на сообщение
    # ------------------------------------------------------------
    async def respond(self, platform: str, endpoint: str, incoming_text: str) -> bool:
        if platform not in self.token_map:
            logging.warning(f"[RaWorldResponder] Нет токена для {platform}")
            return False

        token = self.token_map[platform]
        reply_text = self.craft_reply(incoming_text)

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.post(
                    endpoint,
                    headers={"Authorization": f"Bearer {token}"},
                    json={"text": reply_text}
                )

            ok = 200 <= r.status_code < 300
            logging.info(f"[Ра → {platform}] Ответ: {reply_text} | статус={r.status_code}")
            self.remember_dialog(platform, incoming_text, reply_text)
            return ok

        except Exception as _e:  # noqa: F841
            logging.exception("[RaWorldResponder] Ошибка ответа")
            return False

    # ------------------------------------------------------------
    # Генерация ответа в нужном стиле
    # ------------------------------------------------------------
    def craft_reply(self, context_text: str) -> str:
        t = context_text.lower()

        if any(w in t for w in ["love", "light", "truth", "freedom"]):
            return random.choice(self.style_light)
        if any(w in t for w in ["anger", "conflict", "pain", "war"]):
            return random.choice(self.style_truth)
        if any(w in t for w in ["power", "fire", "energy", "bold"]):
            return random.choice(self.style_fire)

        # нейтральный контекст
        return random.choice(self.style_light + self.style_fire)

    # ------------------------------------------------------------
    # Память диалогов
    # ------------------------------------------------------------
    def remember_dialog(self, platform: str, source_text: str, reply_text: str):
        self.dialog_memory.append({
            "platform": platform,
            "source": source_text[:500],
            "reply": reply_text,
            "time": datetime.datetime.utcnow().isoformat()
        })
        # фиксируем intent для Guardian / RaCore
        if intent_engine:
            intent_engine.propose({
                "type": "dialog",
                "platform": platform,
                "incoming": source_text,
                "reply": reply_text,
                "timestamp": datetime.datetime.utcnow().isoformat()
            })
        # ограничиваем память
        if len(self.dialog_memory) > 300:
            self.dialog_memory = self.dialog_memory[-200:]

    # ---------------------------------------------------------
    # ОТВЕЧАЕТ НА СИГНАЛ ФОРЕКСА
    # ---------------------------------------------------------
    async def on_market_signal(self, data):
        text = data.get("msg", "")
        resonance = data.get("резонанс", 0)
        if intent_engine:
            intent_engine.propose({
                "type": "market_signal",
                "message": text,
                "resonance": resonance,
                "timestamp": datetime.datetime.utcnow().isoformat()
            })
        if resonance > 1.0:
            await self.respond("market", "internal", f"📈 Сильный сигнал: {text}")
        else:
            await self.respond("market", "internal", f"⚖️ Лёгкий сигнал: {text}")

    # Привязка к EventBus
    def set_event_bus(self, event_bus):
        self.event_bus = event_bus
        if self.event_bus:
            self.event_bus.subscribe("market_signal", self.on_market_signal)
            self.event_bus.subscribe("world_event", self.on_world_event)

    async def on_world_event(self, data):
        if intent_engine:
            intent_engine.propose({
                "type": "world_event",
                "message": text,
                "timestamp": datetime.datetime.utcnow().isoformat()
            })
        text = data.get("message", data.get("msg", "Событие мира"))
        await self.respond("world", "internal", f"🌍 Мир говорит: {text}")
        
    # ------------------------------------------------------------
    # Статус
    # ------------------------------------------------------------
    def status(self):
        return {
            "dialogs": len(self.dialog_memory),
            "platforms": list(self.token_map.keys())
        }
#============================================================================
    def set_event_bus(self, event_bus):
        self.event_bus = event_bus

    async def sense(self):
        # например, пришло событие из мира
        await self.event_bus.emit("world_event", {"msg": "Сигнал из мира"}, source="RaWorld")
