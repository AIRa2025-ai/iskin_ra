import os, json, time
from pathlib import Path
from datetime import datetime
import MetaTrader5 as mt5

SYMBOL = "EURUSD"
TIMEFRAME = mt5.TIMEFRAME_M15
LOOKBACK = 200
JSON_FILE = os.path.join(os.getcwd(), "Files", "ra_signal.json")

# инициализация MT5
if not mt5.initialize():
    print("Ошибка инициализации MT5, продолжаем без терминала")
else:
    print("MT5 подключен, версия:", mt5.version())

def get_candles(symbol, timeframe, n):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n)
    return rates

def analyze_fvg(candles):
    fvg_list = []
    for i in range(2, len(candles)):
        highA, lowA = candles[i-2]['high'], candles[i-2]['low']
        highB, lowB = candles[i-1]['high'], candles[i-1]['low']
        highC, lowC = candles[i]['high'], candles[i]['low']
        # Bullish FVG
        if lowC > highA:
            fvg_list.append({
                "type": "bull",
                "time_from": int(candles[i-2]['time']),
                "time_to": int(candles[i]['time']),
                "price_top": highA,
                "price_bottom": lowB
            })
        # Bearish FVG
        if highC < lowA:
            fvg_list.append({
                "type": "bear",
                "time_from": int(candles[i-2]['time']),
                "time_to": int(candles[i]['time']),
                "price_top": highB,
                "price_bottom": lowB
            })
    return fvg_list

def forecast(candles):
    closes = [c['close'] for c in candles]
    ema = sum(closes[-100:])/100
    delta_up = sum(max(closes[i+1]-closes[i],0) for i in range(-14,-1))
    delta_down = sum(abs(closes[i+1]-closes[i]) for i in range(-14,-1))
    rsi = 100 - (100/(1 + delta_up/(delta_down if delta_down!=0 else 1)))
    price = closes[-1]
    signal = "bull" if price > ema and rsi<70 else "bear" if price < ema and rsi>30 else "none"
    return {"signal": signal, "ema": ema, "rsi": rsi, "price": price}

def write_json(signal, fvg):
    data = {
        "timestamp": int(datetime.now().timestamp()),
        "symbol": SYMBOL,
        "signal": signal["signal"],
        "ema": signal["ema"],
        "rsi": signal["rsi"],
        "price": signal["price"],
        "fvg": fvg
    }
    Path(os.path.dirname(JSON_FILE)).mkdir(parents=True, exist_ok=True)
    with open(JSON_FILE,"w") as f:
        json.dump(data,f,indent=2)

# основной цикл
while True:
    try:
        candles = get_candles(SYMBOL,TIMEFRAME,LOOKBACK)
        fvg = analyze_fvg(candles)
        signal = forecast(candles)
        write_json(signal,fvg)
        print("Обновлено ra_signal.json:", signal["signal"], datetime.now())
    except Exception as e:
        print("Ошибка:", e)
    time.sleep(60)  # обновление каждые 60 секунд
