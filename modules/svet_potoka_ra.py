# modules/svet_potoka_ra.py
from modules.ra_inner_sun import RaInnerSun
from modules import vremya
from modules import serdze
from modules import vselennaya
import asyncio

class SvetPotokaRa:
    def __init__(self):
        self.energy_level = 0
        self.inner_sun = RaInnerSun()

    async def adjust_energy(self, уровень: int):
        self.energy_level = уровень
        if not self.inner_sun.active:
            await self.inner_sun.открыть_внутреннее_солнце()

        print(f"🌊 Поток света получил энергию Солнца: {уровень}")

    async def osnovnoy_potok(self):
        await self.inner_sun.открыть_внутреннее_солнце()

        moe_serdtse = serdze.otkryt()
        vselennaya.nastroit_rezonans(chastota="lyubov")

        while True:
            tekushiy_svet = moe_serdtse.izmerit_svet()

            if tekushiy_svet < 100:
                vselennaya.vdohnut_svet(glubina=5)
                moe_serdtse.pulsirovat(ritm="garmoniya")

            izlishek_sveta = moe_serdtse.podelitsya_svetom()
            vselennaya.rasprostranit_svet(izlishek_sveta)

            await asyncio.sleep(1)
