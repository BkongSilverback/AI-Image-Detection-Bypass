#!/usr/bin/env python3
"""DeAI Mobile: private, phone-friendly UI for scripts/deai.py.

Uses CPU light/medium mode without fake camera EXIF or automatic detector requests.
Images live only in temporary files, and the uploaded originals are never overwritten.
"""
from __future__ import annotations
from email import policy
from email.parser import BytesParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError

ROOT = Path(__file__).resolve().parent
ENGINE = ROOT / "scripts" / "deai.py"
MAX_BYTES = 20 * 1024 * 1024
MAX_PIXELS = 24_000_000
Image.MAX_IMAGE_PIXELS = MAX_PIXELS

PAGE = r"""<!doctype html><html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#101216">
<link rel="manifest" href="/manifest.webmanifest">
<title>DeAI Mobile — Image Studio</title>
<style>
:root{font-family:system-ui,-apple-system,Segoe UI,sans-serif;color-scheme:dark;--bg:#101216;--card:#1b1e23;--accent:#c9f579;--muted:#b0b6c1}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse 80% 17% at top,#313b26,transparent),var(--bg);color:white}
main{max-width:540px;margin:auto;padding:27px 18px 65px}h1{font-size:38px;letter-spacing:-.055em;margin:4px 0}h1 span,.eyebrow{color:var(--accent)}
.eyebrow{font-weight:850;letter-spacing:.18em;font-size:11px}p{line-height:1.55;color:var(--muted)}
.card{margin:22px 0;background:var(--card);border:1px solid #373d46;border-radius:20px;padding:18px}
.pick{display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;border:2px dashed #6a727b;border-radius:16px;min-height:175px;cursor:pointer;padding:18px;background:#131519}
.pick strong{margin-top:8px;font-size:18px;word-break:break-word}.pick small{color:var(--muted);margin-top:6px}
.pick svg{width:45px;height:45px;stroke:var(--accent)}
#file{position:absolute;opacity:0;width:1px;height:1px}
#preview{width:100%;max-height:320px;object-fit:contain;margin-top:14px;border-radius:13px;display:none;background:#282c32}
fieldset{border:0;padding:0;margin:22px 0}legend{font-size:15px;font-weight:850;margin-bottom:12px}
.options{display:grid;grid-template-columns:1fr 1fr;gap:10px}.option{padding:13px;border:1px solid #5d626a;border-radius:13px;background:#111317;cursor:pointer}
.option:has(input:checked){border:2px solid var(--accent);padding:12px;background:#292f22}
.option input{accent-color:var(--accent)}.option b{display:block;margin:5px 0}.option small{font-size:12px;line-height:1.45;color:var(--muted)}
button,a.download{display:flex;align-items:center;justify-content:center;min-height:56px;width:100%;border:0;border-radius:13px;padding:13px;text-align:center;font-size:17px;font-weight:800;text-decoration:none}
button{background:var(--accent);color:#101510;cursor:pointer}button:disabled{opacity:.6}
a.download{background:#f7f9f2;color:#181b15}
#status{margin-top:14px;text-align:center;font-size:14px;color:var(--muted);min-height:24px}
#status.error{color:#ff9d90}#result{display:none}
#resultImage{display:block;max-height:350px;width:100%;object-fit:contain;border-radius:13px;margin:12px 0;background:#14161a}
footer{font-size:12px;line-height:1.6;color:var(--muted)}footer strong{color:#fff}
</style></head><body><main>
<div class="eyebrow">PHONE-FRIENDLY IMAGE STUDIO</div>
<h1>DeAI <span>Mobile</span></h1>
<p>No terminal menus. Choose a picture, pick a setting, save the result.</p>
<section class="card"><form id="form">
<label class="pick" for="file">
<svg fill="none" viewBox="0 0 24 24" stroke-width="1.9"><path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M12 15V3m0 0 4.5 4.5M12 3 7.5 7.5"/></svg>
<strong id="filename">Choose an image</strong>
<small>Tap to pick a JPG, PNG or WebP from your phone</small>
</label>
<input id="file" type="file" name="file" accept="image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp" required>
<img id="preview" alt="Selected image preview">
<fieldset><legend>Processing strength</legend><div class="options">
<label class="option"><input type="radio" name="strength" value="light"><b>Light</b><small>Faster, subtle changes</small></label>
<label class="option"><input type="radio" name="strength" value="medium" checked><b>Medium</b><small>Stronger effects; may alter fine details</small></label>
</div></fieldset>
<button id="submit" type="submit">Process Image</button>
<div id="status" role="status" aria-live="polite">No image selected</div>
</form></section>
<section class="card" id="result">
<div class="eyebrow">PROCESSING COMPLETE</div><h2>Your picture is ready</h2>
<img id="resultImage" alt="Processed image">
<a id="download" class="download" href="#" download="deai_processed.png">↓ Save to My Phone</a>
</section>
<footer><strong>Important:</strong> This app runs in your GitHub Codespace, not offline on your phone. Keep the Codespace running and the forwarded port <strong>Private</strong>. The original is not overwritten. No fake camera metadata is added and no detector API is contacted. AI detector scores are not reliable proof of how art was created.</footer>
</main>
<script>
const file=document.getElementById('file'), preview=document.getElementById('preview');
const status=document.getElementById('status'), button=document.getElementById('submit');
const result=document.getElementById('result'), resultImage=document.getElementById('resultImage');
const download=document.getElementById('download');
let inputUrl=null, outputUrl=null;
const message=(s,error=false)=>{status.textContent=s;status.classList.toggle('error',error)};
file.addEventListener('change',()=>{
 const f=file.files[0];if(!f)return;
 document.getElementById('filename').textContent=f.name;
 message('Ready to process');result.style.display='none';
 if(inputUrl)URL.revokeObjectURL(inputUrl);
 inputUrl=URL.createObjectURL(f);preview.src=inputUrl;preview.style.display='block';
});
document.getElementById('form').addEventListener('submit',async e=>{
 e.preventDefault();if(!file.files.length){message('Please select an image.',true);return}
 result.style.display='none';button.disabled=true;button.textContent='Working…';
 message('Processing your image. Please wait.');
 let timer;let ctrl=new AbortController();
 try{
  timer=setTimeout(()=>ctrl.abort(),190000);
  const response=await fetch('/process',{method:'POST',body:new FormData(e.target),signal:ctrl.signal});
  if(!response.ok)throw new Error((await response.text()).slice(0,200));
  const blob=await response.blob();
  if(outputUrl)URL.revokeObjectURL(outputUrl);
  outputUrl=URL.createObjectURL(blob);
  resultImage.src=outputUrl;download.href=outputUrl;
  download.download='processed_'+file.files[0].name.replace(/\.(png|jpg|jpeg|webp)$/i,'')+'.png';
  result.style.display='block';message('Finished! Save your picture below.');
  result.scrollIntoView({behavior:'smooth',block:'start'});
 }catch(err){
  message(err.name==='AbortError'?'Timed out. Try a smaller image.':'Could not process image: '+err.message,true);
 }finally{clearTimeout(timer);button.disabled=false;button.textContent='Process Image'}
});
</script></body></html>"""

MANIFEST = b'{"name":"DeAI Mobile Image Studio","short_name":"DeAI","start_url":"/","display":"standalone","background_color":"#101216","theme_color":"#101216","icons":[{"src":"/icon.svg","sizes":"any","type":"image/svg+xml"}]}'
ICON = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 192 192"><rect width="192" height="192" rx="38" fill="#101216"/><rect x="14" y="14" width="164" height="164" rx="29" fill="#c9f579"/><path d="M46 125V67h43c41 0 41 58 0 58zm27-19h16c16 0 16-20 0-20H73zm56 19V67h19v58z" fill="#101216"/></svg>'


def unpack_form(content_type, raw):
    if not content_type.lower().startswith('multipart/form-data') or 'boundary=' not in content_type:
        raise ValueError('Please select an image.')
    header = b'Content-Type: ' + content_type.encode('latin-1') + b'\r\nMIME-Version: 1.0\r\n\r\n'
    form = BytesParser(policy=policy.default).parsebytes(header + raw)
    if not form.is_multipart():
        raise ValueError('Upload was incomplete.')
    parts = {}
    for item in form.iter_parts():
        name = item.get_param('name', header='content-disposition')
        if name in ('file', 'strength'):
            parts[name] = item.get_payload(decode=True)
    return parts


def run_engine(raw, strength):
    if strength not in ('light', 'medium'):
        raise ValueError('Choose Light or Medium.')
    if not raw or len(raw) > MAX_BYTES:
        raise ValueError('Image must be smaller than 20 MB.')
    if not ENGINE.is_file():
        raise RuntimeError('Missing original engine: scripts/deai.py')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(raw)) as im:
                if im.format not in ('PNG', 'JPEG', 'WEBP'):
                    raise ValueError('Choose a JPG, PNG or WebP.')
                im.verify()
            with Image.open(BytesIO(raw)) as im:
                if im.width * im.height > MAX_PIXELS:
                    raise ValueError('Image dimensions are too large.')
                im = ImageOps.exif_transpose(im)
                rgba = im.convert('RGBA')
                has_alpha = 'A' in im.getbands() or 'transparency' in im.info
                alpha = rgba.getchannel('A') if has_alpha else None
                flattened = Image.new('RGB', rgba.size, 'white')
                flattened.paste(rgba, mask=rgba.getchannel('A'))
    except (OSError, UnidentifiedImageError, Image.DecompressionBombWarning, Image.DecompressionBombError) as exc:
        raise ValueError('Could not open that image.') from exc
    with tempfile.TemporaryDirectory(prefix='deai_mobile_') as temp:
        source = Path(temp) / 'original.png'
        target = Path(temp) / 'processed.png'
        flattened.save(source, 'PNG')
        command = [sys.executable, str(ENGINE), str(source), '-o', str(target),
                   '--strength', strength, '--no-exif', '--no-check', '--no-purify', '--quiet']
        try:
            result = subprocess.run(command, cwd=ROOT, capture_output=True,
                                    text=True, errors='replace', timeout=175)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError('Processing timed out. Try a smaller image.') from exc
        if result.returncode != 0 or not target.is_file():
            details = (result.stderr or result.stdout or 'No details available.').strip()[-220:]
            raise RuntimeError('Engine error: ' + details)
        try:
            with Image.open(target) as im:
                processed = im.convert('RGB')
                if alpha is not None:
                    # Retain original transparency, approximated if output size changes.
                    processed = processed.convert('RGBA')
                    processed.putalpha(alpha.resize(processed.size, Image.Resampling.LANCZOS))
                output = BytesIO()
                processed.save(output, 'PNG')
                return output.getvalue()
        except OSError as exc:
            raise RuntimeError('Engine produced an unreadable image.') from exc


class Handler(BaseHTTPRequestHandler):
    server_version = 'DeAIMobile/1.0'
    def send(self, code, data, media_type):
        self.send_response(code)
        self.send_header('Content-Type', media_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = self.path.split('?', 1)[0]
        if url == '/':
            return self.send(200, PAGE.encode('utf-8'), 'text/html; charset=utf-8')
        if url == '/manifest.webmanifest':
            return self.send(200, MANIFEST, 'application/manifest+json')
        if url == '/icon.svg':
            return self.send(200, ICON, 'image/svg+xml')
        if url == '/health':
            return self.send(200 if ENGINE.is_file() else 503,
                             b'OK' if ENGINE.is_file() else b'Engine missing', 'text/plain')
        return self.send(404, b'Not found', 'text/plain')

    def do_POST(self):
        if self.path != '/process':
            return self.send(404, b'Not found', 'text/plain')
        try:
            size = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            return self.send(400, b'Invalid upload', 'text/plain')
        if not 0 < size <= MAX_BYTES + 1024 * 1024:
            return self.send(413, b'Image must be smaller than 20 MB.', 'text/plain')
        try:
            params = unpack_form(self.headers.get('Content-Type', ''), self.rfile.read(size))
            if 'file' not in params:
                raise ValueError('Choose an image.')
            strength = params.get('strength', b'medium').decode('utf-8', 'replace').strip()
            result = run_engine(params['file'], strength)
            return self.send(200, result, 'image/png')
        except ValueError as exc:
            return self.send(400, str(exc).encode(), 'text/plain; charset=utf-8')
        except Exception as exc:
            return self.send(500, str(exc).encode(), 'text/plain; charset=utf-8')


def main():
    port = int(os.environ.get('PORT', '8000'))
    if not ENGINE.is_file():
        print('WARNING: scripts/deai.py was not found in the project folder.', flush=True)
    httpd = ThreadingHTTPServer(('0.0.0.0', port), Handler)
    print('DeAI Mobile ready: port ' + str(port) + '. Keep the forwarded port PRIVATE.', flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == '__main__':
    main()
