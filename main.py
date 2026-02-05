import os, json, time, threading, requests
import numpy as np
from binance.client import Client
from flask import Flask, jsonify

# ================= CONFIG =================
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")

SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"]
CHECK_INTERVAL = 60
MIN_SCORE = 70
# =========================================

client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

with open("setup.json") as f:
    SETUP = json.load(f)

dashboard_data = {"status": "ONLINE", "ranking": []}
last_signal = {}

# ============== INDICADORES ==============
def ema(data, period):
    weights = np.exp(np.linspace(-1., 0., period))
    weights /= weights.sum()
    return np.convolve(data, weights, mode='valid')[-1]

def rsi(data, period=14):
    delta = np.diff(data)
    gain = np.maximum(delta, 0)
    loss = np.abs(np.minimum(delta, 0))
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    if avg_loss == 0:
        return 100
    return 100 - (100 / (1 + avg_gain / avg_loss))

def get_closes(symbol, interval):
    klines = client.futures_klines(symbol=symbol, interval=interval, limit=100)
    return np.array([float(k[4]) for k in klines])

# ============== SCORE =====================
def calculate_score(symbol):
    trend, momentum, volatility, confluence = 0, 0, 0, 0
    directions = []

    for tf in SETUP["timeframes"]:
        closes = get_closes(symbol, tf)
        price = closes[-1]

        ema9 = ema(closes, 9)
        ema21 = ema(closes, 21)
        rsi_val = rsi(closes)
        bb_mid = np.mean(closes[-20:])

        if ema9 > ema21:
            trend += 1
        if 40 <= rsi_val <= 60:
            momentum += 1
        if abs(price - bb_mid) / price < 0.01:
            volatility += 1

        if price > ema21 and ema9 > ema21:
            directions.append("LONG")
        elif price < ema21 and ema9 < ema21:
            directions.append("SHORT")

    if len(set(directions)) == 1:
        confluence = 3
        direction = directions[0]
    else:
        direction = "NEUTRO"

    score = (
        (trend / 3) * 30 +
        (momentum / 3) * 30 +
        (volatility / 3) * 20 +
        (confluence / 3) * 20
    )

    return round(score, 2), direction

# ============== ALERTAS ===================
def send_alert(msg):
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg}
        )
    if DISCORD_WEBHOOK:
        requests.post(DISCORD_WEBHOOK, json={"content": msg})

# ============== BOT LOOP ==================
def bot_loop():
    global dashboard_data
    print("STONKS BR SIGNALS - BOT INICIADO")

    while True:
        ranking = []

        for symbol in SYMBOLS:
            score, direction = calculate_score(symbol)
            ranking.append({
                "symbol": symbol,
                "score": score,
                "direction": direction
            })

        ranking.sort(key=lambda x: x["score"], reverse=True)
        top3 = ranking[:3]
        dashboard_data["ranking"] = top3

        for asset in top3:
            if asset["score"] < MIN_SCORE or asset["direction"] == "NEUTRO":
                continue

            symbol = asset["symbol"]
            direction = asset["direction"]

            if last_signal.get(symbol) == direction:
                continue

            msg = (
                f"🔥 TOP 3 SIGNAL 🔥\n\n"
                f"Par: {symbol}\n"
                f"Direção: {direction}\n"
                f"Score: {asset['score']}\n"
                f"Setup: {SETUP['setup_name']}"
            )

            send_alert(msg)
            last_signal[symbol] = direction

        time.sleep(CHECK_INTERVAL)

# ============== WEB =======================
app = Flask(__name__)

@app.route("/")
def home():
    return jsonify(dashboard_data)

def start_http():
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ============== START =====================
if __name__ == "__main__":
    threading.Thread(target=start_http, daemon=True).start()
    bot_loop()




