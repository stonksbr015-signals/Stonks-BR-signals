import os
import time
import threading
import requests
import numpy as np
from http.server import HTTPServer, BaseHTTPRequestHandler

print("STONKS BR SIGNALS - BOT INICIADO")

# ==================================================
# TELEGRAM
# ==================================================
def send_telegram_message(text):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("Telegram não configurado")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }

    try:
        requests.post(url, json=payload, timeout=10)
        print("Mensagem enviada para o Telegram")
    except Exception as e:
        print("Erro ao enviar Telegram:", e)

# ==================================================
# HTTP SERVER (KEEP ALIVE)
# ==================================================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"STONKS BR SIGNALS ONLINE")

def start_http_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("", port), HealthHandler)
    print(f"Servidor HTTP ativo na porta {port}")
    server.serve_forever()

# ==================================================
# BINANCE FUTURES DATA
# ==================================================
BINANCE_FUTURES_URL = "https://fapi.binance.com/fapi/v1/klines"

def get_klines(symbol, interval, limit=100):
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    try:
        r = requests.get(BINANCE_FUTURES_URL, params=params, timeout=10)
        return r.json()
    except Exception as e:
        print("Erro Binance:", e)
        return []

# ==================================================
# INDICADORES
# ==================================================
def calculate_ema(prices, period):
    return np.mean(prices[-period:])

def calculate_rsi(prices, period=14):
    deltas = np.diff(prices)
    gains = deltas[deltas > 0].sum() / period if len(deltas[deltas > 0]) > 0 else 0
    losses = -deltas[deltas < 0].sum() / period if len(deltas[deltas < 0]) > 0 else 0
    if losses == 0:
        return 100
    rs = gains / losses
    return 100 - (100 / (1 + rs))

def calculate_bollinger(prices, period=20):
    sma = np.mean(prices[-period:])
    std = np.std(prices[-period:])
    return sma + 2 * std, sma - 2 * std

# ==================================================
# ANÁLISE DE SINAL
# ==================================================
def analyze_symbol(symbol):
    klines = get_klines(symbol, "15m")
    if not klines or len(klines) < 50:
        return None

    closes = np.array([float(k[4]) for k in klines])

    ema9 = calculate_ema(closes, 9)
    ema21 = calculate_ema(closes, 21)
    rsi = calculate_rsi(closes)
    bb_upper, bb_lower = calculate_bollinger(closes)

    score = 0

    if ema9 > ema21:
        score += 30
    if rsi > 55:
        score += 30
    if bb_lower < closes[-1] < bb_upper:
        score += 20

    direction = "LONG" if ema9 > ema21 else "SHORT"

    return {
        "symbol": symbol,
        "direction": direction,
        "score": score,
        "price": closes[-1]
    }

# ==================================================
# CONFIG
# ==================================================
SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "SOLUSDT",
    "XRPUSDT"
]

# ==================================================
# BOT LOOP
# ==================================================
def run_bot():
    send_telegram_message("🚀 STONKS BR SIGNALS ONLINE 🚀")

    while True:
        results = []

        for symbol in SYMBOLS:
            analysis = analyze_symbol(symbol)
            if analysis:
                results.append(analysis)

        top3 = sorted(results, key=lambda x: x["score"], reverse=True)[:3]

        for s in top3:
            msg = (
                f"📊 {s['symbol']}\n"
                f"Direção: {s['direction']}\n"
                f"Score: {s['score']}\n"
                f"Preço: {s['price']}\n"
                f"TP: 2% | SL: 1%"
            )
            send_telegram_message(msg)

        print("Ciclo concluído. Aguardando próximo candle...")
        time.sleep(900)  # 15 minutos

# ==================================================
# START
# ==================================================
if __name__ == "__main__":
    threading.Thread(target=start_http_server, daemon=True).start()
    run_bot()





