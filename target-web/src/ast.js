'use strict';





const JENIS_SIMPUL = {
  Program: 'Akar program',
  Bab: 'Judul bab (narasi)',
  Let: 'Menyiapkan wadah',
  Set: 'Mengganti isi wadah',
  Tambah: 'Menambah isi wadah',
  Kurang: 'Mengurangi isi wadah',
  Berkata: 'Berkata / mencetak',
  Jika: 'Percabangan',
  Selama: 'Perulangan',
  Kebiasaan: 'Membuat kebiasaan (fungsi)',
  Panggil: 'Memanggil kebiasaan',
  Kembali: 'Mengembalikan nilai',
  Sambung: 'Menyambung cerita',
  Tanya: 'Bertanya / masukan',
  Halaman: 'Membuat halaman web',
  Judul: 'Menaruh judul',
  Paragraf: 'Menaruh paragraf',
  Isian: 'Menaruh kotak isian',
  Tombol: 'Menaruh tombol',
  Jawaban: 'Menaruh jawaban',
  GantiJawaban: 'Mengubah jawaban',
  BacaIsian: 'Membaca kotak isian',
};

const JENIS_UNGKAPAN = {
  Angka: 'angka', Teks: 'teks', Wadah: 'isi wadah', Panjang: 'panjang wadah',
  KeAngka: 'wadah jadi angka', Panggilan: 'panggilan kebiasaan', Biner: 'operasi',
  Logika: 'logika', Tidak: 'penyangkalan', Kondisi: 'perbandingan',
  Kebenaran: 'nilai kebenaran', Benar: 'benar', Salah: 'salah',
};


function ringkas(simpul, level = 0) {
  const j = '  '.repeat(level);
  if (!simpul || typeof simpul !== 'object') return j + String(simpul);
  const t = simpul.t;
  switch (t) {
    case 'Program':
      return simpul.isi.map((n) => ringkas(n, level)).join('\n');
    case 'Bab':
      return `${j}BAB: ${simpul.judul}`;
    case 'Let':
      return `${j}LET ${simpul.nama} = ${ringkasUngkapan(simpul.nilai)}`;
    case 'Set':
      return `${j}SET ${simpul.nama} = ${ringkasUngkapan(simpul.nilai)}`;
    case 'Tambah':
      return `${j}TAMBAH ${simpul.nama} += ${ringkasUngkapan(simpul.nilai)}`;
    case 'Kurang':
      return `${j}KURANG ${simpul.nama} -= ${ringkasUngkapan(simpul.nilai)}`;
    case 'Berkata':
      return `${j}BERKATA ${ringkasUngkapan(simpul.nilai)}`;
    case 'Tanya':
      return `${j}TANYA -> wadah ${simpul.nama} (${ringkasUngkapan(simpul.pertanyaan)})`;
    case 'Jika':
      return [
        `${j}JIKA ${ringkasUngkapan(simpul.kondisi)}`,
        ...simpul.tubuh.map((n) => ringkas(n, level + 1)),
        ...(simpul.lain.length
          ? [`${j}KALAU TIDAK`, ...simpul.lain.map((n) => ringkas(n, level + 1))]
          : []),
        `${j}SELESAI`,
      ].join('\n');
    case 'Selama':
      return [
        `${j}SELAMA ${ringkasUngkapan(simpul.kondisi)}`,
        ...simpul.tubuh.map((n) => ringkas(n, level + 1)),
        `${j}SELESAI`,
      ].join('\n');
    case 'Kebiasaan':
      return [
        `${j}KEBIASAAN ${simpul.nama}(${simpul.params.join(', ')})`,
        ...simpul.tubuh.map((n) => ringkas(n, level + 1)),
        `${j}SELESAI`,
      ].join('\n');
    case 'Panggil':
      return `${j}PANGGIL ${simpul.nama}(${simpul.args.map(ringkasUngkapan).join(', ')})`;
    case 'Kembali':
      return `${j}KEMBALI ${ringkasUngkapan(simpul.nilai)}`;
    case 'Sambung':
      return `${j}SAMBUNG "${simpul.berkas}"`;
    case 'Halaman':
      return `${j}HALAMAN ${simpul.nama} berjudul ${ringkasUngkapan(simpul.judul)}`;
    case 'Judul':
      return `${j}JUDUL[${simpul.target}] ${ringkasUngkapan(simpul.nilai)}`;
    case 'Paragraf':
      return `${j}PARAGRAF[${simpul.target}] ${ringkasUngkapan(simpul.nilai)}`;
    case 'Isian':
      return `${j}ISIAN[${simpul.target}] ${simpul.nama}`;
    case 'Tombol':
      return `${j}TOMBOL[${simpul.target}] ${ringkasUngkapan(simpul.label)} -> ${simpul.fungsi}()`;
    case 'Jawaban':
      return `${j}JAWABAN[${simpul.target}] ${ringkasUngkapan(simpul.nilai)}`;
    case 'GantiJawaban':
      return `${j}UBAH JAWABAN[${simpul.target}] ${ringkasUngkapan(simpul.nilai)}`;
    case 'BacaIsian':
      return `${j}BACA ISIAN ${simpul.nama} -> wadah ${simpul.sasaran}`;
    case 'Ambil':
      return `${j}AMBIL "${simpul.modul}" -> wadah ${simpul.nama}`;
    case 'Serahkan':
      return `${j}SERAHKAN kebiasaan ${simpul.nama} kepada dunia`;
    default:
      return `${j}${t}`;
  }
}

function ringkasUngkapan(n) {
  if (!n || typeof n !== 'object') return String(n);
  switch (n.t) {
    case 'Angka': return String(n.nilai);
    case 'Teks': return JSON.stringify(n.nilai);
    case 'Benar': return 'benar';
    case 'Salah': return 'salah';
    case 'Wadah': return `wadah ${n.nama}`;
    case 'Panjang': return `panjang dari wadah ${n.nama}`;
    case 'KeAngka': return `angka dari wadah ${n.nama}`;
    case 'HurufKecil': return `huruf kecil dari wadah ${n.nama}`;
    case 'HurufBesar': return `huruf besar dari wadah ${n.nama}`;
    case 'Panggilan': return `${n.nama}(${n.args.map(ringkasUngkapan).join(', ')})`;
    case 'Biner': return `(${ringkasUngkapan(n.kiri)} ${n.op} ${ringkasUngkapan(n.kanan)})`;
    case 'Logika': return `(${ringkasUngkapan(n.kiri)} ${n.op} ${ringkasUngkapan(n.kanan)})`;
    case 'Tidak': return `tidak ${ringkasUngkapan(n.anak)}`;
    case 'Kondisi': return `(${ringkasUngkapan(n.kiri)} ${n.frasa} ${ringkasUngkapan(n.kanan)})`;
    case 'Mengandung': return `(${ringkasUngkapan(n.kiri)} mengandung ${ringkasUngkapan(n.kanan)})`;
    case 'Kebenaran': return ringkasUngkapan(n.expr);
    default: return n.t;
  }
}

module.exports = { JENIS_SIMPUL, JENIS_UNGKAPAN, ringkas, ringkasUngkapan };
