import os
import requests
from flask import Flask, redirect, request, render_template_string

app = Flask(__name__)

TELEGRAM_TOKEN = "8469271411:AAEMaIvq-GrE2_col2-py9IuOO3oyahMxR0"
CHAT_ID = "7141351945"
HEDEF_URL = "https://x.com/hepkirildi/status/2065489119833157669?s=20"

HTML_SAYFA = """
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Sana Bir Şey Söylemek İstiyorum</title>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Lato:wght@300;400&display=swap" rel="stylesheet"/>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #1a0a0f;
      font-family: 'Lato', sans-serif;
      overflow: hidden;
      position: relative;
    }

    /* Yüzen kalpler */
    .kalpler {
      position: fixed;
      inset: 0;
      pointer-events: none;
      z-index: 0;
    }
    .kalp {
      position: absolute;
      bottom: -60px;
      font-size: 1.4rem;
      opacity: 0;
      animation: yukari-ucus linear infinite;
    }
    @keyframes yukari-ucus {
      0%   { transform: translateY(0) scale(0.8); opacity: 0; }
      10%  { opacity: 0.6; }
      90%  { opacity: 0.3; }
      100% { transform: translateY(-110vh) scale(1.2); opacity: 0; }
    }

    /* Arka plan parıltıları */
    body::before {
      content: '';
      position: fixed;
      inset: 0;
      background:
        radial-gradient(ellipse at 20% 50%, rgba(180,30,60,0.18) 0%, transparent 60%),
        radial-gradient(ellipse at 80% 20%, rgba(200,50,80,0.12) 0%, transparent 55%),
        radial-gradient(ellipse at 60% 80%, rgba(150,20,50,0.14) 0%, transparent 50%);
      pointer-events: none;
      z-index: 0;
    }

    .kart {
      position: relative;
      z-index: 1;
      background: rgba(30, 8, 16, 0.85);
      border: 1px solid rgba(220, 80, 100, 0.25);
      border-radius: 24px;
      padding: 50px 44px;
      width: 100%;
      max-width: 480px;
      box-shadow:
        0 0 0 1px rgba(220,80,100,0.08),
        0 20px 60px rgba(0,0,0,0.6),
        0 0 80px rgba(180,30,60,0.12);
      backdrop-filter: blur(12px);
    }

    .ust-ikon {
      text-align: center;
      font-size: 2.2rem;
      margin-bottom: 18px;
      animation: kalp-at 1.6s ease-in-out infinite;
    }
    @keyframes kalp-at {
      0%, 100% { transform: scale(1); }
      50% { transform: scale(1.15); }
    }

    h2 {
      color: #f2d0d8;
      font-family: 'Playfair Display', serif;
      font-size: 1.55rem;
      font-weight: 700;
      text-align: center;
      margin-bottom: 8px;
      letter-spacing: 0.3px;
    }

    p.alt {
      color: rgba(220,150,165,0.65);
      font-size: 0.88rem;
      text-align: center;
      margin-bottom: 32px;
      font-weight: 300;
      font-style: italic;
    }

    textarea {
      width: 100%;
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(220,80,100,0.22);
      border-radius: 14px;
      color: #f5dce0;
      font-family: 'Lato', sans-serif;
      font-size: 0.95rem;
      font-weight: 300;
      padding: 16px;
      resize: vertical;
      min-height: 140px;
      outline: none;
      transition: border-color 0.3s, box-shadow 0.3s;
      line-height: 1.6;
    }
    textarea::placeholder { color: rgba(220,150,165,0.4); }
    textarea:focus {
      border-color: rgba(220,80,100,0.55);
      box-shadow: 0 0 0 3px rgba(180,30,60,0.12);
    }

    button {
      margin-top: 18px;
      width: 100%;
      padding: 14px;
      background: linear-gradient(135deg, #c0394f 0%, #8b1a2e 100%);
      color: #ffe4ea;
      font-family: 'Playfair Display', serif;
      font-size: 1rem;
      font-weight: 700;
      letter-spacing: 0.5px;
      border: none;
      border-radius: 14px;
      cursor: pointer;
      transition: opacity 0.2s, transform 0.15s, box-shadow 0.2s;
      box-shadow: 0 4px 20px rgba(180,30,60,0.35);
    }
    button:hover {
      opacity: 0.9;
      transform: translateY(-1px);
      box-shadow: 0 8px 28px rgba(180,30,60,0.45);
    }
    button:active { transform: translateY(0); }

    .ayirici {
      text-align: center;
      color: rgba(220,80,100,0.3);
      font-size: 0.8rem;
      margin-top: 22px;
      letter-spacing: 2px;
    }

    .mesaj-ok {
      margin-top: 18px;
      background: rgba(180,30,60,0.15);
      border: 1px solid rgba(220,80,100,0.3);
      color: #f5a0b0;
      border-radius: 12px;
      padding: 13px 16px;
      font-size: 0.9rem;
      text-align: center;
      display: {{ 'block' if basarili else 'none' }};
      font-style: italic;
    }
    .mesaj-hata {
      margin-top: 18px;
      background: rgba(80,20,20,0.4);
      border: 1px solid rgba(180,60,60,0.35);
      color: #f87171;
      border-radius: 12px;
      padding: 13px 16px;
      font-size: 0.9rem;
      text-align: center;
      display: {{ 'block' if hata else 'none' }};
    }
  </style>
</head>
<body>

  <!-- Yüzen kalpler -->
  <div class="kalpler" id="kalpler"></div>

  <div class="kart">
    <div class="ust-ikon">🌹</div>
    <h2>Nasılsın yavrum? Hazır mısın? İyi misin?</h2>
    <form method="POST" action="/mesaj">
      <textarea name="mesaj" placeholder="Kalbindekini buraya döküver..." required>{{ onceki_mesaj }}</textarea>
      <button type="submit">💌 &nbsp;Gönder</button>
    </form>
    <div class="mesaj-ok">🌸 Mesajın kalbe ulaştı...</div>
    <div class="mesaj-hata">✗ Bir hata oluştu, tekrar dene.</div>
    <p class="ayirici">· · · ♡ · · ·</p>
  </div>

  <script>
    const emojiler = ['❤️','🌹','💕','✨','🌸','💫','🥀','💗'];
    const kont = document.getElementById('kalpler');
    function kalp_ekle() {
      const el = document.createElement('span');
      el.className = 'kalp';
      el.textContent = emojiler[Math.floor(Math.random() * emojiler.length)];
      el.style.left = Math.random() * 100 + 'vw';
      const sure = 6 + Math.random() * 8;
      el.style.animationDuration = sure + 's';
      el.style.animationDelay = Math.random() * 4 + 's';
      el.style.fontSize = (0.9 + Math.random() * 1.2) + 'rem';
      kont.appendChild(el);
      setTimeout(() => el.remove(), (sure + 4) * 1000);
    }
    for (let i = 0; i < 14; i++) setTimeout(kalp_ekle, i * 600);
    setInterval(kalp_ekle, 1800);
  </script>
</body>
</html>
"""


def bildirim_gonder(mesaj):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Telegram credentials eksik.")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mesaj}
    try:
        r = requests.post(url, json=payload, timeout=5)
        return r.status_code == 200
    except Exception as e:
        print("Bildirim gönderilemedi:", e)
        return False


@app.route("/")
def ana_sayfa():
    return render_template_string(HTML_SAYFA, basarili=False, hata=False, onceki_mesaj="")


@app.route("/mesaj", methods=["POST"])
def mesaj_al():
    metin = request.form.get("mesaj", "").strip()
    if not metin:
        return render_template_string(HTML_SAYFA, basarili=False, hata=True, onceki_mesaj="")
    basarili = bildirim_gonder(f"📩 Yeni mesaj:\n\n{metin}")
    return render_template_string(
        HTML_SAYFA,
        basarili=basarili,
        hata=not basarili,
        onceki_mesaj="" if basarili else metin,
    )


@app.route("/git")
def yonlendir():
    bildirim_gonder("⚠️ Kısaltılmış linkine birisi tıkladı!")
    return redirect(HEDEF_URL)


if __name__ == "__main__":
    app.run()
