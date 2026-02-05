import os
import time
import json
import requests
import numpy as np
from flask import Flask
from datetime import datetime

# =========================
# CONFIG
# =========================
BINANCE_API = "https://api.binance.com/api/v3/klines"
SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]

TIMEFRAMES = {
    "15m": "15m",
    "1h": "1h",
    "12h": "12h"
}

STOP_PCT = 0.01
TAKE_PCT = 0.02

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

open_trades = {}

# =========================
# TELEGRAM
# =========================
def send_telegram(msg):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})

# =========================
# INDICADORES
# =========================
def fetch_klines(symbol, interval, limit=100):
    data = requests.get(BINANCE_API, params={
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }).json()
    return np.array([float(c[4]) for c in data])

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
# SETUP
# =========================
def check_setup(symbol):
    directions = []

    for tf, interval in TIMEFRAMES.items():
        closes = fetch_klines(symbol, interval)
        price = closes[-1]

        ema9 = ema(closes, 9)[-1]
        ema21 = ema(closes, 21)[-1]
        rsi_val = rsi(closes)

        if price > ema21 and ema9 > ema21 and 40 <= rsi_val <= 60:
            directions.append("LONG")
        elif price < ema21 and ema9 < ema21 and 40 <= rsi_val <= 60:
            directions.append("SHORT")
        else:
            return None, price

    if all(d == directions[0] for d in directions):
        return directions[0], price

    return None, price

# =========================
# PAPER TRADE ENGINE
# =========================
def manage_trade(symbol, price):
    trade = open_trades[symbol]

    if trade["direction"] == "LONG":
        if price <= trade["stop"]:
            close_trade(symbol, price, "STOP")
        elif price >= trade["take"]:
            close_trade(symbol, price, "TAKE")

    if trade["direction"] == "SHORT":
        if price >= trade["stop"]:
            close_trade(symbol, price, "STOP")
        elif price <= trade["take"]:
            close_trade(symbol, price, "TAKE")

def close_trade(symbol, price, result):
    trade = open_trades.pop(symbol)

    pnl = (
        (price - trade["entry"]) / trade["entry"]
        if trade["direction"] == "LONG"
        else (trade["entry"] - price) / trade["entry"]
    ) * 100

    send_telegram(
        f"📉 TRADE ENCERRADO\n\n"
        f"Par: {symbol}\n"
        f"Resultado: {result}\n"
        f"PnL: {pnl:.2f}%\n"
        f"Direção: {trade['direction']}"
    )

def open_trade(symbol, direction, price):
    stop = price * (1 - STOP_PCT) if direction == "LONG" else price * (1 + STOP_PCT)
    take = price * (1 + TAKE_PCT) if direction == "LONG" else price * (1 - TAKE_PCT)

    open_trades[symbol] = {
        "direction": direction,
        "entry": price,
        "stop": stop,
        "take": take,
        "time": datetime.utcnow()
    }

    send_telegram(
        f"🚀 PAPER TRADE ABERTO\n\n"
        f"Par: {symbol}\n"
        f"Direção: {direction}\n"
        f"Entrada: {price:.2f}\n"
        f"Stop: {stop:.2f}\n"
        f"Take: {take:.2f}"
    )

# =========================
# LOOP
# =========================
def run_bot():
    send_telegram("🤖 STONKS BR PAPER TRADE iniciado")

    while True:
        for symbol in SYMBOLS:
            closes = fetch_klines(symbol, "15m")
            price = closes[-1]

            if symbol in open_trades:
                manage_trade(symbol, price)
                continue

            direction, entry_price = check_setup(symbol)
            if direction:
                open_trade(symbol, direction, entry_price)

        time.sleep(60)

# =========================
# FLASK
# =========================
app = Flask(__name__)

@app.route("/")
def status():
    return "STONKS BR PAPER TRADE - ONLINE"

if __name__ == "__main__":
    import threading
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=8080)


