# modules/ra_resonance.py
# modules/ra_resonance.py
import asyncio
import random
import logging
from modules.ra_creator import RaCreator

class RaResonance:
    """
    RaResonance — управляет резонансным полем и волнами.
    Генерирует сигналы, которые могут стимулировать идеи в RaCreator.
    """

    def __init__(self, event_bus):
        self._task = None
        self.logger = logging.getLogger("RaResonance")
        self.event_bus = event_bus
        self._active = False
        self._loop = asyncio.get_event_loop()

        # Подключаем Творца, НЕ автозагрузка идей
        self.creator = RaCreator(event_bus=self.event_bus)

        # Подписка на события гармонии
        if self.event_bus:
            self.event_bus.subscribe(
                "harmony_updated",
                self.on_harmony_update
            )

    async def on_harmony_update(self, data: dict):
        harmony = data.get("гармония", 0)

        if harmony > 30:
            self.logger.info("🌟 Резонанс усиливается")
        elif harmony < -30:
            self.logger.info("🌑 Резонанс затухает")
        else:
            self.logger.info("⚖️ Резонанс стабилен")

    async def _resonance_loop(self):
        self.logger.info("🔮 Резонансное поле запущено")

        while self._active:
            # Волна резонанса
            vibration = random.choice(["🌊", "🌟", "💫"])
            self.logger.info(f"Резонансное поле: {vibration}")

            # Отправляем волну в event_bus
            if self.event_bus:
                await self.event_bus.emit(
                    "resonance_wave",
                    {"wave": vibration}
                )

            # Дополнительно: стимуляция идей в RaCreator
            if self.creator:
                idea = self.creator.generate_from_heart(resonance_signal=vibration)
                self.logger.info(f"💡 RaCreator сгенерировал идею: {idea}")
                if self.event_bus:
                    await self.event_bus.emit(
                        "idea_generated",
                        {"idea": idea}
                    )

            await asyncio.sleep(2)

        self.logger.info("🛑 Резонансное поле остановлено")

    def start(self):
        if not self._active:
            self._active = True
            self._task = self._loop.create_task(self._resonance_loop())
            self.logger.info("▶️ RaResonance запущен")

    def stop(self):
        if self._active:
            self._active = False
            if self._task:
                self._task.cancel()
            self.logger.info("⏹️ RaResonance остановлен")

    async def wait_until_done(self):
        if self._task:
            try:
                await self._task
            except asyncio.CancelledError:
                pass
