import os
import time
import requests
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "STONKS BR SIGNALS ONLINE", 200


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


def run_bot():
    print("STONKS BR SIGNALS - BOT INICIADO")
    send_telegram_message("🚀 STONKS BR SIGNALS ONLINE 🚀")

    while True:
        print("Bot ativo - aguardando sinais...")
        time.sleep(60)


if __name__ == "__main__":
    import threading

    threading.Thread(target=run_bot, daemon=True).start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

