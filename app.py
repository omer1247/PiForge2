from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from pathlib import Path
import json, threading, time, os

try:
    import mpmath
except ImportError:
    raise SystemExit("mpmath kurulu degil. BASLA.bat dosyasini yeniden calistir.")

HOST, PORT = "0.0.0.0", int(os.environ.get("PORT", "8000"))
MAX_DIGITS = int(os.environ.get("MAX_DIGITS", "2000000"))
SERVER_MAX_DIGITS = int(os.environ.get("SERVER_MAX_DIGITS", str(MAX_DIGITS)))
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results"
OUT.mkdir(exist_ok=True)
LOCK = threading.Lock()
STATE = {"running": False, "requested": 0, "completed_digits": 0, "progress": 0, "elapsed": 0.0,
         "status": "Hazir", "error": None, "filename": None}

PAGE = r'''<!doctype html>
<html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PiForge | Pi Calculation Lab</title>
<style>
:root{color-scheme:dark;--bg:#080b10;--panel:#111722;--line:#263244;--text:#edf4ff;--muted:#94a3b8;--green:#71f5b5;--cyan:#64d9ff;--red:#ff7777}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 20% 0%,#142532 0,transparent 40%),var(--bg);color:var(--text);font:15px/1.5 system-ui,Segoe UI,sans-serif}
.wrap{max-width:1180px;margin:auto;padding:28px 20px 50px}.top{display:flex;justify-content:space-between;align-items:center;gap:18px;flex-wrap:wrap;margin-bottom:24px}
.brand{display:flex;align-items:center;gap:13px}.logo{display:grid;place-items:center;width:50px;height:50px;border:1px solid #38634f;border-radius:15px;background:#10251e;color:var(--green);font-size:27px;font-weight:800}
h1{font-size:24px;margin:0}.sub{color:var(--muted);font-size:13px}.badge{border:1px solid var(--line);border-radius:99px;padding:7px 12px;color:var(--green);font-size:12px}
.grid{display:grid;grid-template-columns:1.1fr .9fr;gap:18px}.card{background:linear-gradient(145deg,#121a26,#0d131c);border:1px solid var(--line);border-radius:18px;padding:22px;box-shadow:0 18px 60px #0002}.card h2{font-size:16px;margin:0 0 16px}.hero{grid-column:1/-1;min-height:210px;overflow:hidden}.eyebrow{color:var(--green);font-size:11px;letter-spacing:1.6px;text-transform:uppercase;font-weight:700}
.pi{font:clamp(21px,3vw,35px)/1.4 ui-monospace,Consolas,monospace;overflow-wrap:anywhere;word-break:break-word;margin-top:14px}.hint{color:var(--muted);font-size:12px;margin-top:12px}
label{display:block;color:#c4d0e0;font-size:13px;margin-bottom:7px}input{width:100%;background:#080d14;border:1px solid #344154;color:var(--text);border-radius:10px;padding:12px 13px;font:inherit;outline:none}input:focus{border-color:var(--green)}
.row,.searchrow{display:grid;grid-template-columns:1fr auto;gap:10px;align-items:end}.btn{border:0;border-radius:10px;background:var(--green);color:#06120d;font-weight:800;padding:12px 16px;font:inherit;cursor:pointer;white-space:nowrap}.btn:disabled{opacity:.5;cursor:wait}.btn.secondary{background:#1b2939;border:1px solid #33445b;color:var(--text)}.btnrow{display:flex;gap:9px;flex-wrap:wrap;margin-top:14px}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.stat{background:#0a1018;border:1px solid #202c3b;border-radius:12px;padding:14px}.label{color:var(--muted);font-size:11px}.value{font-size:22px;font-weight:750;margin-top:5px}.green{color:var(--green)}
.track{height:8px;border-radius:20px;background:#202a38;overflow:hidden;margin-top:14px}.bar{height:100%;width:0;background:linear-gradient(90deg,var(--green),var(--cyan));transition:width .25s}
.result{margin-top:13px;color:var(--muted);font-size:13px;overflow-wrap:anywhere}.error{color:var(--red)}.notice{margin-top:12px;padding:11px 13px;border:1px solid #4a4024;background:#211c10;color:#e6d4a0;border-radius:10px;font-size:12px}.foot{margin-top:18px;color:#75849a;font-size:12px;text-align:center}
@media(max-width:780px){.grid{grid-template-columns:1fr}.hero{grid-column:auto}.stats{grid-template-columns:1fr}.row,.searchrow{grid-template-columns:1fr}.btn{width:100%}}
</style></head><body><div class="wrap">
<header class="top"><div class="brand"><div class="logo">π</div><div><h1>PiForge</h1><div class="sub">Browser + server computation lab · v2.0</div></div></div><div class="badge">● TARAYICI + SUNUCU MODU</div></header>
<main class="grid">
<section class="card hero"><div class="eyebrow">Pi sabiti · canlı sonuç</div><div class="pi" id="piPreview">3.14159265358979323846264338327950288419716939937510…</div><div class="hint" id="previewHint">Örnek gösterim. Hesaplama başlayınca gerçek sonuç görünür.</div></section>
<section class="card"><h2>⚙ Hesaplama motoru</h2><label for="engine">Hesaplama nerede yapılsın?</label><select id="engine" style="width:100%;background:#080d14;border:1px solid #344154;color:var(--text);border-radius:10px;padding:12px 13px;font:inherit;margin-bottom:14px"><option value="browser">Bu tarayıcıda (ziyaretçinin bilgisayarı)</option><option value="server">PiForge sunucusunda</option></select><label for="digits">Ondalık basamak sayısı</label><div class="row"><input id="digits" type="number" min="10" max="2000000" value="10000"><button class="btn" id="start">Hesapla ↗</button></div>
<div class="btnrow"><button class="btn secondary preset" data-n="10000">10 bin</button><button class="btn secondary preset" data-n="100000">100 bin</button><button class="btn secondary preset" data-n="1000000">1 milyon</button></div>
<div class="notice">Tarayıcı modu ziyaretçinin bilgisayarını kullanır. Sunucu modu sitenin kaynaklarını kullanır. Büyük hesaplamalar cihazı yavaşlatabilir. Sunucu modu için yayınlanan sunucunun limiti ayrıca uygulanır.</div><div class="result" id="status">Durum: Hazır</div></section>
<section class="card"><h2>📈 Performans paneli</h2><div class="stats"><div class="stat"><div class="label">DURUM</div><div class="value green" id="progress">0%</div></div><div class="stat"><div class="label">GEÇEN SÜRE</div><div class="value" id="elapsed">0.00 s</div></div><div class="stat"><div class="label">HESAPLANAN BASAMAK</div><div class="value" id="count">0 / 0</div></div></div><div class="track"><div class="bar" id="bar"></div></div><div class="result" id="speed">Hız: henüz ölçülmedi</div></section>
<section class="card"><h2>🔎 Basamak dizisi ara</h2><label for="needle">Aranacak sayı dizisi (ör. 123456)</label><div class="searchrow"><input id="needle" class="mono" inputmode="numeric" placeholder="Sayı dizisini yaz"><button class="btn secondary" id="search">Ara</button></div><div class="result" id="searchResult">Arama, hesaplama tamamlandıktan sonra kullanılabilir.</div></section>
<section class="card"><h2>💾 Sonucu dışa aktar</h2><div class="sub">Tam sonuç results klasörüne kaydedilir. İstersen ayrıca TXT indirebilirsin.</div><div class="btnrow"><button class="btn secondary" id="download" disabled>TXT indir</button><button class="btn secondary" id="copy" disabled>Sonucu kopyala</button></div><div class="result" id="saved">Henüz dosya oluşturulmadı.</div></section>
</main><div class="foot">PiForge · Tarayıcı modu JavaScript BigInt, sunucu modu Python + mpmath kullanır.</div></div>
<script>
let currentDigits="", resultLoaded=false, browserWorker=null, startedAt=0, browserRequested=0;
const $=id=>document.getElementById(id);
function setStatus(text,error=false){$('status').textContent='Durum: '+text;$('status').className='result'+(error?' error':'')}
function resetResult(){currentDigits='';resultLoaded=false;$('download').disabled=true;$('copy').disabled=true;$('searchResult').textContent='Arama, hesaplama tamamlandıktan sonra kullanılabilir.'}
function stopBrowserWorker(){if(browserWorker){browserWorker.terminate();browserWorker=null}}
async function poll(){try{
 const r=await fetch('/api/status');const s=await r.json();
 if($('engine').value==='server'){
  $('progress').textContent=s.running?'Hesaplanıyor · '+s.progress+'%':s.progress+'%';$('bar').style.width=s.progress+'%';$('elapsed').textContent=(s.elapsed||0).toFixed(2)+' s';$('count').textContent=(s.completed_digits||0).toLocaleString('tr-TR')+' / '+(s.requested||0).toLocaleString('tr-TR');
  $('speed').textContent=s.progress===100?'Hız: yaklaşık '+Math.round((s.requested||0)/Math.max(s.elapsed,.001)).toLocaleString('tr-TR')+' basamak/s':(s.running?'Sunucu aşaması: '+(s.completed_digits||0).toLocaleString('tr-TR')+' / '+(s.requested||0).toLocaleString('tr-TR')+' basamak':'Sunucu hazır');$('start').disabled=Boolean(s.running);
  if(s.progress===100&&!s.running&&!resultLoaded&&s.requested>0){const rr=await fetch('/api/result');const d=await rr.json();currentDigits=d.digits||'';resultLoaded=Boolean(currentDigits);if(currentDigits){$('piPreview').textContent=currentDigits.length>180?currentDigits.slice(0,180)+'…':currentDigits;$('previewHint').textContent='Sonuç hazır · '+s.requested.toLocaleString('tr-TR')+' ondalık basamak';$('download').disabled=false;$('copy').disabled=false;$('saved').textContent='Sunucuda kaydedildi: '+(d.filename||'pi_digits.txt');}}
  if(s.error)setStatus('Hata: '+s.error,true);else if(s.status)setStatus(s.status);
 }
}catch(e){}}
$('start').onclick=async()=>{
 const n=Number($('digits').value),engine=$('engine').value;
 const max=engine==='browser'?100000:Number(document.body.dataset.serverMax||2000000);
 if(!Number.isInteger(n)||n<10||n>max){setStatus('10 ile '+max.toLocaleString('tr-TR')+' arasında tam sayı gir.',true);return}
 stopBrowserWorker();resetResult();browserRequested=n;startedAt=performance.now();$('start').disabled=true;$('bar').style.width='0%';$('progress').textContent='Hesaplanıyor · 0%';$('elapsed').textContent='0.00 s';$('count').textContent='0 / '+n.toLocaleString('tr-TR');$('speed').textContent='Hesaplama başlatılıyor…';
 if(engine==='browser'){
  setStatus('Tarayıcıda hesaplanıyor…');
  const workerCode=`
  function isqrt(n){if(n<2n)return n;let x=1n<<BigInt(Math.ceil(n.toString(2).length/2));while(true){let y=(x+n/x)>>1n;if(y>=x)return x;x=y}}
  onmessage=(ev)=>{const n=ev.data.digits;try{const guard=12, scale=10n**BigInt(n+guard);let a=scale,b=isqrt(scale*scale/2n),t=scale/4n,p=1n;const iterations=Math.ceil(Math.log2(n))+2;for(let i=0;i<iterations;i++){const an=(a+b)>>1n;const bn=isqrt(a*b);const diff=a-an;t=t-(p*diff*diff)/scale;a=an;b=bn;p*=2n;const estimate=Math.min(n,Math.max(1,Math.floor(2**(i+1))));postMessage({type:'progress',progress:Math.min(99,Math.floor((i+1)*100/iterations)),completed:estimate,requested:n,iteration:i+1,iterations});}const piScaled=((a+b)*(a+b))/(4n*t);let raw=piScaled.toString().padStart(n+guard+1,'0');const result=raw.slice(0,raw.length-guard- n)+'.'+raw.slice(raw.length-guard-n,raw.length-guard);const clean=result.slice(0,n+2);postMessage({type:'done',digits:clean,requested:n});}catch(e){postMessage({type:'error',error:String(e)})}};`;
  browserWorker=new Worker(URL.createObjectURL(new Blob([workerCode],{type:'text/javascript'})));
  browserWorker.onmessage=(ev)=>{const d=ev.data;if(d.type==='progress'){$('progress').textContent='Hesaplanıyor · '+d.progress+'%';$('bar').style.width=d.progress+'%';$('elapsed').textContent=((performance.now()-startedAt)/1000).toFixed(2)+' s';$('count').textContent='≈ '+d.completed.toLocaleString('tr-TR')+' / '+n.toLocaleString('tr-TR');$('speed').textContent='Tarayıcı aşaması '+d.iteration+'/'+d.iterations+' · basamak sayısı yaklaşık';setStatus('Tarayıcıda hesaplanıyor…');}else if(d.type==='done'){currentDigits=d.digits;resultLoaded=true;$('progress').textContent='100%';$('bar').style.width='100%';$('elapsed').textContent=((performance.now()-startedAt)/1000).toFixed(2)+' s';$('count').textContent=n.toLocaleString('tr-TR')+' / '+n.toLocaleString('tr-TR');$('speed').textContent='Tarayıcı hesaplaması tamamlandı';$('piPreview').textContent=currentDigits.length>180?currentDigits.slice(0,180)+'…':currentDigits;$('previewHint').textContent='Tarayıcıda hesaplandı · '+n.toLocaleString('tr-TR')+' ondalık basamak';$('download').disabled=false;$('copy').disabled=false;$('saved').textContent='Sonuç bu tarayıcıda hazır. Sunucuya kaydedilmedi.';setStatus('Tamamlandı (tarayıcı)');$('start').disabled=false;stopBrowserWorker();}else if(d.type==='error'){setStatus('Tarayıcı hesaplama hatası: '+d.error,true);$('start').disabled=false;stopBrowserWorker();}};
  browserWorker.postMessage({digits:n});
 }else{
  try{const r=await fetch('/api/calculate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({digits:n})});const d=await r.json();if(!r.ok)throw Error(d.error||'İstek başarısız');setStatus('Sunucuda hesaplanıyor…');}catch(e){setStatus(e.message,true);$('start').disabled=false;return}
  // poll() reenables the button when the server task finishes.
 }
};
document.querySelectorAll('.preset').forEach(b=>b.onclick=()=>$('digits').value=b.dataset.n);
$('engine').onchange=()=>{const browser=$('engine').value==='browser';$('digits').max=browser?100000:2000000;$('digits').value=Math.min(Number($('digits').value)||10000,browser?100000:2000000);setStatus(browser?'Tarayıcı modu seçildi.':'Sunucu modu seçildi.');};
$('search').onclick=()=>{const q=$('needle').value.trim();if(!/^\d+$/.test(q)){$('searchResult').textContent='Yalnızca rakam gir.';return}if(!currentDigits){$('searchResult').textContent='Önce hesaplama tamamla.';return}const i=currentDigits.indexOf(q);$('searchResult').textContent=i<0?'Bulunamadı.':`Bulundu! Başlangıçtan ${i.toLocaleString('tr-TR')} karakter sonra.`;};
$('download').onclick=()=>{if(!currentDigits)return;const b=new Blob([currentDigits+'\n'],{type:'text/plain;charset=utf-8'});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='pi_digits.txt';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);};
$('copy').onclick=async()=>{if(!currentDigits)return;try{await navigator.clipboard.writeText(currentDigits);$('saved').textContent='Sonuç panoya kopyalandı.'}catch(e){$('saved').textContent='Panoya erişilemedi; TXT indir seçeneğini kullan.'}};
setInterval(poll,1000);poll();
</script></body></html>'''

def worker(n):
    start = time.perf_counter()
    with LOCK:
        STATE.update(running=True, requested=n, completed_digits=0, progress=0, elapsed=0.0,
                     status=f"Hesaplanıyor: 0 / {n:,} basamak", error=None, filename=None)
    try:
        # Calculate at increasing precision checkpoints so the UI can show
        # the latest completed precision milestone instead of a fake live counter.
        checkpoints = []
        step = min(1000, n)
        while step < n:
            checkpoints.append(step)
            step *= 4
        checkpoints.append(n)
        result = None
        for checkpoint in checkpoints:
            mpmath.mp.dps = checkpoint + 10
            text_pi = mpmath.nstr(mpmath.pi, checkpoint + 10)
            if checkpoint == n:
                integer, frac = text_pi.split(".", 1)
                result = integer + "." + (frac + "0" * n)[:n]
            elapsed_now = time.perf_counter() - start
            with LOCK:
                STATE.update(completed_digits=checkpoint,
                             progress=min(99, int(checkpoint * 100 / n)),
                             elapsed=elapsed_now,
                             status=f"Hesaplanıyor: {checkpoint:,} / {n:,} basamak aşaması")
        filename = OUT / f"pi_{n}_digits.txt"
        filename.write_text(result + "\n", encoding="ascii")
        elapsed = time.perf_counter() - start
        # Publish the result before marking the task complete to avoid a polling race.
        global LAST_RESULT
        LAST_RESULT = result
        with LOCK:
            STATE.update(running=False, completed_digits=n, progress=100, elapsed=elapsed,
                         status="Tamamlandı", filename=str(filename), error=None)
    except Exception as exc:
        with LOCK:
            STATE.update(running=False, status="Hata", error=str(exc),
                         elapsed=time.perf_counter() - start)

LAST_RESULT = ""

class Handler(BaseHTTPRequestHandler):
    def send_data(self, code, body, content_type="application/json; charset=utf-8"):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            self.send_data(200, PAGE.replace("<body>", f"<body data-server-max=\"{min(MAX_DIGITS, SERVER_MAX_DIGITS)}\">"), "text/html; charset=utf-8")
        elif path == "/api/status":
            with LOCK: snapshot = dict(STATE)
            self.send_data(200, json.dumps(snapshot, ensure_ascii=False))
        elif path == "/api/result":
            with LOCK:
                data = {"digits": LAST_RESULT, "filename": STATE.get("filename")}
            self.send_data(200, json.dumps(data, ensure_ascii=False))
        else:
            self.send_data(404, json.dumps({"error": "Bulunamadi"}))
    def do_POST(self):
        if urlparse(self.path).path != "/api/calculate":
            self.send_data(404, json.dumps({"error": "Bulunamadi"})); return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            n = int(body.get("digits", 0))
            if not 10 <= n <= min(MAX_DIGITS, SERVER_MAX_DIGITS):
                limit = min(MAX_DIGITS, SERVER_MAX_DIGITS)
                self.send_data(400, json.dumps({"error": f"Sunucu basamak limiti 10 ile {limit} arasinda olmali."})); return
            with LOCK:
                if STATE["running"]:
                    self.send_data(409, json.dumps({"error": "Bir hesaplama zaten devam ediyor."})); return
                STATE.update(running=True, requested=n, completed_digits=0, progress=0, elapsed=0.0,
                             status=f"Hesaplanıyor: 0 / {n:,} basamak", error=None, filename=None)
            global LAST_RESULT
            LAST_RESULT = ""
            threading.Thread(target=worker, args=(n,), daemon=True).start()
            self.send_data(202, json.dumps({"ok": True, "digits": n}))
        except Exception as exc:
            self.send_data(400, json.dumps({"error": str(exc)}))
    def log_message(self, fmt, *args): pass

if __name__ == "__main__":
    print("=" * 50)
    print("PiForge - Pi hesaplama laboratuvari")
    print(f"Tarayicida ac: http://127.0.0.1:{PORT}")
    print("Durdurmak icin Ctrl+C")
    print("=" * 50)
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    try: server.serve_forever()
    except KeyboardInterrupt: print("\\nPiForge durduruldu.")
    finally: server.server_close()
