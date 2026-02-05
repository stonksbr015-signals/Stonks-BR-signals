import os
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# ==============================
# CONFIG
# ==============================
PORT = int(os.environ.get("PORT", 10000))

# ==============================
# SERVIDOR HTTP (OBRIGATÓRIO PARA RENDER)
# ==============================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"STONKS BR SIGNALS ONLINE")

def start_http_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    print(f"Servidor HTTP ativo na porta {PORT}")
    server.serve_forever()

# ==============================
# BOT (LOOP PRINCIPAL)
# ==============================
def run_bot():
    print("STONKS BR SIGNALS - BOT INICIADO")
    while True:
        print("Bot ativo - aguardando sinais...")
        time.sleep(60)

# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    threading.Thread(target=start_http_server, daemon=True).start()
    run_bot()
