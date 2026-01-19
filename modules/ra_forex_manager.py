# ra_forex_manager.py — МУЛЬТИ-ТИМФРЕЙМ + КРОСС-СИГНАЛЫ
from modules.forex_brain import ForexBrain
from modules.ra_market_consciousness import RaMarketConsciousness
from datetime import datetime
import time
import json
import logging

class TelegramSender:
    def __init__(self, bot_token, chat_id):
        import requests
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.requests = requests

    def send(self, message):
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = {"chat_id": self.chat_id, "text": message}
        try:
            self.requests.post(url, data=data)
        except Exception as e:
            print(f"[TelegramSender] Ошибка отправки: {e}")

class RaForexManager:
    def __init__(self, pairs=None, timeframes="1h", telegram_sender=None, log_file='forex_signals.json'):
        self.timeframes = timeframes or ['M15', 'H1']
        self.telegram = telegram_sender
        self.log_file = log_file
        self.brain_modules = {}  # {pair: {tf: ForexBrain}}
        self.ra_modules = {}     # {pair: {tf: RaMarketConsciousness}}

        for pair in pairs or ['EURUSD', 'GBPUSD']:
            self.brain_modules[pair] = {}
            self.ra_modules[pair] = {}
            for tf in self.timeframes:
                brain = ForexBrain(pairs=[pair], timeframe=tf)
                self.brain_modules[pair][tf] = brain
                self.ra_modules[pair][tf] = RaMarketConsciousness(pair, tf, telegram_sender)

        self.brain = ForexBrain(pairs=pairs, timeframe=timeframe)
        self.consciousness = RaMarketConsciousness()

    def update(self):
        results = []

        for pair in self.brain.pairs:
            df = self.brain.fetch_history(pair)
            if df is None:
                continue

            snapshot = self.brain.get_market_snapshot(pair)
            signal = self.consciousness.perceive(snapshot)

            if signal:
                results.append(signal)

        return results

    # -------------------- ФИГУРЫ --------------------
    def detect_figures(self, df):
        figures = []
        if len(df) < 5:
            return figures
        highs, lows = df['high'], df['low']
        if highs.iloc[-1] < highs.iloc[-3] > highs.iloc[-5]:
            figures.append('Double Top')
        if lows.iloc[-1] > lows.iloc[-3] < lows.iloc[-5]:
            figures.append('Double Bottom')
        if abs(highs.iloc[-1] - highs.iloc[-5]) < (highs.max() - lows.min()) * 0.05:
            figures.append('Triangle')
        if abs(highs.iloc[-1] - lows.iloc[-1]) < (highs.max() - lows.min()) * 0.1:
            figures.append('Flag')
        return figures

    # -------------------- SL/TP --------------------
    def compute_sl_tp(self, price, atr, signal):
        if signal == "BUY":
            return round(price - atr * 1.5, 5), round(price + atr * 3, 5)
        elif signal == "SELL":
            return round(price + atr * 1.5, 5), round(price - atr * 3, 5)
        return None, None

    # -------------------- АНАЛИЗ ОДНОЙ ПАРЫ ПО ТАЙМФРЕЙМУ --------------------
    def analyze_pair_tf(self, pair, tf):
        brain = self.brain_modules[pair][tf]
        df = brain.fetch_history(pair)
        if df is None or len(df) < 10:
            return None

        ra = self.ra_modules[pair][tf]
        ra.load_market_data(df)
        ra.analyze()

        figures = self.detect_figures(df)

        rsi = ra.df['rsi'].iloc[-1]
        macd = ra.df['macd'].iloc[-1]
        atr = ra.df['atr'].iloc[-1]
        ema50 = ra.df['ema50'].iloc[-1]
        ema200 = ra.df['ema200'].iloc[-1]
        price = ra.df['close'].iloc[-1]

        trend = 1 if ema50 > ema200 else -1
        score = 0
        reasons = []

        if rsi < 30: score += 1; reasons.append("RSI перепродан")
        if rsi > 70: score -= 1; reasons.append("RSI перекуплен")
        score += 1 if macd > 0 else -1; reasons.append("MACD бычий" if macd > 0 else "MACD медвежий")
        score += trend; reasons.append("Тренд вверх" if trend > 0 else "Тренд вниз")
        score += len(figures); reasons += figures

        signal = "BUY" if score >= 3 else "SELL" if score <= -2 else None
        sl, tp = self.compute_sl_tp(price, atr, signal)

        return {
            "pair": pair,
            "tf": tf,
            "signal": signal,
            "price": price,
            "sl": sl,
            "tp": tp,
            "rsi": rsi,
            "macd": macd,
            "ema50": ema50,
            "ema200": ema200,
            "atr": atr,
            "figures": figures,
            "reasons": reasons,
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }

    # -------------------- КРОСС-СИГНАЛЫ --------------------
    def cross_tf_signal(self, pair):
        results = []
        for tf in self.timeframes:
            res = self.analyze_pair_tf(pair, tf)
            if res:
                results.append(res)

        # Проверка согласованности сигналов
        signals = [r['signal'] for r in results if r['signal']]
        if len(signals) >= 2 and all(s == signals[0] for s in signals):
            final_signal = signals[0]
            final_result = results[0]
            final_result['signal'] = final_signal
            if final_signal and self.telegram:
                msg = f"🔥 {pair} | {final_signal} (согласовано по таймфреймам)\nЦена: {final_result['price']:.5f}\nSL: {final_result['sl']}\nTP: {final_result['tp']}\nОснования:\n- " + "\n- ".join(final_result['reasons'])
                self.telegram.send(msg)
            self.log_signal(final_result)
            return final_result
        else:
            # Нет согласованного сигнала
            return None

    # -------------------- АНАЛИЗ ВСЕХ ПАР --------------------
    def analyze_all(self):
        results = []
        for pair in self.brain_modules.keys():
            res = self.cross_tf_signal(pair)
            if res:
                results.append(res)
        return results

    # -------------------- ЛОГИРОВАНИЕ --------------------
    def log_signal(self, signal):
        try:
            with open(self.log_file, 'r') as f:
                data = json.load(f)
        except:
            data = []
        data.append(signal)
        with open(self.log_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"[RaForexManager] Сигнал {signal['pair']} сохранён.")

    # -------------------- ЦИКЛ --------------------
    def run_loop(self, interval_sec=3600):
        while True:
            print(f"[{datetime.utcnow()}] 🔄 Обновляем и анализируем все пары...")
            self.analyze_all()
            time.sleep(interval_sec)

# ====================== ПРИМЕР ЗАПУСКА ======================
if __name__ == "__main__":
    bot_token = "7304435178:AAFzVnyQVtBMiYMXDvShbfcyPDw1_JnPCFM"
    chat_id = "5694569448"
    telegram = TelegramSender(bot_token, chat_id)

    pairs = ['EURUSD', 'GBPUSD']
    timeframes = ['1h', '4h']
    manager = RaForexManager(pairs=pairs, timeframes=timeframes, telegram_sender=telegram)

    # Один проход для теста
    manager.analyze_all()
