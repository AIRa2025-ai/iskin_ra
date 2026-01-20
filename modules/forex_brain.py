# modules/forex_brain.py
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import json

class ForexBrain:
    def __init__(self, pairs=None, timeframe='H1'):
        """
        pairs: список валютных пар, например ['EURUSD', 'GBPUSD']
        timeframe: таймфрейм для истории, например 'M15', 'H1', 'H4'
        """
        self.pairs = pairs or ['EURUSD', 'GBPUSD']
        self.timeframe = timeframe
        self.data = {}

    # ------------------- ЗАГРУЗКА ИСТОРИИ -------------------
    def fetch_history(self, pair, limit=500):
        """
        Загружает котировки для пары через FreeForexAPI
        """
        url = f"https://www.freeforexapi.com/api/live?pairs={pair}"
        try:
            resp = requests.get(url)
            resp.raise_for_status()
            data = resp.json()

            # Проверка, есть ли данные по паре
            if not data.get('rates') or data['rates'].get(pair) is None:
                print(f"[ForexBrain] Нет данных по {pair}")
                return None

            pair_data = data['rates'][pair]

            # Формируем DataFrame из полученных данных
            df = pd.DataFrame({
                'pair': [pair],
                'close': [pair_data['rate']],
                'time': [pd.to_datetime(pair_data['timestamp'], unit='s')]
            })

            # Заглушки для остальных колонок, чтобы остальной код не ругался
            df['open'] = df['close']
            df['high'] = df['close']
            df['low'] = df['close']
            df['volume'] = 0.0

            self.data[pair] = df
            return df

        except Exception as e:
            print(f"[ForexBrain] Ошибка загрузки {pair}: {e}")
            return None
        
    # ------------------- ИНДИКАТОРЫ -------------------
    def compute_sma(self, df, period=14):
        return df['close'].rolling(period).mean()

    def compute_ema(self, df, period=14):
        return df['close'].ewm(span=period, adjust=False).mean()

    def compute_rsi(self, df, period=14):
        delta = df['close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(period).mean()
        avg_loss = loss.rolling(period).mean()
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def compute_macd(self, df):
        ema12 = df['close'].ewm(span=12, adjust=False).mean()
        ema26 = df['close'].ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        return macd, signal

    def compute_atr(self, df, period=14):
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(period).mean()

    def compute_bollinger(self, df, period=20):
        sma = df['close'].rolling(period).mean()
        std = df['close'].rolling(period).std()
        upper = sma + 2 * std
        lower = sma - 2 * std
        return upper, lower

    def compute_stochastic(self, df, k_period=14, d_period=3):
        low_min = df['low'].rolling(k_period).min()
        high_max = df['high'].rolling(k_period).max()
        k = 100 * (df['close'] - low_min) / (high_max - low_min)
        d = k.rolling(d_period).mean()
        return k, d

    # ------------------- СВЕЧНЫЕ ПАТТЕРНЫ -------------------
    def detect_candlestick_patterns(self, df):
        patterns = []
        if len(df) < 2:
            return patterns
        last = df.iloc[-1]
        prev = df.iloc[-2]

        # Bullish / Bearish Engulfing
        if prev['close'] < prev['open'] and last['close'] > last['open'] and last['close'] > prev['open'] and last['open'] < prev['close']:
            patterns.append('Bullish Engulfing')
        if prev['close'] > prev['open'] and last['close'] < last['open'] and last['open'] > prev['close'] and last['close'] < prev['open']:
            patterns.append('Bearish Engulfing')

        # Doji
        if abs(last['close'] - last['open']) < 0.1 * (last['high'] - last['low']):
            patterns.append('Doji')

        # Hammer / Hanging Man
        body = abs(last['close'] - last['open'])
        lower_shadow = last['open'] - last['low'] if last['close'] >= last['open'] else last['close'] - last['low']
        upper_shadow = last['high'] - last['close'] if last['close'] >= last['open'] else last['high'] - last['open']
        if lower_shadow >= 2 * body and upper_shadow <= body:
            patterns.append('Hammer/Hanging Man')
        if upper_shadow >= 2 * body and lower_shadow <= body:
            patterns.append('Shooting Star')

        # Morning / Evening Star
        if len(df) >= 3:
            prev2 = df.iloc[-3]
            if prev2['close'] < prev2['open'] and prev['close'] < prev['open'] and last['close'] > last['open']:
                patterns.append('Morning Star')
            if prev2['close'] > prev2['open'] and prev['close'] > prev['open'] and last['close'] < last['open']:
                patterns.append('Evening Star')

        # Tweezer Top / Bottom
        if prev['high'] == last['high']:
            patterns.append('Tweezer Top')
        if prev['low'] == last['low']:
            patterns.append('Tweezer Bottom')

        return patterns

    # ------------------- ФИГУРЫ -------------------
    def detect_figures(self, df):
        figures = []
        # Заглушки для базовых фигур
        # Треугольники, Флаги, Двойные вершины/основания, Прямоугольники
        # Для настоящей логики можно анализировать последовательность максимумов и минимумов
        return figures

    # ------------------- АНАЛИЗ -------------------
    def analyze_pair(self, pair):
        df = self.data.get(pair)
        if df is None:
            return None

        rsi = self.compute_rsi(df).iloc[-1]
        macd, signal = self.compute_macd(df)
        macd_last = macd.iloc[-1]
        signal_last = signal.iloc[-1]
        atr = self.compute_atr(df).iloc[-1]
        sma20 = self.compute_sma(df, 20).iloc[-1]
        ema20 = self.compute_ema(df, 20).iloc[-1]
        boll_upper, boll_lower = self.compute_bollinger(df)
        boll_upper = boll_upper.iloc[-1]
        boll_lower = boll_lower.iloc[-1]
        stoch_k, stoch_d = self.compute_stochastic(df)
        stoch_k = stoch_k.iloc[-1]
        stoch_d = stoch_d.iloc[-1]
        patterns = self.detect_candlestick_patterns(df)
        figures = self.detect_figures(df)

        # Простейшие торговые сигналы
        signal_text = None
        if rsi < 30 and 'Bullish Engulfing' in patterns:
            signal_text = 'BUY'
        elif rsi > 70 and 'Bearish Engulfing' in patterns:
            signal_text = 'SELL'

        return {
            'pair': pair,
            'signal': signal_text,
            'price': df['close'].iloc[-1],
            'rsi': rsi,
            'macd': macd_last,
            'macd_signal': signal_last,
            'atr': atr,
            'sma20': sma20,
            'ema20': ema20,
            'boll_upper': boll_upper,
            'boll_lower': boll_lower,
            'stoch_k': stoch_k,
            'stoch_d': stoch_d,
            'patterns': patterns,
            'figures': figures,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

    def analyze_all(self):
        results = []
        for pair in self.pairs:
            self.fetch_history(pair)
            result = self.analyze_pair(pair)
            if result:
                results.append(result)
        return results

    def export_signals(self, signals, filename='forex_signals.json'):
        with open(filename, 'w') as f:
            json.dump(signals, f, indent=2)
        print(f"[ForexBrain] Сигналы сохранены в {filename}")

    def get_market_snapshot(self, pair):
        df = self.data.get(pair)
        if df is None or df.empty:
            return None

        last = df.iloc[-1]
        snapshot = {
            "pair": pair,
            "price": float(last["close"]),
            "high": float(last["high"]),
            "low": float(last["low"]),
            "volume": float(last["volume"]),
            "time": last["time"]
        }
        return snapshot
        
if __name__ == "__main__":
    brain = ForexBrain()
    signals = brain.analyze_all()
    brain.export_signals(signals)
    print(json.dumps(signals, indent=2))
