# ra_forex_manager.py
from modules.forex_brain import ForexBrain
from modules.ra_market_consciousness import RaMarketConsciousness
from datetime import datetime
import time
import json

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
    def __init__(self, pairs=None, timeframe='1h', telegram_sender=None, log_file='forex_signals.json'):
        self.brain = ForexBrain(pairs=pairs, timeframe=timeframe)
        self.ra_modules = {}
        self.telegram = telegram_sender
        self.log_file = log_file

        for pair in self.brain.pairs:
            self.ra_modules[pair] = RaMarketConsciousness(pair, timeframe, telegram_sender)

    # -------------------- ФИГУРЫ --------------------
    def detect_figures(self, df):
        """Простейшее распознавание фигур: треугольники, двойные вершины/основания, флаги"""
        figures = []

        if len(df) < 5:
            return figures

        highs = df['high']
        lows = df['low']

        # Двойная вершина
        if len(highs) >= 5 and highs.iloc[-1] < highs.iloc[-3] and highs.iloc[-3] > highs.iloc[-5]:
            figures.append('Double Top')

        # Двойное основание
        if len(lows) >= 5 and lows.iloc[-1] > lows.iloc[-3] and lows.iloc[-3] < lows.iloc[-5]:
            figures.append('Double Bottom')

        # Простые треугольники (по последним 5 свечам)
        if abs(highs.iloc[-1] - highs.iloc[-5]) < (highs.max() - highs.min()) * 0.05:
            figures.append('Triangle')

        # Флаг (короткий горизонтальный канал)
        if abs(highs.iloc[-1] - lows.iloc[-1]) < (highs.max() - lows.min()) * 0.1:
            figures.append('Flag')

        return figures

    # -------------------- АНАЛИЗ ОДНОЙ ПАРЫ --------------------
    def analyze_pair(self, pair):
        df = self.brain.fetch_history(pair)
        if df is None or len(df) < 10:
            return None

        ra = self.ra_modules[pair]
        ra.load_market_data(df)

        # Анализируем индикаторы через Ra
        ra.analyze()

        # Дополнительные фигуры
        figures = self.detect_figures(df)

        # Собираем полный анализ для логирования
        rsi = ra.df['rsi'].iloc[-1]
        macd = ra.df['macd'].iloc[-1]
        atr = ra.df['atr'].iloc[-1]
        ema50 = ra.df['ema50'].iloc[-1]
        ema200 = ra.df['ema200'].iloc[-1]
        price = ra.df['close'].iloc[-1]

        # Дополнительно сигнал на основе нескольких индикаторов
        signal = None
        score = 0
        reasons = []

        if rsi < 30:
            score += 1
            reasons.append("RSI перепродан")
        if rsi > 70:
            score += 1
            reasons.append("RSI перекуплен")
        if macd > 0:
            score += 1
            reasons.append("MACD бычий")
        else:
            score -= 1
            reasons.append("MACD медвежий")
        if price > ema50 > ema200:
            score += 1
            reasons.append("Восходящий тренд EMA")
        if price < ema50 < ema200:
            score -= 1
            reasons.append("Нисходящий тренд EMA")
        if figures:
            score += len(figures)
            reasons += figures

        if score >= 3:
            signal = 'BUY'
        elif score <= -2:
            signal = 'SELL'

        result = {
            'pair': pair,
            'signal': signal,
            'price': price,
            'rsi': rsi,
            'macd': macd,
            'atr': atr,
            'ema50': ema50,
            'ema200': ema200,
            'figures': figures,
            'reasons': reasons,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

        # Отправка в телегу и логирование
        if signal and self.telegram:
            message = f"🔥 {pair} | {signal}\nЦена: {price:.5f}\nОснования:\n- " + "\n- ".join(reasons)
            self.telegram.send(message)

        self.log_signal(result)
        return result

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

    # -------------------- АНАЛИЗ ВСЕХ ПАР --------------------
    def analyze_all(self):
        results = []
        for pair in self.brain.pairs:
            result = self.analyze_pair(pair)
            if result:
                results.append(result)
        return results

    # -------------------- ЦИКЛ --------------------
    def run_loop(self, interval_sec=3600):
        while True:
            print(f"[{datetime.utcnow()}] 🔄 Обновляем и анализируем все пары...")
            self.analyze_all()
            time.sleep(interval_sec)

# ====================== ПРИМЕР ЗАПУСКА ======================
if __name__ == "__main__":
    bot_token = "ВАШ_TELEGRAM_BOT_TOKEN"
    chat_id = "ВАШ_CHAT_ID"
    telegram = TelegramSender(bot_token, chat_id)

    pairs = ['EURUSD', 'GBPUSD']
    manager = RaForexManager(pairs=pairs, timeframe='1h', telegram_sender=telegram)

    # Один проход для теста
    manager.analyze_all()
