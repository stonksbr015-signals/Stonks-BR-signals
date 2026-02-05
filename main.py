import os
import time
import threading
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler

# ===============================
# TELEGRAM
# ===============================
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
        print("Erro Telegram:", e)

# ===============================
# DISCORD
# ===============================
def send_discord_message(text):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")

    if not webhook_url:
        print("Discord não configurado")
        return

    payload = {
        "content": text
    }

    try:
        requests.post(webhook_url, json=payload, timeout=10)
        print("Mensagem enviada para o Discord")
    except Exception as e:
        print("Erro Discord:", e)

# ===============================
# HTTP KEEP ALIVE
# ===============================
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"STONKS BR SIGNALS ONLINE")

def start_http_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    print(f"Servidor HTTP ativo na porta {port}")
    server.serve_forever()

# ===============================
# BOT PRINCIPAL
# ===============================
def run_bot():
    print("STONKS BR SIGNALS - BOT INICIADO")

    start_message = "🚀 STONKS BR SIGNALS ONLINE 🚀"
    send_telegram_message(start_message)
    send_discord_message(start_message)

    last_price = None

    while True:
        try:
            response = requests.get(
                "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT",
                timeout=10
            )
            data = response.json()
            price = float(data["price"])

            if last_price is None:
                last_price = price
                print(f"Preço inicial BTC: {price}")
            else:
                change = ((price - last_price) / last_price) * 100

                if change >= 1:
                    msg = f"📈 BTC SUBINDO +{change:.2f}%\nPreço: ${price}"
                    send_telegram_message(msg)
                    send_discord_message(msg)
                    last_price = price

                elif change <= -1:
                    msg = f"📉 BTC CAINDO {change:.2f}%\nPreço: ${price}"
                    send_telegram_message(msg)
                    send_discord_message(msg)
                    last_price = price

            time.sleep(60)

        except Exception as e:
            print("Erro ao buscar preço:", e)
            time.sleep(60)





