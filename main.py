import json
import time
import requests
import numpy as np
from flask import Flask

# =========================
# CONFIGURAÇÕES
# =========================
BINANCE_API = "https://api.binance.com/api/v3/klines"
SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
TIMEFRAMES = {
    "15m": "15m",
    "1h": "1h",
    "12h": "12h"
}

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# =========================
# UTILIDADES
# =========================
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})

def fetch_klines(symbol, interval, limit=100):
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    data = requests.get(BINANCE_API, params=params).json()
    closes = [float(c[4]) for c in data]
    return np.array(closes)

def ema(values, period):
    weights = np.exp(np.linspace(-1., 0., period))
    weights /= weights.sum()
    return np.convolve(values, weights, mode="valid")

def rsi(values, period=14):
    deltas = np.diff(values)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# =========================
# ANÁLISE DO SETUP
# =========================
def analyze_symbol(symbol):
    confirmations = []

    for tf, interval in TIMEFRAMES.items():
        closes = fetch_klines(symbol, interval)

        ema9 = ema(closes, 9)[-1]
        ema21 = ema(closes, 21)[-1]
        current_price = closes[-1]
        rsi_val = rsi(closes)

        if current_price > ema21 and ema9 > ema21 and 40 <= rsi_val <= 60:
            confirmations.append("LONG")
        elif current_price < ema21 and ema9 < ema21 and 40 <= rsi_val <= 60:
            confirmations.append("SHORT")
        else:
            return None

    if all(c == confirmations[0] for c in confirmations):
        return confirmations[0]

    return None

# =========================
# LOOP PRINCIPAL
# =========================
def run_bot():
    send_telegram("🤖 STONKS BR SIGNALS iniciado e monitorando o mercado.")

    while True:
        for symbol in SYMBOLS:
            direction = analyze_symbol(symbol)

            if direction:
                msg = (
                    f"📊 *SINAL CONFIRMADO*\n\n"
                    f"Par: {symbol}\n"
                    f"Direção: {direction}\n"
                    f"Timeframes: 15m / 1h / 12h\n"
                    f"Stop: 1%\n"
                    f"Alvo: 2%\n"
                    f"RR: 1:2\n\n"
                    f"Setup: STONKS_BR_CORE_SETUP"
                )
                send_telegram(msg)
                time.sleep(60)

        time.sleep(30)

# =========================
# FLASK (KEEP ALIVE)
# =========================
app = Flask(__name__)

@app.route("/")
def health():
    return "STONKS BR SIGNALS - ONLINE"

if __name__ == "__main__":
    import threading
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=8080)



