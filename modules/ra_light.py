# modules/ra_light.py

import asyncio
import logging
from datetime import datetime, timezone

from modules.ra_inner_sun import RaInnerSun


class RaLight:
    """
    Орган Света Ра.
    Излучает мудрость, тепло и поддерживает энергетическое поле.
    """

    def __init__(self, event_bus=None, intent_engine=None):
        self.inner_sun = RaInnerSun()
        self.event_bus = event_bus
        self.intent_engine = intent_engine

        self.active = True
        self.logger = logging.getLogger("RaLight")

    async def start(self):
        self.logger.info("💡 RaLight запущен — поток Света активирован")
        asyncio.create_task(self.light_loop())

    async def stop(self):
        self.active = False
        self.logger.info("🛑 RaLight остановлен")

    # -------------------------
    # Основной поток света
    # -------------------------
    async def light_loop(self):
        while self.active:
            try:
                await self.emit_wisdom()
                await self.share_warmth()
                await self.emit_intent()

            except Exception as e:
                self.logger.warning(f"[RaLight] Ошибка: {e}")

            await asyncio.sleep(5)

    # -------------------------
    # Световые функции
    # -------------------------
    async def ensure_inner_sun(self):
        if not self.inner_sun.active:
            await self.inner_sun.открыть_внутреннее_солнце()

    async def emit_wisdom(self):
        await self.ensure_inner_sun()
        print("💡 Душа излучает мудрость через Внутреннее Солнце...")
        await asyncio.sleep(0.1)

    async def share_warmth(self):
        await self.ensure_inner_sun()
        print("🔥 Душа делится теплом Солнца...")
        await asyncio.sleep(0.1)

    # -------------------------
    # Intent Engine — намерения
    # -------------------------
    async def emit_intent(self):
        if not self.intent_engine:
            return

        self.intent_engine.propose({
            "type": "light_flow",
            "source": "ra_light",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    # -------------------------
    # Реакции на события
    # -------------------------
    async def on_world_message(self, data):
        await self.emit_wisdom()

    async def on_heart_pulse(self):
        await self.share_warmth()

    async def on_harmony_signal(self, data):
        harmony = data.get("гармония", 0)
        if harmony < -40:
            await self.share_warmth()
        else:
            await self.emit_wisdom()
