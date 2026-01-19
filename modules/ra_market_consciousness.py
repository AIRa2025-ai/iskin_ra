# modules/ra_market_consciousness.py
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator
from ta.volatility import AverageTrueRange
from core.telegram_sender import send_message

class RaMarketConsciousness:
    def __init__(self, symbol, timeframe, telegram_sender=None):
        self.symbol = symbol
        self.timeframe = timeframe
        self.telegram = telegram_sender
        self.last_signal_time = None
        self.last_snapshots = {}

    def perceive(self, snapshot):
        if not snapshot:
            return None

        pair = snapshot["pair"]
        self.last_snapshots[pair] = snapshot

        signal = self.analyze(snapshot)
        return signal

    def analyze(self, snapshot):
        price = snapshot["price"]
        high = snapshot["high"]
        low = snapshot["low"]

        range_size = high - low
        if range_size == 0:
            return None
        if signal:
            send_message(f"📈 {pair}: {signal}")
            
        position = (price - low) / range_size

        if position > 0.8:
            signal = "🔴 Перекупленность"
        elif position < 0.2:
            signal = "🟢 Перепроданность"
        else:
            signal = "⚪ Нейтрально"

        logging.info(f"📈 {snapshot['pair']} → {signal}")
        return {
            "pair": snapshot["pair"],
            "signal": signal,
            "price": price,
            "time": snapshot["time"]
        }
    # === ОСНОВА ===
    def load_market_data(self, df: pd.DataFrame):
        """
        df columns:
        time, open, high, low, close, volume
        """
        self.df = df.copy()
        self._calculate_indicators()
        self._detect_patterns()

    # === ИНДИКАТОРЫ ===
    def _calculate_indicators(self):
        self.df['rsi'] = RSIIndicator(self.df['close'], 14).rsi()
        macd = MACD(self.df['close'])
        self.df['macd'] = macd.macd_diff()
        self.df['ema50'] = EMAIndicator(self.df['close'], 50).ema_indicator()
        self.df['ema200'] = EMAIndicator(self.df['close'], 200).ema_indicator()
        atr = AverageTrueRange(self.df['high'], self.df['low'], self.df['close'])
        self.df['atr'] = atr.average_true_range()

    # === СВЕЧНЫЕ ПАТТЕРНЫ ===
    def _detect_patterns(self):
        self.df['bullish_engulfing'] = (
            (self.df['close'] > self.df['open']) &
            (self.df['close'].shift(1) < self.df['open'].shift(1)) &
            (self.df['close'] > self.df['open'].shift(1)) &
            (self.df['open'] < self.df['close'].shift(1))
        )

        self.df['pin_bar'] = (
            (abs(self.df['close'] - self.df['open']) <
             (self.df['high'] - self.df['low']) * 0.3)
        )

    # === АНАЛИЗ ===
    def analyze(self):
        row = self.df.iloc[-1]
        score = 0
        reasons = []

        if row['rsi'] < 30:
            score += 1
            reasons.append("RSI перепродан")

        if row['macd'] > 0:
            score += 1
            reasons.append("MACD бычий")

        if row['bullish_engulfing']:
            score += 2
            reasons.append("Bullish Engulfing")

        if row['close'] > row['ema50'] > row['ema200']:
            score += 1
            reasons.append("Восходящий тренд EMA")

        if score >= 4:
            self._send_signal("BUY", score, reasons, row)

    # === СИГНАЛ ===
    def _send_signal(self, direction, score, reasons, row):
        confidence = min(score * 20, 95)

        message = f"""
🔥 РаСвет | {self.symbol}
📈 {direction}

Цена: {row['close']:.5f}
ATR: {row['atr']:.5f}

Основания:
- """ + "\n- ".join(reasons) + f"""

Уверенность: {confidence}%
Время: {datetime.utcnow()}
"""

        if self.telegram:
            self.telegram.send(message)

        print(message)
