import os
import time
import threading
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler

print("STONKS BR SIGNALS - BOT INICIADO")

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
        print("Erro ao enviar Telegram:", e)

# ===============================
# HTTP SERVER (KEEP ALIVE)
# ===============================
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

# ===============================
# BOT LOOP
# ===============================
def run_bot():
    send_telegram_message("🚀 STONKS BR SIGNALS ONLINE 🚀")

    while True:
        print("Bot ativo - aguardando sinais...")
        time.sleep(60)

# ===============================
# START
# ===============================
if __name__ == "__main__":
    threading.Thread(target=start_http_server, daemon=True).start()
    run_bot()




