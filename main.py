import os
import time
import threading
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer

# ==================================================
# CONFIGURAÇÃO
# ==================================================
PORT = int(os.environ.get("PORT", 10000))

# ==================================================
# SERVIDOR HTTP (OBRIGATÓRIO NO RENDER FREE)
# ==================================================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"STONKS BR SIGNALS ONLINE")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

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
# DISCORD WEBHOOK
# ==================================================
def send_discord_message(text):
    webhook = os.environ.get("DISCORD_WEBHOOK_URL")

    if not webhook:
        print("Discord webhook não configurado")
        return

    payload = {
        "content": text
    }

    try:
        requests.post(webhook, json=payload, timeout=10)
        print("Mensagem enviada para o Discord")
    except Exception as e:
        print("Erro ao enviar Discord:", e)

# ==================================================
# BOT PRINCIPAL
# ==================================================
def run_bot():
    print("STONKS BR SIGNALS - BOT INICIADO")

    mensagem = "🚀 STONKS BR SIGNALS ONLINE 🚀"

    send_telegram_message(mensagem)
    send_discord_message(mensagem)

    while True:
        print("Bot ativo - aguardando sinais...")
        time.sleep(60)

# ==================================================
# MAIN
# ==================================================
if __name__ == "__main__":
    threading.Thread(target=start_http_server, daemon=True).start()
    run_bot()


