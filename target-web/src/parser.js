'use strict';





const { GalatInsJay, lexUngkapan, pisahArgumen } = require('./lexer');

const PERBANDINGAN = [
  ['tidak sama dengan', '!=='],
  ['lebih besar atau sama dengan', '>='],
  ['lebih kecil atau sama dengan', '<='],
  ['sama dengan', '==='],
  ['lebih besar dari', '>'],
  ['lebih kecil dari', '<'],
];


function findTopLevel(s, phrase) {
  let depth = 0, inStr = false;
  for (let i = 0; i < s.length; i++) {
    const c = s[i];
    if (c === '"') inStr = !inStr;
    else if (!inStr) {
      if (c === '(') depth++;
      else if (c === ')') depth--;
      else if (depth === 0 && s.startsWith(phrase, i)) return i;
    }
  }
  return -1;
}




class ParserUngkapan {
  constructor(toks, berkas) { this.t = toks; this.p = 0; this.berkas = berkas; }

  peek() { return this.t[this.p] || null; }
  next() { return this.t[this.p++]; }
  galat(p) { throw new GalatInsJay(p, null, this.berkas); }

  parse() {
    const n = this.atau();
    if (this.peek()) this.galat("Ungkapan belum selesai dibaca (ada sisa kata).");
    return n;
  }
  atau() {
    let k = this.dan();
    while (this.peek() && this.peek().t === 'ident' && this.peek().v === 'atau') {
      this.next(); k = { t: 'Logika', op: 'atau', kiri: k, kanan: this.dan() };
    }
    return k;
  }
  dan() {
    let k = this.tidak();
    while (this.peek() && this.peek().t === 'ident' && this.peek().v === 'dan') {
      this.next(); k = { t: 'Logika', op: 'dan', kiri: k, kanan: this.tidak() };
    }
    return k;
  }
  tidak() {
    if (this.peek() && this.peek().t === 'ident' && this.peek().v === 'tidak') {
      this.next(); return { t: 'Tidak', anak: this.tidak() };
    }
    return this.tambah();
  }
  tambah() {
    let k = this.kali();
    while (this.peek() && this.peek().t === 'op' && (this.peek().v === '+' || this.peek().v === '-')) {
      const op = this.next().v; k = { t: 'Biner', op, kiri: k, kanan: this.kali() };
    }
    return k;
  }
  kali() {
    let k = this.atom();
    while (this.peek() && this.peek().t === 'op' && '*/%'.includes(this.peek().v)) {
      const op = this.next().v; k = { t: 'Biner', op, kiri: k, kanan: this.atom() };
    }
    return k;
  }
  atom() {
    const tok = this.peek();
    if (!tok) this.galat('Ada ungkapan yang kosong.');
    switch (tok.t) {
      case 'angka': this.next(); return { t: 'Angka', nilai: tok.v };
      case 'teks': this.next(); return { t: 'Teks', nilai: tok.v };
      case 'var': this.next(); return { t: 'Wadah', nama: tok.nama };
      case 'panjang': this.next(); return { t: 'Panjang', nama: tok.nama };
      case 'kewadah': this.next(); return { t: 'KeAngka', nama: tok.nama };
      case 'hurufkecil': this.next(); return { t: 'HurufKecil', nama: tok.nama };
      case 'hurufbesar': this.next(); return { t: 'HurufBesar', nama: tok.nama };
      case 'lp': {
        this.next();
        const d = this.atau();
        if (!this.peek() || this.peek().t !== 'rp') this.galat("Kurung '(' tidak pernah ditutup.");
        this.next();
        return d;
      }
      case 'panggil': {
        this.next();
        const nama = tok.nama;
        const args = [];
        if (this.peek() && this.peek().t === 'ident' && this.peek().v === 'dengan') {
          this.next();
          args.push(this.atau());
          while (this.peek() && this.peek().t === 'comma') { this.next(); args.push(this.atau()); }
        }
        return { t: 'Panggilan', nama, args };
      }
      case 'ident': {
        this.next();
        if (tok.v === 'benar') return { t: 'Benar' };
        if (tok.v === 'salah') return { t: 'Salah' };
        this.galat(`Kata '${tok.v}' tidak dikenal. Untuk mengambil isi wadah, tulis 'wadah ${tok.v}'.`);
        break;
      }
      default:
        this.galat('Ungkapan tidak terduga.');
    }
  }
}

function parseUngkapan(s, berkas) {
  return new ParserUngkapan(lexUngkapan(s, berkas), berkas).parse();
}

function parseKondisi(teks, berkas) {
  const s = teks.trim();
  if (/^tidak\s+/i.test(s)) {
    return { t: 'Tidak', anak: parseKondisi(s.replace(/^tidak\s+/i, ''), berkas) };
  }
  const idxMengandung = findTopLevel(s, 'mengandung');
  if (idxMengandung !== -1) {
    return {
      t: 'Mengandung',
      kiri: parseUngkapan(s.slice(0, idxMengandung), berkas),
      kanan: parseUngkapan(s.slice(idxMengandung + 'mengandung'.length), berkas),
    };
  }
  for (const [frasa, op] of PERBANDINGAN) {
    const idx = findTopLevel(s, frasa);
    if (idx !== -1) {
      return {
        t: 'Kondisi', op, frasa,
        kiri: parseUngkapan(s.slice(0, idx), berkas),
        kanan: parseUngkapan(s.slice(idx + frasa.length), berkas),
      };
    }
  }
  const low = s.toLowerCase();
  if (low === 'benar') return { t: 'Benar' };
  if (low === 'salah') return { t: 'Salah' };
  return { t: 'Kebenaran', expr: parseUngkapan(s, berkas) };
}




class Parser {
  constructor(tokens, berkas) { this.t = tokens; this.i = 0; this.berkas = berkas; }

  peek() { return this.t[this.i] || null; }
  galat(p, tok) {
    throw new GalatInsJay(p, tok ? tok.baris : null, tok ? tok.berkas : this.berkas, tok ? tok.teks : null);
  }

  program() {
    const isi = [];
    while (this.i < this.t.length) isi.push(this.kalimat());
    return { t: 'Program', isi };
  }


  blok(penutup) {
    const isi = [];
    while (this.i < this.t.length && !penutup.includes(this.t[this.i].jenis)) {
      isi.push(this.kalimat());
    }
    return isi;
  }

  kalimat() {
    const tok = this.t[this.i++];
    const g = tok.m;
    const dasar = { baris: tok.baris, berkas: tok.berkas };
    switch (tok.jenis) {
      case 'BAB':
        return { ...dasar, t: 'Bab', judul: tok.judul };
      case 'LET':
        return { ...dasar, t: 'Let', nama: g[1], nilai: parseUngkapan(g[2], tok.berkas) };
      case 'SET':
        return { ...dasar, t: 'Set', nama: g[1], nilai: parseUngkapan(g[2], tok.berkas) };
      case 'ADD':
        return { ...dasar, t: 'Tambah', nama: g[2], nilai: parseUngkapan(g[1], tok.berkas) };
      case 'SUB':
        return { ...dasar, t: 'Kurang', nama: g[1], nilai: parseUngkapan(g[2], tok.berkas) };
      case 'BERKATA':
        return { ...dasar, t: 'Berkata', nilai: parseUngkapan(g[1], tok.berkas) };
      case 'TANYA':
        return { ...dasar, t: 'Tanya', nama: g[2], pertanyaan: parseUngkapan(g[1], tok.berkas) };
      case 'JIKA': {
        const kondisi = parseKondisi(g[1], tok.berkas);
        const tubuh = this.blok(['KALAU_TIDAK', 'SELESAI']);
        let lain = [];
        if (this.peek() && this.peek().jenis === 'KALAU_TIDAK') {
          this.i++;
          lain = this.blok(['SELESAI']);
        }
        if (!this.peek() || this.peek().jenis !== 'SELESAI') this.galat("Blok 'jika' belum ditutup dengan 'selesai'.", tok);
        this.i++;
        return { ...dasar, t: 'Jika', kondisi, tubuh, lain };
      }
      case 'SELAMA': {
        const kondisi = parseKondisi(g[1], tok.berkas);
        const tubuh = this.blok(['SELESAI']);
        if (!this.peek() || this.peek().jenis !== 'SELESAI') this.galat("Blok 'selama' belum ditutup dengan 'selesai'.", tok);
        this.i++;
        return { ...dasar, t: 'Selama', kondisi, tubuh };
      }
      case 'KEBIASAAN': {
        const nama = g[1];
        const params = g[2] ? pisahArgumen(g[2]).map((p) => p.trim()).filter(Boolean) : [];
        const tubuh = this.blok(['SELESAI']);
        if (!this.peek() || this.peek().jenis !== 'SELESAI') this.galat(`Kebiasaan '${nama}' belum ditutup dengan 'selesai'.`, tok);
        this.i++;
        return { ...dasar, t: 'Kebiasaan', nama, params, tubuh };
      }
      case 'PANGGIL': {
        const args = g[2] ? pisahArgumen(g[2]).map((a) => parseUngkapan(a, tok.berkas)) : [];
        return { ...dasar, t: 'Panggil', nama: g[1], args };
      }
      case 'KEMBALI':
        return { ...dasar, t: 'Kembali', nilai: parseUngkapan(g[1], tok.berkas) };
      case 'SAMBUNG':
        return { ...dasar, t: 'Sambung', berkas: g[1] };
      case 'HALAMAN':
        return { ...dasar, t: 'Halaman', nama: g[1], judul: parseUngkapan(g[2], tok.berkas) };
      case 'JUDUL':
        return { ...dasar, t: 'Judul', target: g[2], nilai: parseUngkapan(g[1], tok.berkas) };
      case 'PARAGRAF':
        return { ...dasar, t: 'Paragraf', target: g[2], nilai: parseUngkapan(g[1], tok.berkas) };
      case 'ISIAN':
        return { ...dasar, t: 'Isian', nama: g[1], target: g[2] };
      case 'TOMBOL':
        return { ...dasar, t: 'Tombol', target: g[3], label: parseUngkapan(g[1], tok.berkas), fungsi: g[2] };
      case 'JAWABAN':
        return { ...dasar, t: 'Jawaban', target: g[2], nilai: parseUngkapan(g[1], tok.berkas) };
      case 'GANTI_JAWABAN':
        return { ...dasar, t: 'GantiJawaban', target: g[1], nilai: parseUngkapan(g[2], tok.berkas) };
      case 'BACA_ISIAN':
        return { ...dasar, t: 'BacaIsian', nama: g[1], sasaran: g[2] };
      case 'AMBIL':
        return { ...dasar, t: 'Ambil', modul: g[1], nama: g[2] };
      case 'SERAHKAN':
        return { ...dasar, t: 'Serahkan', nama: g[1] };
      case 'SELESAI':
      case 'KALAU_TIDAK':
        this.galat(`'${tok.jenis === 'SELESAI' ? 'selesai' : 'kalau tidak'}' ini tidak punya pasangan.`, tok);
        break;
      default:
        this.galat(`Kalimat jenis '${tok.jenis}' belum bisa diurai.`, tok);
    }
  }
}

module.exports = { Parser, ParserUngkapan, parseUngkapan, parseKondisi, findTopLevel, PERBANDINGAN };
