'use strict';
// ===========================================================================
// TAHAP 4 — PENGANALISIS SEMANTIK
// Memeriksa makna: wadah dipakai sebelum disiapkan, kebiasaan ada/tidak,
// jumlah isian cocok, 'mengembalikan' hanya di dalam kebiasaan, dsb.
// ===========================================================================

class Penganalisis {
  constructor() {
    this.diagnostik = [];
    this.kerangka = [new Map()]; // tumpukan lingkup: Map(nama -> {simpul, dipakai})
    this.fungsi = new Map();     // nama -> {jumlah, simpul, dipakai}
    this.dalamFungsi = 0;
    this.jumlahBab = 0;
    this.jumlahKalimat = 0;
  }

  galat(simpul, pesan) {
    this.diagnostik.push({ tingkat: 'galat', pesan, baris: simpul.baris, berkas: simpul.berkas });
  }
  peringatan(simpul, pesan) {
    this.diagnostik.push({ tingkat: 'peringatan', pesan, baris: simpul.baris, berkas: simpul.berkas });
  }

  // -- pengelolaan lingkup --------------------------------------------------
  bawah() { return this.kerangka[this.kerangka.length - 1]; }
  dorong() { this.kerangka.push(new Map()); }
  tarik(simpul) {
    const f = this.kerangka.pop();
    for (const [nama, info] of f) {
      if (!info.dipakai) {
        this.peringatan(info.simpul, `Wadah '${nama}' disiapkan tetapi tidak pernah dipakai.`);
      }
    }
    if (simpul) { /* placeholder */ }
  }
  deklare(nama, simpul) { this.bawah().set(nama, { simpul, dipakai: false }); }
  ada(nama) {
    for (let i = this.kerangka.length - 1; i >= 0; i--) if (this.kerangka[i].has(nama)) return true;
    return false;
  }
  tandai(nama) {
    for (let i = this.kerangka.length - 1; i >= 0; i--) {
      if (this.kerangka[i].has(nama)) { this.kerangka[i].get(nama).dipakai = true; return; }
    }
  }

  // -- pemeriksaan ungkapan -------------------------------------------------
  periksaUngkapan(n, simpul) {
    if (!n) return;
    switch (n.t) {
      case 'Angka': case 'Teks': case 'Benar': case 'Salah': return;
      case 'Wadah': case 'Panjang': case 'KeAngka': case 'HurufKecil': case 'HurufBesar':
        if (!this.ada(n.nama)) {
          this.galat(simpul, `Wadah '${n.nama}' dipakai sebelum pernah disiapkan.`);
        } else this.tandai(n.nama);
        return;
      case 'Panggilan':
        for (const a of n.args) this.periksaUngkapan(a, simpul);
        this.periksaPanggilan(n.nama, n.args.length, simpul);
        return;
      case 'Biner': case 'Logika':
        this.periksaUngkapan(n.kiri, simpul); this.periksaUngkapan(n.kanan, simpul);
        return;
      case 'Tidak': this.periksaUngkapan(n.anak, simpul); return;
      case 'Kondisi': case 'Mengandung':
        this.periksaUngkapan(n.kiri, simpul); this.periksaUngkapan(n.kanan, simpul);
        return;
      case 'Kebenaran': this.periksaUngkapan(n.expr, simpul); return;
      default: return;
    }
  }

  periksaPanggilan(nama, jumlahArg, simpul) {
    if (!this.fungsi.has(nama)) {
      this.galat(simpul, `Kebiasaan '${nama}' dipanggil tetapi belum pernah dibuat.`);
      return;
    }
    const f = this.fungsi.get(nama);
    f.dipakai = true;
    if (f.jumlah !== jumlahArg) {
      this.galat(simpul, `Kebiasaan '${nama}' menerima ${f.jumlah} isian, tetapi diberi ${jumlahArg}.`);
    }
  }

  // -- penelusuran AST ------------------------------------------------------
  analisis(program) {
    for (const n of program.isi) this.kalimat(n);
    this.tarik(null);
    for (const [nama, info] of this.fungsi) {
      if (!info.dipakai) this.peringatan(info.simpul, `Kebiasaan '${nama}' dibuat tetapi tidak pernah dipanggil.`);
    }
    return {
      diagnostik: this.diagnostik,
      ringkasan: {
        bab: this.jumlahBab,
        kalimat: this.jumlahKalimat,
        fungsi: this.fungsi.size,
        galat: this.diagnostik.filter((d) => d.tingkat === 'galat').length,
        peringatan: this.diagnostik.filter((d) => d.tingkat === 'peringatan').length,
      },
    };
  }

  kalimat(n) {
    this.jumlahKalimat++;
    switch (n.t) {
      case 'Bab': this.jumlahBab++; return;
      case 'Let':
        this.periksaUngkapan(n.nilai, n); this.deklare(n.nama, n); return;
      case 'Set': case 'Tambah': case 'Kurang':
        if (!this.ada(n.nama)) this.galat(n, `Wadah '${n.nama}' diubah sebelum pernah disiapkan.`);
        else this.tandai(n.nama);
        this.periksaUngkapan(n.nilai, n); return;
      case 'Berkata': this.periksaUngkapan(n.nilai, n); return;
      case 'Tanya': this.periksaUngkapan(n.pertanyaan, n); this.deklare(n.nama, n); return;
      case 'Jika':
        this.periksaUngkapan(n.kondisi, n);
        for (const a of n.tubuh) this.kalimat(a);
        for (const a of n.lain) this.kalimat(a);
        return;
      case 'Selama':
        this.periksaUngkapan(n.kondisi, n);
        for (const a of n.tubuh) this.kalimat(a);
        return;
      case 'Kebiasaan': {
        this.fungsi.set(n.nama, { jumlah: n.params.length, simpul: n, dipakai: false });
        this.dorong();
        for (const p of n.params) this.deklare(p, n);
        this.dalamFungsi++;
        for (const a of n.tubuh) this.kalimat(a);
        this.dalamFungsi--;
        this.tarik(n);
        return;
      }
      case 'Panggil':
        for (const a of n.args) this.periksaUngkapan(a, n);
        this.periksaPanggilan(n.nama, n.args.length, n);
        return;
      case 'Kembali':
        if (this.dalamFungsi === 0) this.galat(n, "'mengembalikan' hanya boleh dipakai di dalam sebuah kebiasaan.");
        this.periksaUngkapan(n.nilai, n);
        return;
      case 'Sambung':
        this.galat(n, `Penyambungan cerita '${n.berkas}' belum diselesaikan.`);
        return;
      case 'Halaman': this.periksaUngkapan(n.judul, n); return;
      case 'Judul': case 'Paragraf': case 'Jawaban': case 'GantiJawaban':
        this.periksaUngkapan(n.nilai, n); return;
      case 'Isian': return;
      case 'Tombol':
        this.periksaUngkapan(n.label, n);
        if (!this.fungsi.has(n.fungsi)) {
          this.galat(n, `Tombol memanggil kebiasaan '${n.fungsi}' yang belum pernah dibuat.`);
        } else this.fungsi.get(n.fungsi).dipakai = true;
        return;
      case 'BacaIsian': this.deklare(n.sasaran, n); return;
      case 'Ambil': this.deklare(n.nama, n); return;
      case 'Serahkan':
        if (!this.fungsi.has(n.nama)) {
          this.galat(n, `Kebiasaan '${n.nama}' diserahkan ke dunia tetapi belum pernah dibuat.`);
        } else this.fungsi.get(n.nama).dipakai = true;
        return;
      default: return;
    }
  }
}

function analisis(program) {
  return new Penganalisis().analisis(program);
}

module.exports = { Penganalisis, analisis };
