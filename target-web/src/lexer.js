'use strict';
// ===========================================================================
// TAHAP 1 — LEXING
// Mengubah teks .Jay menjadi deretan token kalimat, plus lexer untuk ungkapan.
// ===========================================================================

/** Kesalahan bahasa dengan lokasi. */
class GalatInsJay extends Error {
  constructor(pesan, baris, berkas, potongan) {
    super(pesan);
    this.pesan = pesan;
    this.baris = baris;
    this.berkas = berkas;
    this.potongan = potongan;
  }
  format() {
    let lokasi = this.berkas || '';
    if (lokasi && this.baris) lokasi += ':' + this.baris;
    const ekor = lokasi ? ` (${lokasi})` : '';
    const petunjuk = this.potongan ? `\n        Kalimat: "${this.potongan}"` : '';
    return `${this.pesan}${ekor}${petunjuk}`;
  }
}

// Pola kalimat yang sah. URUTAN PENTING: yang lebih khusus lebih dahulu.
const POLA = [
  ['LET', /^aku\s+menyiapkan\s+wadah\s+bernama\s+(\w+)\s+yang\s+berisi\s+(.+)$/i],
  ['SET', /^aku\s+mengganti\s+isi\s+wadah\s+(\w+)\s+menjadi\s+(.+)$/i],
  ['ADD', /^aku\s+menambahkan\s+(.+?)\s+ke\s+dalam\s+wadah\s+(\w+)$/i],
  ['SUB', /^aku\s+mengurangi\s+wadah\s+(\w+)\s+dengan\s+(.+)$/i],
  ['BERKATA', /^aku\s+berkata:\s*(.+)$/i],
  ['JIKA', /^jika\s+(.+?)\s+maka$/i],
  ['KALAU_TIDAK', /^kalau\s+tidak$/i],
  ['SELAMA', /^selama\s+(.+?),\s*ulangi$/i],
  ['SELESAI', /^selesai$/i],
  ['KEBIASAAN', /^aku\s+membuat\s+kebiasaan\s+bernama\s+(\w+)(?:\s+yang\s+menerima\s+(.+))?$/i],
  ['PANGGIL', /^aku\s+memanggil\s+kebiasaan\s+(\w+)(?:\s+dengan\s+(.+))?$/i],
  ['KEMBALI', /^aku\s+mengembalikan\s+(.+)$/i],
  ['SAMBUNG', /^aku\s+menyambung\s+cerita\s+dari\s+"(.+)"$/i],
  ['TANYA', /^aku\s+bertanya:\s*(.+?)\s+ke\s+dalam\s+wadah\s+(\w+)$/i],
  ['HALAMAN', /^aku\s+menyiapkan\s+halaman\s+bernama\s+(\w+)\s+berjudul\s+(.+)$/i],
  ['JUDUL', /^aku\s+menaruh\s+judul\s+(.+?)\s+ke\s+dalam\s+halaman\s+(\w+)$/i],
  ['PARAGRAF', /^aku\s+menaruh\s+paragraf\s+(.+?)\s+ke\s+dalam\s+halaman\s+(\w+)$/i],
  ['ISIAN', /^aku\s+menaruh\s+kotak\s+isian\s+bernama\s+(\w+)\s+ke\s+dalam\s+halaman\s+(\w+)$/i],
  ['TOMBOL', /^aku\s+menaruh\s+tombol\s+(.+?)\s+yang\s+memanggil\s+kebiasaan\s+(\w+)\s+ke\s+dalam\s+halaman\s+(\w+)$/i],
  ['JAWABAN', /^aku\s+menaruh\s+jawaban\s+(.+?)\s+ke\s+dalam\s+halaman\s+(\w+)$/i],
  ['GANTI_JAWABAN', /^aku\s+mengubah\s+jawaban\s+di\s+halaman\s+(\w+)\s+menjadi\s+(.+)$/i],
  ['BACA_ISIAN', /^aku\s+membaca\s+kotak\s+isian\s+(\w+)\s+ke\s+dalam\s+wadah\s+(\w+)$/i],
  // --- v0.4: impor modul & ekspor fungsi (jembatan ke Node/npm) ---
  ['AMBIL', /^aku\s+mengambil\s+dari\s+"(.+)"\s+ke\s+dalam\s+wadah\s+(\w+)$/i],
  ['SERAHKAN', /^aku\s+menyerahkan\s+kebiasaan\s+(\w+)\s+kepada\s+dunia$/i],
];

/** Tahap Lexing utama: teks -> daftar token kalimat. */
function lex(teks, berkas) {
  const token = [];
  const barisSemua = teks.split(/\r?\n/);
  for (let i = 0; i < barisSemua.length; i++) {
    let t = barisSemua[i].trim();
    if (!t) continue;
    if (t.startsWith('//')) continue;
    if (t.startsWith('#')) {
      token.push({ jenis: 'BAB', baris: i + 1, berkas, teks: t, judul: t.replace(/^#\s*/, '') });
      continue;
    }
    if (t.endsWith('.')) t = t.slice(0, -1).trim();

    let ketemu = false;
    for (const [jenis, re] of POLA) {
      const m = t.match(re);
      if (m) {
        token.push({ jenis, baris: i + 1, berkas, teks: t, m });
        ketemu = true;
        break;
      }
    }
    if (!ketemu) {
      throw new GalatInsJay(
        'Kalimat ini tidak mengikuti alur cerita insJaY sehingga tidak bisa dipahami.',
        i + 1, berkas, t
      );
    }
  }
  return token;
}

// ---------------------------------------------------------------------------
// Lexer ungkapan
// ---------------------------------------------------------------------------
const FRASA = {
  PANJANG: 'panjang dari wadah',
  KEWADAH: 'angka dari wadah',
  HURUFKECIL: 'huruf kecil dari wadah',
  HURUFBESAR: 'huruf besar dari wadah',
  VAR: 'wadah',
  PANGGIL: 'hasil dari kebiasaan',
};

function lexUngkapan(s, berkas) {
  const toks = [];
  let i = 0;
  const galat = (p) => { throw new GalatInsJay(p, null, berkas); };
  while (i < s.length) {
    const c = s[i];
    if (/\s/.test(c)) { i++; continue; }
    if (c === '"') {
      const j = s.indexOf('"', i + 1);
      if (j < 0) galat('Tanda kutip pembuka tidak pernah ditutup.');
      toks.push({ t: 'teks', v: s.slice(i + 1, j) });
      i = j + 1; continue;
    }
    if (s.startsWith(FRASA.PANJANG, i)) {
      i += FRASA.PANJANG.length;
      const m = /^\s*(\w+)/.exec(s.slice(i));
      if (!m) galat("'panjang dari wadah' harus diikuti nama wadah.");
      toks.push({ t: 'panjang', nama: m[1] }); i += m[0].length; continue;
    }
    if (s.startsWith(FRASA.KEWADAH, i)) {
      i += FRASA.KEWADAH.length;
      const m = /^\s*(\w+)/.exec(s.slice(i));
      if (!m) galat("'angka dari wadah' harus diikuti nama wadah.");
      toks.push({ t: 'kewadah', nama: m[1] }); i += m[0].length; continue;
    }
    if (s.startsWith(FRASA.HURUFKECIL, i)) {
      i += FRASA.HURUFKECIL.length;
      const m = /^\s*(\w+)/.exec(s.slice(i));
      if (!m) galat("'huruf kecil dari wadah' harus diikuti nama wadah.");
      toks.push({ t: 'hurufkecil', nama: m[1] }); i += m[0].length; continue;
    }
    if (s.startsWith(FRASA.HURUFBESAR, i)) {
      i += FRASA.HURUFBESAR.length;
      const m = /^\s*(\w+)/.exec(s.slice(i));
      if (!m) galat("'huruf besar dari wadah' harus diikuti nama wadah.");
      toks.push({ t: 'hurufbesar', nama: m[1] }); i += m[0].length; continue;
    }
    if (s.startsWith(FRASA.VAR, i)) {
      i += FRASA.VAR.length;
      const m = /^\s*(\w+)/.exec(s.slice(i));
      if (!m) galat("'wadah' harus diikuti nama wadah.");
      toks.push({ t: 'var', nama: m[1] }); i += m[0].length; continue;
    }
    if (s.startsWith(FRASA.PANGGIL, i)) {
      i += FRASA.PANGGIL.length;
      const m = /^\s*(\w+)/.exec(s.slice(i));
      if (!m) galat("'hasil dari kebiasaan' harus diikuti nama kebiasaan.");
      toks.push({ t: 'panggil', nama: m[1] }); i += m[0].length; continue;
    }
    if ('+-*/%'.includes(c)) { toks.push({ t: 'op', v: c }); i++; continue; }
    if (c === '(') { toks.push({ t: 'lp' }); i++; continue; }
    if (c === ')') { toks.push({ t: 'rp' }); i++; continue; }
    if (c === ',') { toks.push({ t: 'comma' }); i++; continue; }

    let m = /^\d+\.\d+|^\d+/.exec(s.slice(i));
    if (m) {
      const v = m[0];
      toks.push({ t: 'angka', v: v.includes('.') ? parseFloat(v) : parseInt(v, 10) });
      i += v.length; continue;
    }
    m = /^[A-Za-z_]\w*/.exec(s.slice(i));
    if (m) { toks.push({ t: 'ident', v: m[0] }); i += m[0].length; continue; }
    galat(`Karakter '${c}' tidak dikenal dalam ungkapan.`);
  }
  return toks;
}

/** Pisah argumen pada koma di kedalaman teratas. */
function pisahArgumen(teks) {
  const hasil = [];
  let depth = 0, inStr = false, buf = '';
  for (const c of teks) {
    if (c === '"') inStr = !inStr;
    if (!inStr) {
      if (c === '(') depth++;
      else if (c === ')') depth--;
      else if (c === ',' && depth === 0) { hasil.push(buf.trim()); buf = ''; continue; }
    }
    buf += c;
  }
  if (buf.trim()) hasil.push(buf.trim());
  return hasil;
}

module.exports = { GalatInsJay, POLA, lex, lexUngkapan, pisahArgumen, FRASA };
