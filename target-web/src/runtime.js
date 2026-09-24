'use strict';
// ===========================================================================
// RUNTIME + PEMBUNGKUS HTML
// Pustaka bantu yang dipakai program .Jay hasil kompilasi.
// ===========================================================================

const RUNTIME_JS = `// ===== insJaY runtime v0.3 =====
const __ins = {
  _out: [],
  _wadah: {},
  ambil(n){ return Object.prototype.hasOwnProperty.call(this._wadah, n) ? this._wadah[n] : undefined; },
  simpan(n, v){ this._wadah[n] = v; return v; },
  _teks(v){
    if (typeof v === 'boolean') return v ? 'benar' : 'salah';
    if (v === undefined || v === null) return '';
    if (typeof v === 'number' && Number.isInteger(v)) return String(v);
    return String(v);
  },
  kata(v){ const s = this._teks(v); this._out.push(s); console.log(s); },
  panjang(v){ return (v === null || v === undefined) ? 0 : (v.length !== undefined ? v.length : 0); },
  benar(v){ return Boolean(v); },
  angka(v){ const n = Number(v); return Number.isNaN(n) ? 0 : n; },
  _lines: null, _li: 0,
  tanya(msg){
    if (typeof document !== 'undefined' && typeof window !== 'undefined' && typeof window.prompt === 'function') {
      return window.prompt(msg);
    }
    try {
      const fs = require('fs');
      if (this._lines === null) {
        let data = '';
        try { data = fs.readFileSync(0, 'utf8'); } catch (e) { data = ''; }
        this._lines = data.split('\\n');
      }
      process.stdout.write(msg + ' ');
      const l = this._lines[this._li++] || '';
      return l.replace(/\\r$/, '');
    } catch (e) { return ''; }
  },
  _doc(){ return (typeof document !== 'undefined') ? document : null; },
  _halaman(id){
    const d = this._doc(); if (!d) return null;
    let el = d.getElementById('ins-' + id);
    if (!el) {
      el = d.createElement('section');
      el.id = 'ins-' + id;
      el.className = 'ins-halaman';
      const app = d.getElementById('app') || d.body;
      app.appendChild(el);
    }
    return el;
  },
  halaman(id, judul){
    const d = this._doc(); if (!d) return;
    const el = this._halaman(id);
    if (el && !el.querySelector('.ins-judul-halaman')) {
      const h = d.createElement('h2');
      h.className = 'ins-judul-halaman';
      h.textContent = this._teks(judul);
      el.appendChild(h);
    }
  },
  _tambah(id, tag, teks){
    const d = this._doc(); const el = this._halaman(id); if (!d || !el) return null;
    const node = d.createElement(tag);
    node.textContent = this._teks(teks);
    el.appendChild(node);
    return node;
  },
  judul(id, teks){ this._tambah(id, 'h1', teks); },
  paragraf(id, teks){ this._tambah(id, 'p', teks); },
  isian(id, nama){
    const d = this._doc(); const el = this._halaman(id); if (!d || !el) return;
    const inp = d.createElement('input');
    inp.type = 'text';
    inp.className = 'ins-isian';
    inp.setAttribute('data-isian', nama);
    inp.placeholder = nama;
    el.appendChild(inp);
  },
  tombol(id, label, fn){
    const d = this._doc(); const el = this._halaman(id); if (!d || !el) return;
    const b = d.createElement('button');
    b.className = 'ins-tombol';
    b.textContent = this._teks(label);
    b.onclick = function(){ try { fn(); } catch (e) { console.error(e); } };
    el.appendChild(b);
  },
  jawaban(id, teks){
    const d = this._doc(); const el = this._halaman(id); if (!d || !el) return;
    let p = el.querySelector('.ins-jawaban');
    if (!p) { p = d.createElement('p'); p.className = 'ins-jawaban'; el.appendChild(p); }
    p.textContent = this._teks(teks);
  },
  gantiJawaban(id, teks){
    const d = this._doc(); const el = this._halaman(id); if (!d || !el) return;
    let p = el.querySelector('.ins-jawaban');
    if (!p) { p = d.createElement('p'); p.className = 'ins-jawaban'; el.appendChild(p); }
    p.textContent = this._teks(teks);
  },
  bacaIsian(nama){
    const d = this._doc(); if (!d) return this.ambil(nama) || '';
    const inp = d.querySelector('input[data-isian="' + nama + '"]');
    const v = inp ? inp.value : '';
    this.simpan(nama, v);
    return v;
  }
};
if (typeof globalThis !== 'undefined') { globalThis.__ins = __ins; }`;

const CSS = `:root{
  --ins-bg:#0f1220; --ins-ink:#eef1ff; --ins-muted:#9aa3c7;
  --ins-aksen:#7c5cff; --ins-aksen2:#22d3a7; --ins-garis:#2a3050;
}
*{box-sizing:border-box}
body{margin:0;min-height:100vh;background:radial-gradient(1200px 600px at 10% -10%,#241b4d 0%,transparent 60%),radial-gradient(900px 500px at 110% 10%,#123a34 0%,transparent 55%),var(--ins-bg);color:var(--ins-ink);font-family:"Segoe UI",Inter,system-ui,sans-serif;line-height:1.65;}
#app{max-width:760px;margin:0 auto;padding:48px 22px 90px;}
.ins-halaman{background:linear-gradient(180deg,rgba(255,255,255,.04),rgba(255,255,255,.01));border:1px solid var(--ins-garis);border-radius:18px;padding:28px 26px;box-shadow:0 20px 50px -30px rgba(0,0,0,.9);}
.ins-judul-halaman{margin:0 0 6px;font-size:.82rem;letter-spacing:.14em;text-transform:uppercase;color:var(--ins-aksen2);font-weight:600;}
.ins-halaman h1{font-size:1.7rem;margin:.15rem 0 .6rem;line-height:1.25}
.ins-halaman p{color:var(--ins-muted);margin:.35rem 0}
.ins-isian{width:100%;padding:12px 14px;margin:8px 0;border-radius:12px;border:1px solid var(--ins-garis);background:#0c0f1c;color:var(--ins-ink);font-size:1rem;outline:none;}
.ins-isian:focus{border-color:var(--ins-aksen);box-shadow:0 0 0 3px rgba(124,92,255,.22)}
.ins-tombol{margin:8px 8px 4px 0;padding:11px 20px;border:0;border-radius:12px;cursor:pointer;background:linear-gradient(135deg,var(--ins-aksen),#4f8bff);color:#fff;font-size:.98rem;font-weight:600;}
.ins-tombol:hover{filter:brightness(1.08)}
.ins-jawaban{margin-top:14px;padding:12px 14px;border-radius:12px;background:rgba(34,211,167,.1);border:1px solid rgba(34,211,167,.35);font-weight:600;}`;

function esc(v) {
  return String(v).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
}

/** Bungkus JS menjadi satu berkas HTML mandiri. */
function bungkusHTML(js, judul) {
  return `<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(judul)}</title>
<style>
${CSS}
</style>
</head>
<body>
<main id="app"></main>
<script>
${RUNTIME_JS}
</script>
<script>
${js}
</script>
</body>
</html>
`;
}

/** Ambil judul dari simpul Halaman pertama (bila berupa teks tetap). */
function judulHalaman(program) {
  for (const n of program.isi) {
    if (n.t === 'Halaman' && n.judul && n.judul.t === 'Teks') return n.judul.nilai;
  }
  return 'Aplikasi insJaY';
}

module.exports = { RUNTIME_JS, CSS, bungkusHTML, judulHalaman };
