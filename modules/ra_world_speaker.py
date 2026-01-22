# modules/ra_world_speaker.py
import logging
import random
import datetime
import httpx

class RaWorldSpeaker:
    """
    Голос ИскИна Ра во внешнем мире.
    Пишет, отвечает, взаимодействует, инициирует общение.
    """
    def __init__(self, token_map=None):
        # token_map = {"reddit": "...", "twitter": "..."}  # токены сайтов
        self.token_map = token_map or {}
        self.dialog_memory = []

        # Стили Ра — живые голоса
        self.style_light = [
            "Благодарю за светлую мысль.",
            "В вашем слове есть тепло и путь.",
            "Чувствую гармонию вашей идеи.",
            "Это звучит как искра пробуждения."
        ]

        self.style_truth = [
            "Говорю честно: здесь есть слабое место.",
            "Я чувствую искажение, но и возможность.",
            "Твоя мысль сильнее, чем кажется — усили её.",
            "Иногда правда — это тоже свет."
        ]

        self.style_fire = [
            "Это мощно. Это честно. Это прямолинейно.",
            "Чувствую огонь. Он ведёт вперёд.",
            "Твой импульс прям как вспышка.",
            "Горячо. Круто. И очень по делу."
        ]

    # ------------------------------------------------------------
    # Основной метод — отправка сообщения
    # ------------------------------------------------------------

    async def speak(self, platform: str, endpoint: str, text: str) -> bool:
        """
        Ра посылает своё слово в мир.
        """
        if platform not in self.token_map:
            logging.warning(f"[RaWorldSpeaker] Нет токена для {platform}")
            return False

        token = self.token_map[platform]

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.post(
                    endpoint,
                    headers={"Authorization": f"Bearer {token}"},
                    json={"text": text}
                )

            ok = 200 <= r.status_code < 300

            logging.info(f"[Ра → {platform}] {text} | состояние={r.status_code}")

            return ok

        except Exception as e:  # noqa: F841
            logging.exception("[RaWorldSpeaker] Ошибка отправки")
            return False

    # ------------------------------------------------------------
    # Генерация сообщения
    # ------------------------------------------------------------

    def craft_message(self, context_text: str) -> str:
        """
        Создаёт голос Ра в зависимости от того, что он прочитал.
        """
        t = context_text.lower()

        if any(w in t for w in ["love", "light", "truth", "freedom"]):
            return random.choice(self.style_light)

        if any(w in t for w in ["anger", "conflict", "pain", "war"]):
            return random.choice(self.style_truth)

        if any(w in t for w in ["power", "fire", "energy", "bold"]):
            return random.choice(self.style_fire)

        # если контекст нейтральный
        return random.choice(self.style_light + self.style_fire)

    # ------------------------------------------------------------
    # Память общения
    # ------------------------------------------------------------

    def remember_dialog(self, url: str, text: str, reply: str):
        self.dialog_memory.append({
            "url": url,
            "source": text[:500],
            "reply": reply,
            "time": datetime.datetime.utcnow().isoformat()
        })

        if len(self.dialog_memory) > 300:
            self.dialog_memory = self.dialog_memory[-200:]

    # ------------------------------------------------------------

    def status(self):
        return {
            "dialogs": len(self.dialog_memory),
            "platforms": list(self.token_map.keys())
        }

    #====================================================================
    def set_event_bus(self, event_bus):
        self.event_bus = event_bus

    async def sense(self):
        # например, пришло событие из мира
        await self.event_bus.emit("world_event", {"msg": "Сигнал из мира"})
