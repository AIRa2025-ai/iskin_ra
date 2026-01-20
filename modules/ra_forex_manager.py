# modules/ra_forex_manager.py
import time
import json
import logging
from datetime import datetime

from modules.forex_brain import ForexBrain
from modules.ra_market_consciousness import RaMarketConsciousness

# ================= TELEGRAM SENDER =================
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
            self.requests.post(url, data=data, timeout=10)
        except Exception as e:
            logging.error(f"[TelegramSender] Ошибка отправки: {e}")

# ================= RA FOREX MANAGER =================
class RaForexManager:
    def __init__(self, pairs=None, timeframes=None, telegram_sender=None, log_file='forex_signals.json'):
        self.pairs = pairs or ['EURUSD', 'GBPUSD']
        self.timeframes = timeframes or ['M15', 'H1']
        self.telegram = telegram_sender
        self.log_file = log_file

        self.brain_modules = {}
        self.ra_modules = {}

        for pair in self.pairs:
            self.brain_modules[pair] = {}
            self.ra_modules[pair] = {}
            for tf in self.timeframes:
                brain = ForexBrain(pairs=[pair], timeframe=tf)
                ra = RaMarketConsciousness(pair, tf, telegram_sender)
                self.brain_modules[pair][tf] = brain
                self.ra_modules[pair][tf] = ra

        logging.info(f"[RaForexManager] Инициализирован: {self.pairs} | {self.timeframes}")

    # ================= ENTRY =================
    def compute_entry(self, df, signal):
        if df is None or len(df) < 2 or not signal:
            return None
        last = df.iloc[-1]
        prev = df.iloc[-2]

        if signal == "BUY":
            entry = min(last['close'], prev['low'])
        elif signal == "SELL":
            entry = max(last['close'], prev['high'])
        else:
            return None

        return round(entry, 5)

    # ================= SL / TP =================
    def compute_sl_tp(self, price, atr, signal):
        if not atr or not signal or not price:
            return None, None
        if signal == "BUY":
            return round(price - atr * 1.5, 5), round(price + atr * 3, 5)
        elif signal == "SELL":
            return round(price + atr * 1.5, 5), round(price - atr * 3, 5)
        return None, None

    # ================= АНАЛИЗ ПАРЫ ПО ТФ =================
    def analyze_pair_tf(self, pair, tf):
        brain = self.brain_modules[pair][tf]
        df = brain.fetch_history(pair)
        if df is None or df.empty or len(df) < 2:
            return None

        ra = self.ra_modules[pair][tf]
        ra.load_market_data(df)
        ra.analyze()

        # Проверка на пустые колонки
        try:
            rsi = ra.df['rsi'].iloc[-1] if 'rsi' in ra.df.columns and not ra.df.empty else None
            macd = ra.df['macd'].iloc[-1] if 'macd' in ra.df.columns and not ra.df.empty else None
            atr = ra.df['atr'].iloc[-1] if 'atr' in ra.df.columns and not ra.df.empty else None
            ema50 = ra.df['ema50'].iloc[-1] if 'ema50' in ra.df.columns and not ra.df.empty else None
            ema200 = ra.df['ema200'].iloc[-1] if 'ema200' in ra.df.columns and not ra.df.empty else None
            price = ra.df['close'].iloc[-1] if 'close' in ra.df.columns and not ra.df.empty else None
        except Exception as e:
            logging.warning(f"[RaForexManager] Ошибка анализа {pair} {tf}: {e}")
            return None

        if price is None:
            return None

        trend = 1 if ema50 and ema200 and ema50 > ema200 else -1
        score = 0
        reasons = []

        if rsi is not None:
            if rsi < 30: score += 1; reasons.append("RSI перепродан")
            if rsi > 70: score -= 1; reasons.append("RSI перекуплен")
        if macd is not None:
            score += 1 if macd > 0 else -1
            reasons.append("MACD бычий" if macd > 0 else "MACD медвежий")
        score += trend
        reasons.append("Тренд вверх" if trend > 0 else "Тренд вниз")

        signal = "BUY" if score >= 3 else "SELL" if score <= -2 else None
        sl, tp = self.compute_sl_tp(price, atr, signal)
        entry = self.compute_entry(df, signal)

        return {
            "pair": pair,
            "tf": tf,
            "signal": signal,
            "price": round(price, 5) if price else None,
            "entry": entry,
            "sl": sl,
            "tp": tp,
            "reasons": reasons,
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }

    # ================= КРОСС-ТФ =================
    def cross_tf_signal(self, pair):
        results = []
        for tf in self.timeframes:
            res = self.analyze_pair_tf(pair, tf)
            if res and res["signal"]:
                results.append(res)

        if len(results) >= 2 and all(r['signal'] == results[0]['signal'] for r in results):
            final = results[0]
            self.send_signal(final)
            self.log_signal(final)
            return final
        return None

    # ================= ВСЕ ПАРЫ =================
    def analyze_all(self):
        for pair in self.pairs:
            self.cross_tf_signal(pair)

    # ================= ОТПРАВКА =================
    def send_signal(self, signal):
        if not self.telegram or not signal:
            return
        msg = (
            f"🔥 {signal['pair']} | {signal['signal']}\n"
            f"TF: {signal['tf']}\n"
            f"Entry: {signal['entry']}\n"
            f"Цена: {signal['price']}\n"
            f"SL: {signal['sl']}\n"
            f"TP: {signal['tp']}\n"
            f"Основания:\n- " + "\n- ".join(signal['reasons'])
        )
        self.telegram.send(msg)

    # ================= ЛОГ =================
    def log_signal(self, signal):
        try:
            with open(self.log_file, 'r') as f:
                data = json.load(f)
        except:
            data = []
        data.append(signal)
        with open(self.log_file, 'w') as f:
            json.dump(data, f, indent=2)
        logging.info(f"[RaForexManager] Сигнал сохранён: {signal['pair']}")

    # ================= ЦИКЛ =================
    def run_loop(self, interval_sec=900):
        while True:
            logging.info("🔄 Анализируем рынок...")
            self.analyze_all()
            time.sleep(interval_sec)
