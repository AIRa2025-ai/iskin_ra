from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/signal", methods=["POST"])
def signal():
    data = request.get_json()
    # тут можно вставить любую логику ИИ: EMA, ATR, старший тренд
    # для теста пока просто отправим "BUY" или "SELL"
    action = "BUY" if data["trend_higher_tf"] == "UP" else "SELL"
    sl = 20
    tp = 50
    lot = 0.1
    return jsonify({"action": action, "sl_points": sl, "tp_points": tp, "lot": lot})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
