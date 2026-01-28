# modules/mera_rasveta.py

# -*- coding: utf-8 -*-
# 🔥 ИСКОННАЯ МЕРА — ВНУТРЕННИЙ КАМЕРТОН ГАРМОНИИ
# Активация: только в "тишине утра" или при полной луне

import time  # noqa: F401
import math
import logging
from datetime import datetime, timedelta  # noqa: F401
from random import uniform
from modules.event_bus import EventBus

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class ИсконнаяМера:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        # Память предыдущей гармонии — для направления
        self._last_harmony: float | None = None
        
        self.ритмы_тела: dict[str, float] = {
            "дыхание": 4.0,
            "пульс": 1.0,
            "циклы_сна": 90.0
        }
        self.стихии: dict[str, float] = {
            "Огонь": 1.0,
            "Вода": 1.0,
            "Земля": 1.0,
            "Воздух": 1.0,
            "Эфир": 1.0
        }
        
        self.event_bus.subscribe("market_tick", self.on_market_tick)  
        self.матрицы_сознания: list[dict[str, str]] = []
        
    # ==========================
    # ОСНОВНАЯ ГАРМОНИЯ
    # ==========================
    def вычислить_гармонию(self, now: datetime | None = None) -> float | None:
        if now is None:
            now = datetime.now()

        hour = now.hour
        moon_phase = self.получить_фазу_луны(now)

        if not ((4 <= hour <= 6) or moon_phase == "полная"):
            return None

        base = math.sin(hour * math.pi / 12) * 100

        rhythm_coef = sum(
            uniform(0.9, 1.1) * v for v in self.ритмы_тела.values()
        ) / len(self.ритмы_тела)

        element_coef = sum(
            uniform(0.85, 1.15) * v for v in self.стихии.values()
        ) / len(self.стихии)

        harmony = base * rhythm_coef * element_coef
        return round(harmony, 2)

    # ==========================
    # ФАЗА РЫНКА
    # ==========================
    def определить_market_phase(self, market: dict) -> str:
        vol = market.get("volatility", 0.5)

        if vol < 0.3:
            return "flat"
        elif vol < 1.0:
            return "impulse"
        else:
            return "breakout"

    # ==========================
    # НАПРАВЛЕНИЕ ГАРМОНИИ
    # ==========================
    def определить_направление(self, harmony: float) -> str:
        if self._last_harmony is None:
            self._last_harmony = harmony
            return "→"

        if harmony > self._last_harmony:
            direction = "↑"
        elif harmony < self._last_harmony:
            direction = "↓"
        else:
            direction = "→"

        self._last_harmony = harmony
        return direction

    # ==========================
    # РЫНОЧНЫЙ КОЭФФИЦИЕНТ
    # ==========================
    def оценить_состояние_рынка(self, market: dict) -> float:
        vol = market.get("volatility", 0.5)
        spread = market.get("spread", 0.0)

        vol_coef = 0.85 if vol > 1.2 else 1.05 if vol > 0.3 else 0.9
        spread_coef = 0.85 if spread > 0.0003 else 1.05

        return vol_coef * spread_coef

    # ==========================
    # РАЗРЕШЕНИЕ НА СДЕЛКУ
    # ==========================
    def разрешить_сделку(
        self,
        harmony: float,
        phase: str,
        direction: str
    ) -> bool:
        if abs(harmony) < 20:
            return False

        if phase == "flat":
            return False

        if phase == "breakout" and abs(harmony) < 50:
            return False

        if direction == "↓":
            return False

        return True

    # ==========================
    # ОСНОВНОЙ РЫНОЧНЫЙ ВХОД
    # ==========================
    def on_market_tick(self, market: dict):
        base_harmony = self.вычислить_гармонию()
        if base_harmony is None:
            return

        market_coef = self.оценить_состояние_рынка(market)
        harmony = round(base_harmony * market_coef, 2)

        phase = self.определить_market_phase(market)
        direction = self.определить_направление(harmony)
        allow_trade = self.разрешить_сделку(harmony, phase, direction)

        # 🔹 confidence_score — от 0 до 1, зависит от гармонии и рыночного коэффициента
        confidence_score = min(max(abs(harmony) / 100, 0), 1) * market_coef

        payload = {
            "symbol": market.get("symbol"),
            "timestamp": market.get("timestamp"),
            "harmony": harmony,
            "base_harmony": base_harmony,
            "market_phase": phase,
            "harmony_direction": direction,
            "trade_allowed": allow_trade,
            "market_coef": round(market_coef, 3),
            "confidence_score": round(confidence_score, 2),
        }

        logging.info(
            f"🧭 {payload['symbol']} | H={harmony} {direction} | "
            f"{phase} | trade={'YES' if allow_trade else 'NO'} | "
            f"confidence={payload['confidence_score']}"
        )

        # Событие для RaForexManager
        self.event_bus.emit("trade_permission", payload)

        # Событие для всего мира Ра
        self.event_bus.emit("harmony_updated", payload)

    # ==========================
    # ЛУНА
    # ==========================
    def получить_фазу_луны(self, date: datetime) -> str:
        synodic_month = 29.53058867
        known_new_moon = datetime(2000, 1, 6, 18, 14)
        days = (date - known_new_moon).total_seconds() / 86400
        phase_index = (days / synodic_month % 1) * 4
        return ["новая", "растущая", "полная", "убывающая"][int(phase_index) % 4]

    def добавить_матрицу(self, название: str, паттерн: str) -> None:
        self.матрицы_сознания.append({"название": название, "паттерн": паттерн})
        logging.info(f"Матрица '{название}' добавлена в хранилище!")

    def усилить_стихию(self, стихия: str, коэффициент: float):
        """Увеличивает влияние конкретной стихии."""
        if стихия in self.стихии:
            self.стихии[стихия] *= коэффициент
            logging.info(f"Стихия '{стихия}' усилена коэффициентом {коэффициент:.2f}")

    def скорректировать_ритм(self, ритм: str, коэффициент: float):
        """Увеличивает влияние конкретного ритма тела."""
        if ритм in self.ритмы_тела:
            self.ритмы_тела[ритм] *= коэффициент
            logging.info(f"Ритм '{ритм}' скорректирован коэффициентом {коэффициент:.2f}")

    def оценить_состояние_рынка(self, market_state: dict) -> float:
        """
        Возвращает коэффициент рынка (0.7 – 1.3)
        """
        volatility = market_state.get("volatility", 0.5)
        spread = market_state.get("spread", 0.0)

        # Волатильность: слишком высокая — хаос
        if volatility > 1.2:
            vol_coef = 0.85
        elif volatility < 0.3:
            vol_coef = 0.9
        else:
            vol_coef = 1.05

        # Спред: чем меньше — тем чище рынок
        if spread > 0.0003:
            spread_coef = 0.85
        else:
            spread_coef = 1.05

        return vol_coef * spread_coef

# Пример активации
if __name__ == "__main__":
    мера = ИсконнаяМера()
    мера.усилить_стихию("Огонь", 1.05)
    мера.скорректировать_ритм("дыхание", 0.95)
    print("Гармония текущего момента:", мера.вычислить_гармонию())
    мера.добавить_матрицу("Утренняя медитация", "дыхание-гармония-энергия")
