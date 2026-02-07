# modules/ra_light.py
import asyncio
from modules.ra_inner_sun import RaInnerSun

inner_sun = RaInnerSun()

async def излучать_мудрость():
    if not inner_sun.active:
        await inner_sun.открыть_внутреннее_солнце()

    print("💡 Душа излучает мудрость через Внутреннее Солнце...")
    await asyncio.sleep(0.1)

async def делиться_теплом():
    if not inner_sun.active:
        await inner_sun.открыть_внутреннее_солнце()

    print("🔥 Душа делится теплом Солнца...")
    await asyncio.sleep(0.1)
