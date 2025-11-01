import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# Функция оценки сигнала
def analyze_signal(data):
    """
    data: dict с котировками, ATR, RSI, Stochastic, объёмами
    Вернёт allow_entry (bool) и confidence (float)
    """
    closeM15 = data["closeM15"]
    closeH1  = data["closeH1"]
    atr      = data["atr"]
    rsi      = data["rsi"]
    stoch    = data["stoch"]
    volume   = data["volume"]

    # Простейшая логика, потом можно заменить на GPT
    trend_up = closeH1[-1] > closeH1[-2]
    trend_down = closeH1[-1] < closeH1[-2]

    if data["type"] == "BUY" and trend_up and rsi < 50 and stoch < 50 and volume > 0:
        return {"allow_entry": True, "confidence": 0.85}
    elif data["type"] == "SELL" and trend_down and rsi > 50 and stoch > 50 and volume > 0:
        return {"allow_entry": True, "confidence": 0.85}
    else:
        return {"allow_entry": False, "confidence": 0.3}

# REST API
@app.route("/check_signal", methods=["POST"])
def check_signal():
    data = request.json
    result = analyze_signal(data)
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
