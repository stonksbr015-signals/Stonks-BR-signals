import os, json, time, threading, requests
import numpy as np
from binance.client import Client
from flask import Flask, jsonify, render_template_string

# ================= CONFIG =================
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
CHECK_INTERVAL = 60
MIN_SCORE = 70

client = Client()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")

with open("setup.json") as f:
    SETUP = json.load(f)

dashboard = {"ranking": [], "trades": []}
last_signal = {}

# ================= INDICADORES =================
def ema(data, period):
    w = np.exp(np.linspace(-1., 0., period))
    w /= w.sum()
    return np.convolve(data, w, mode='valid')[-1]

def rsi(data, period=14):
    delta = np.diff(data)
    gain = np.maximum(delta, 0)
    loss = np.abs(np.minimum(delta, 0))
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    return 100 if avg_loss == 0 else 100 - (100 / (1 + avg_gain / avg_loss))

def closes(symbol, tf):
    k = client.futures_klines(symbol=symbol, interval=tf, limit=100)
    return np.array([float(c[4]) for c in k])

# ================= SCORE =================
def score_asset(symbol):
    trend = momentum = volatility = 0
    directions = []

    for tf in SETUP["timeframes"]:
        c = closes(symbol, tf)
        price = c[-1]
        e9 = ema(c, 9)
        e21 = ema(c, 21)
        r = rsi(c)
        mid = np.mean(c[-20:])

        if e9 > e21: trend += 1
        if 40 <= r <= 60: momentum += 1
        if abs(price - mid) / price < 0.01: volatility += 1

        if price > e21 and e9 > e21:
            directions.append("LONG")
        elif price < e21 and e9 < e21:
            directions.append("SHORT")

    direction = directions[0] if len(set(directions)) == 1 else "NEUTRO"
    confluence = 3 if direction != "NEUTRO" else 0

    score = (
        (trend/3)*30 +
        (momentum/3)*30 +
        (volatility/3)*20 +
        (confluence/3)*20
    )
    return round(score, 2), direction, price

# ================= ALERTAS =================
def alert(msg):
    if TELEGRAM_TOKEN:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg}
        )
    if DISCORD_WEBHOOK:
        requests.post(DISCORD_WEBHOOK, json={"content": msg})

# ================= BOT =================
def bot():
    print("STONKS BR SIGNALS - BOT INICIADO")

    while True:
        ranking = []

        for s in SYMBOLS:
            score, direction, price = score_asset(s)
            ranking.append({
                "symbol": s,
                "score": score,
                "direction": direction,
                "price": price
            })

        ranking.sort(key=lambda x: x["score"], reverse=True)
        dashboard["ranking"] = ranking[:3]

        for a in dashboard["ranking"]:
            if a["score"] < MIN_SCORE or a["direction"] == "NEUTRO":
                continue

            if last_signal.get(a["symbol"]) == a["direction"]:
                continue

            sl = round(a["price"] * 0.99, 2)
            tp = round(a["price"] * 1.02, 2)

            trade = {
                "symbol": a["symbol"],
                "direction": a["direction"],
                "entry": a["price"],
                "sl": sl,
                "tp": tp
            }

            dashboard["trades"].append(trade)
            alert(
                f"🔥 STONKS BR SIGNAL 🔥\n\n"
                f"{a['symbol']} | {a['direction']}\n"
                f"Entry: {a['price']}\n"
                f"SL: {sl}\nTP: {tp}\n"
                f"Score: {a['score']}"
            )

            last_signal[a["symbol"]] = a["direction"]

        time.sleep(CHECK_INTERVAL)

# ================= DASHBOARD =================
app = Flask(__name__)

@app.route("/")
def home():
    return render_template_string("""
<!doctype html>
<html>
<head>
<title>STONKS BR DASHBOARD</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
<h2>STONKS BR SIGNALS</h2>
<pre>{{ data }}</pre>
</body>
</html>
""", data=json.dumps(dashboard, indent=2))

def web():
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

# ================= START =================
if __name__ == "__main__":
    threading.Thread(target=web, daemon=True).start()
    bot()



