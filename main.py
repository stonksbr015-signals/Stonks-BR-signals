import os
import json
import time
import threading
import requests
import numpy as np
from binance.client import Client
from flask import Flask

# ================== CONFIG ==================
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")

SYMBOLS = ["BTCUSDT", "ETHUSDT"]
CHECK_INTERVAL = 60  # segundos

# ============================================

client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

with open("setup.json", "r") as f:
    SETUP = json.load(f)

last_signal = {}

# ================== INDICADORES ==================
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
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def bollinger_mid(data, period=20):
    return np.mean(data[-period:])

# ================== DADOS ==================
def get_closes(symbol, interval, limit=100):
    klines = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
    return np.array([float(k[4]) for k in klines])

# ================== SINAL ==================
def analyze_symbol(symbol):
    directions = []

    for tf in SETUP["timeframes"]:
        closes = get_closes(symbol, tf)
        price = closes[-1]

        ema9 = ema(closes, 9)
        ema21 = ema(closes, 21)
        rsi_val = rsi(closes)
        bb_mid = bollinger_mid(closes)

        if price > ema21 and ema9 > ema21 and 40 <= rsi_val <= 60 and price >= bb_mid:
            directions.append("LONG")
        elif price < ema21 and ema9 < ema21 and 40 <= rsi_val <= 60 and price <= bb_mid:
            directions.append("SHORT")
        else:
            return None

    if len(set(directions)) == 1:
        return directions[0], price

    return None

# ================== ALERTAS ==================
def send_alert(msg):
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg}
        )

    if DISCORD_WEBHOOK:
        requests.post(DISCORD_WEBHOOK, json={"content": msg})

# ================== LOOP ==================
def bot_loop():
    print("STONKS BR SIGNALS - BOT INICIADO")
    while True:
        for symbol in SYMBOLS:
            result = analyze_symbol(symbol)
            if not result:
                continue

            direction, price = result

            if last_signal.get(symbol) == direction:
                continue

            stop = price * (1 - 0.01) if direction == "LONG" else price * (1 + 0.01)
            target = price * (1 + 0.02) if direction == "LONG" else price * (1 - 0.02)

            msg = (
                f"🚀 {symbol} {direction}\n\n"
                f"Preço: {price:.2f}\n"
                f"Timeframes: {', '.join(SETUP['timeframes'])}\n"
                f"Stop: {stop:.2f}\n"
                f"Alvo: {target:.2f}\n"
                f"Setup: {SETUP['setup_name']}"
            )

            send_alert(msg)
            last_signal[symbol] = direction

        time.sleep(CHECK_INTERVAL)

# ================== HTTP SERVER ==================
app = Flask(__name__)

@app.route("/")
def home():
    return "STONKS BR SIGNALS ONLINE"

def start_http():
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ================== START ==================
if __name__ == "__main__":
    threading.Thread(target=start_http, daemon=True).start()
    bot_loop()



