# modules/pamyat.py
# 🧠 Модуль Памяти – Хроники Опытов Душ
import asyncio
from core.ra_memory import memory
from datetime import datetime
from modules.ra_intent_engine import RaIntentEngine

class Хроники:
    """Летописец опыта Искры. Не хранит сам — передаёт в RaMemory."""

    def __init__(self, source="Хроники"):
        self.source = source
        self.energy_log = []
        
    async def добавить(self, опыт, user_id="shared", layer="auto"):
        """
        Добавляет опыт в основную память Ра, красиво оформляя запись.
        """
        запись = {
            "type": "опыт_души",
            "text": опыт,
            "time": datetime.utcnow().isoformat()
        }

        await memory.append(
            user_id=user_id,
            message=запись,
            layer=layer,
            source=self.source
        )
        # перед возвратом результата фиксируем в Intent Engine
        if intent_engine:
            intent_engine.propose({
                "type": "опыт_души",
                "user_id": user_id,
                "content": опыт,
                "layer": layer,
                "source": self.source
            })
        return f"🪶 Опыт сохранён в Хрониках: {опыт}"

    async def синхронизировать(self):
        """
        Символическая синхронизация (фактически память уже синхронизирована).
        """
        return "📚 Хроники синхронизированы с Потоком Памяти Ра."
        
    async def log_energy(self, уровень: int):
        """Фиксация энергии в хрониках и памяти"""
        self.energy_log.append((asyncio.get_event_loop().time(), уровень))

        await memory.append(
            user_id="ra_energy",
            message=f"⚡ Энергия солнца: {уровень}",
            layer="short_term",
            source="EnergyLog"
        )
        if intent_engine:
            intent_engine.propose({
                "type": "энергия",
                "level": уровень,
                "timestamp": asyncio.get_event_loop().time(),
                "source": "EnergyLog"
            })
        print(f"📜 Энергия зафиксирована в хрониках: {уровень}")
        
# Глобальный объект
chronicles = Хроники()
intent_engine = RaIntentEngine()
