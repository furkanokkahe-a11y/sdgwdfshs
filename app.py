import os
import requests
from flask import Flask, redirect

app = Flask(__name__)

TELEGRAM_TOKEN = "8469271411:AAEMaIvq-GrE2_col2-py9IuOO3oyahMxR0"
CHAT_ID = "7141351945"
HEDEF_URL = "https://x.com/hepkirildi/status/2065489119833157669?s=20"


def bildirim_gonder(mesaj):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Telegram credentials eksik.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mesaj}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print("Bildirim gönderilemedi:", e)


@app.route("/git")
def yonlendir():
    bildirim_gonder("⚠️ Kısaltılmış linkine birisi tıkladı!")
    return redirect(HEDEF_URL)


if __name__ == "__main__":
    app.run()
