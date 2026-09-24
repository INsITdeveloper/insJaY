'use strict';
// ===========================================================================
// TAHAP 5 — KOMPILASI
// AST -> JavaScript. Target contoh: JS (Node + browser).
// ===========================================================================

function jsUngkapan(n) {
  switch (n.t) {
    case 'Angka': return JSON.stringify(n.nilai);
    case 'Teks': return JSON.stringify(n.nilai);
    case 'Benar': return 'true';
    case 'Salah': return 'false';
    case 'Wadah': return n.nama;
    case 'Panjang': return `__ins.panjang(${n.nama})`;
    case 'KeAngka': return `__ins.angka(${n.nama})`;
    case 'HurufKecil': return `String(${n.nama}).toLowerCase()`;
    case 'HurufBesar': return `String(${n.nama}).toUpperCase()`;
    case 'Panggilan': return `${n.nama}(${n.args.map(jsUngkapan).join(', ')})`;
    case 'Biner': return `(${jsUngkapan(n.kiri)} ${n.op} ${jsUngkapan(n.kanan)})`;
    case 'Logika': return `(${jsUngkapan(n.kiri)} ${n.op === 'dan' ? '&&' : '||'} ${jsUngkapan(n.kanan)})`;
    case 'Tidak': return `(!${jsUngkapan(n.anak)})`;
    default: throw new Error(`Ungkapan '${n.t}' belum bisa dikompilasi.`);
  }
}

function jsKondisi(n) {
  switch (n.t) {
    case 'Tidak': return `(!${jsKondisi(n.anak)})`;
    case 'Kondisi': return `(${jsUngkapan(n.kiri)} ${n.op} ${jsUngkapan(n.kanan)})`;
    case 'Mengandung': return `(String(${jsUngkapan(n.kiri)}).includes(String(${jsUngkapan(n.kanan)})))`;
    case 'Benar': return 'true';
    case 'Salah': return 'false';
    case 'Kebenaran': return `Boolean(${jsUngkapan(n.expr)})`;
    default: throw new Error(`Kondisi '${n.t}' belum bisa dikompilasi.`);
  }
}

class Kompilator {
  constructor() { this.baris = []; }
  tulis(level, teks) { this.baris.push('  '.repeat(level) + teks); }

  kompilasi(program) {
    for (const n of program.isi) this.kalimat(n, 0);
    return this.baris.join('\n');
  }

  blok(daftar, level) {
    for (const a of daftar) this.kalimat(a, level);
  }

  kalimat(n, level) {
    switch (n.t) {
      case 'Bab': this.tulis(level, `// ${n.judul}`); return;
      case 'Let': this.tulis(level, `var ${n.nama} = ${jsUngkapan(n.nilai)};`); return;
      case 'Set': this.tulis(level, `${n.nama} = ${jsUngkapan(n.nilai)};`); return;
      case 'Tambah': this.tulis(level, `${n.nama} += ${jsUngkapan(n.nilai)};`); return;
      case 'Kurang': this.tulis(level, `${n.nama} -= ${jsUngkapan(n.nilai)};`); return;
      case 'Berkata': this.tulis(level, `__ins.kata(${jsUngkapan(n.nilai)});`); return;
      case 'Tanya': this.tulis(level, `${n.nama} = __ins.tanya(${jsUngkapan(n.pertanyaan)});`); return;
      case 'Jika':
        this.tulis(level, `if (${jsKondisi(n.kondisi)}) {`);
        this.blok(n.tubuh, level + 1);
        if (n.lain.length) {
          this.tulis(level, '} else {');
          this.blok(n.lain, level + 1);
        }
        this.tulis(level, '}');
        return;
      case 'Selama':
        this.tulis(level, `while (${jsKondisi(n.kondisi)}) {`);
        this.blok(n.tubuh, level + 1);
        this.tulis(level, '}');
        return;
      case 'Kebiasaan':
        this.tulis(level, `function ${n.nama}(${n.params.join(', ')}) {`);
        this.blok(n.tubuh, level + 1);
        this.tulis(level, '}');
        return;
      case 'Panggil':
        this.tulis(level, `${n.nama}(${n.args.map(jsUngkapan).join(', ')});`); return;
      case 'Kembali': this.tulis(level, `return ${jsUngkapan(n.nilai)};`); return;
      case 'Sambung': this.tulis(level, `// (cerita "${n.berkas}" belum tersambung)`); return;
      case 'Halaman': this.tulis(level, `__ins.halaman(${JSON.stringify(n.nama)}, ${jsUngkapan(n.judul)});`); return;
      case 'Judul': this.tulis(level, `__ins.judul(${JSON.stringify(n.target)}, ${jsUngkapan(n.nilai)});`); return;
      case 'Paragraf': this.tulis(level, `__ins.paragraf(${JSON.stringify(n.target)}, ${jsUngkapan(n.nilai)});`); return;
      case 'Isian': this.tulis(level, `__ins.isian(${JSON.stringify(n.target)}, ${JSON.stringify(n.nama)});`); return;
      case 'Tombol': this.tulis(level, `__ins.tombol(${JSON.stringify(n.target)}, ${jsUngkapan(n.label)}, ${n.fungsi});`); return;
      case 'Jawaban': this.tulis(level, `__ins.jawaban(${JSON.stringify(n.target)}, ${jsUngkapan(n.nilai)});`); return;
      case 'GantiJawaban': this.tulis(level, `__ins.gantiJawaban(${JSON.stringify(n.target)}, ${jsUngkapan(n.nilai)});`); return;
      case 'BacaIsian': this.tulis(level, `${n.sasaran} = __ins.bacaIsian(${JSON.stringify(n.nama)});`); return;
      case 'Ambil': this.tulis(level, `var ${n.nama} = (typeof require === 'function') ? require(${JSON.stringify(n.modul)}) : {};`); return;
      case 'Serahkan': this.tulis(level, `if (typeof module !== 'undefined' && module.exports) module.exports[${JSON.stringify(n.nama)}] = ${n.nama};`); return;
      default: this.tulis(level, `// (simpul '${n.t}' belum didukung)`);
    }
  }
}

function kompilasi(program) { return new Kompilator().kompilasi(program); }

module.exports = { Kompilator, kompilasi, jsUngkapan, jsKondisi };
