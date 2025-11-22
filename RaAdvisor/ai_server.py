from fastapi import FastAPI, Request
from pydantic import BaseModel
import pandas as pd
import MetaTrader5 as mt5

app = FastAPI()

#--- параметры
SYMBOL = "EURUSD"  # можно менять динамически через JSON
TIMEFRAME = mt5.TIMEFRAME_M30
HIGHER_TF = mt5.TIMEFRAME_H1
EMA_FAST = 9
EMA_SLOW = 24
ATR_PERIOD = 14
RISK_PERCENT = 2.0

class SignalRequest(BaseModel):
    symbol: str

#--- вспомогательные функции
def get_data(symbol, timeframe, bars=100):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    df = pd.DataFrame(rates)
    return df

def calculate_ema(df, period, column='close'):
    return df[column].ewm(span=period, adjust=False).mean()

def calculate_atr(df, period):
    df['high-low'] = df['high'] - df['low']
    df['high-close'] = abs(df['high'] - df['close'].shift())
    df['low-close'] = abs(df['low'] - df['close'].shift())
    df['tr'] = df[['high-low','high-close','low-close']].max(axis=1)
    atr = df['tr'].rolling(period).mean().iloc[-1]
    return atr

@app.post("/signal")
async def signal(req: SignalRequest):
    symbol = req.symbol

    #--- данные для основного TF
    df = get_data(symbol, TIMEFRAME, 100)
    df['ema_fast'] = calculate_ema(df, EMA_FAST)
    df['ema_slow'] = calculate_ema(df, EMA_SLOW)

    #--- данные для старшего TF
    df_htf = get_data(symbol, HIGHER_TF, 100)
    df_htf['ema_fast'] = calculate_ema(df_htf, EMA_FAST)
    df_htf['ema_slow'] = calculate_ema(df_htf, EMA_SLOW)

    #--- определяем направление старшего тренда
    trend_up = df_htf['ema_fast'].iloc[-1] > df_htf['ema_slow'].iloc[-1]
    trend_down = df_htf['ema_fast'].iloc[-1] < df_htf['ema_slow'].iloc[-1]

    #--- кросс EMA на текущем TF
    fast_prev = df['ema_fast'].iloc[-2]
    fast_curr = df['ema_fast'].iloc[-1]
    slow_prev = df['ema_slow'].iloc[-2]
    slow_curr = df['ema_slow'].iloc[-1]

    cross_up = fast_prev < slow_prev and fast_curr > slow_curr
    cross_down = fast_prev > slow_prev and fast_curr < slow_curr

    if not cross_up and not cross_down:
        return {"action": "NONE"}

    atr = calculate_atr(df, ATR_PERIOD)

    #--- задаем стоп и тейк
    if cross_up:
        if trend_up: sl, tp = 20, 50
        else:       sl, tp = 25, 10
        action = "BUY"
    elif cross_down:
        if trend_down: sl, tp = 20, 50
        else:         sl, tp = 25, 10
        action = "SELL"

    #--- расчет лота
    account_info = mt5.account_info()
    balance = account_info.balance
    tick_value = mt5.symbol_info(symbol).trade_tick_value
    tick_size  = mt5.symbol_info(symbol).trade_tick_size
    lot = (balance * RISK_PERCENT / 100) / (sl * (tick_value/tick_size))
    lot = round(lot, 2)

    return {
        "action": action,
        "sl_points": sl,
        "tp_points": tp,
        "lot": lot
    }

if __name__ == "__main__":
    import uvicorn
    mt5.initialize()
    uvicorn.run(app, host="127.0.0.1", port=5000)
