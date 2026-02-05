import os
import json
import time
import threading
import requests
from flask import Flask, jsonify

# ===============================
# CONFIGURAÇÕES GERAIS
# ===============================

APP_PORT = int(os.getenv("PORT", 8080))

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")

# ===============================
# SETUP CORE (JSON DO PROJETO)
# ===============================

CORE_SETUP = {
    "setup_name": "STONKS_BR_CORE_SETUP",
    "market": "Binance Futures",
    "contract_type": "USD-M",
    "analysis_type": "Multi-timeframe confluente",
    "timeframes": ["15m", "1h", "12h"],
    "risk": {
        "stop_loss_percent": 1,
        "take_profit_percent": 2,
        "risk_reward": "1:2"
    },
    "signal_rules": {
        "long": [
            "Preço acima da EMA 21",
            "EMA 9 acima da EMA 21",
            "RSI entre 40 e 60",
            "Confluência total"
        ],
        "short": [
            "Preço abaixo da EMA 21",
            "EMA 9 abaixo da EMA 21",
            "RSI entre 40 e 60",
            "Confluência total"
        ]
    }
}

# ===============================
# FUNÇÕES DE ENVIO
# ===============================

def send_telegram(message: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram não configurado")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }

    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("Erro Telegram:", e)


def send_discord(message: str):
    if not DISCORD_WEBHOOK:
        print("Discord não configurado")
        return

    payload = {
        "content": message
    }

    try:
        r = requests.post(DISCORD_WEBHOOK, json=payload, timeout=10)
        if r.status_code not in [200, 204]:
            print("Erro Discord:", r.text)
    except Exception as e:
        print("Erro Discord:", e)


def send_alert(message: str):
    send_telegram(message)
    send_discord(message)

# ===============================
# BOT LOOP (SIMULADOR / BASE)
# ===============================

def bot_loop():
    print("Bot ativo - aguardando sinais...")

    while True:
        # ⚠️ Aqui futuramente entra:
        # - leitura Binance
        # - indicadores
        # - score
        # - ranking
        # - confirmação candle fechado

        time.sleep(30)

# ===============================
# SERVIDOR HTTP (KEEP ALIVE + PAINEL)
# ===============================

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "bot": "STONKS BR SIGNALS",
        "setup": CORE_SETUP["setup_name"]
    })

@app.route("/setup")
def setup():
    return jsonify(CORE_SETUP)

# ===============================
# STARTUP
# ===============================

def start_http():
    print(f"Servidor HTTP ativo na porta {APP_PORT}")
    app.run(host="0.0.0.0", port=APP_PORT)

if __name__ == "__main__":
    print("STONKS BR SIGNALS - BOT INICIADO")

    send_alert("🤖 STONKS BR SIGNALS iniciado e operacional")

    threading.Thread(target=bot_loop, daemon=True).start()
    start_http()



