#!/usr/bin/env node
'use strict';
// ===========================================================================
// insjay — CLI bahasa insJaY
// Pipeline: Lexing -> Parsing -> AST -> Penganalisis Semantik -> Kompilasi JS
// ===========================================================================

const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const { proses } = require('../src/pipa');
const { GalatInsJay } = require('../src/lexer');
const { ringkas } = require('../src/ast');
const { RUNTIME_JS, bungkusHTML, judulHalaman } = require('../src/runtime');

const VERSI = '0.4.0';

const BANTUAN = `
insJaY v${VERSI} — bahasa pemrograman naratif Indonesia (.Jay)

PEMAKAIAN
  insjay <berkas.Jay>              jalankan cerita
  insjay jalankan <berkas.Jay>     jalankan cerita (alias: run)
  insjay kompilasi <berkas.Jay>    terjemah ke JavaScript   (-o keluar.js)
  insjay web <berkas.Jay>          terjemah ke HTML mandiri (-o index.html)
  insjay periksa <berkas.Jay>      analisis semantik (galat/peringatan)
  insjay ast <berkas.Jay>          tampilkan pohon AST
  insjay lex <berkas.Jay>          tampilkan token hasil lexing
  insjay versi                     tampilkan versi
  insjay bantuan                   tampilkan bantuan ini

CONTOH
  insjay contoh/halo.Jay
  printf "Budi\\n15\\n" | insjay contoh/skrip/sapa_skrip.Jay
  insjay web contoh/web/kalkulator_web.Jay -o index.html
`;

function ambilOpsi(argv) {
  const sisa = [];
  let keluaran = null;
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '-o' || a === '--keluaran') {
      keluaran = argv[++i] || null;
    } else {
      sisa.push(a);
    }
  }
  return { sisa, keluaran };
}

function laporkanDiagnostik(hasil) {
  const d = hasil.analisis.diagnostik;
  if (!d.length) return true;
  let adaGalat = false;
  for (const item of d) {
    const lokasi = item.berkas ? `${item.berkas}${item.baris ? ':' + item.baris : ''}` : '';
    if (item.tingkat === 'galat') {
      adaGalat = true;
      console.error(`  ✗ [galat] ${item.pesan}${lokasi ? '  (' + lokasi + ')' : ''}`);
    } else {
      console.error(`  ! [peringatan] ${item.pesan}${lokasi ? '  (' + lokasi + ')' : ''}`);
    }
  }
  return !adaGalat;
}

function pastikanAda(berkas) {
  if (!berkas) {
    console.error('Sebutkan berkas .Jay. Contoh: insjay jalankan contoh/halo.Jay');
    process.exit(2);
  }
  if (!fs.existsSync(berkas)) {
    console.error(`Berkas '${berkas}' tidak ditemukan.`);
    process.exit(2);
  }
}

function perintahJalankan(berkas) {
  pastikanAda(berkas);
  const hasil = proses(berkas);
  if (!laporkanDiagnostik(hasil)) {
    console.error('\n[Kisah terhenti] Perbaiki galat di atas dahulu.');
    process.exit(1);
  }
  const temp = path.join(os.tmpdir(), `insjay-${process.pid}.js`);
  fs.writeFileSync(temp, RUNTIME_JS + '\n\n' + hasil.js + '\n', 'utf8');
  try {
    const r = spawnSync(process.execPath, [temp], { stdio: 'inherit' });
    process.exit(r.status === null ? 1 : r.status);
  } finally {
    try { fs.unlinkSync(temp); } catch (e) { /* abaikan */ }
  }
}

function perintahKompilasi(berkas, keluaran) {
  pastikanAda(berkas);
  const hasil = proses(berkas);
  laporkanDiagnostik(hasil);
  const kode = RUNTIME_JS + '\n\n' + hasil.js + '\n';
  if (keluaran) {
    fs.writeFileSync(keluaran, kode, 'utf8');
    console.log(`Berhasil ditulis: ${keluaran}`);
  } else {
    process.stdout.write(kode);
  }
}

function perintahWeb(berkas, keluaran) {
  pastikanAda(berkas);
  const hasil = proses(berkas);
  laporkanDiagnostik(hasil);
  const html = bungkusHTML(hasil.js, judulHalaman(hasil.program));
  if (keluaran) {
    fs.writeFileSync(keluaran, html, 'utf8');
    console.log(`Berhasil ditulis: ${keluaran}`);
  } else {
    process.stdout.write(html);
  }
}

function perintahPeriksa(berkas) {
  pastikanAda(berkas);
  const hasil = proses(berkas);
  const r = hasil.analisis.ringkasan;
  console.log(`Periksa semantik: ${path.basename(berkas)}`);
  console.log(`  Bab (narasi)      : ${r.bab}`);
  console.log(`  Kalimat perintah  : ${r.kalimat - r.bab}`);
  console.log(`  Kebiasaan (fungsi): ${r.fungsi}`);
  console.log(`  Galat             : ${r.galat}`);
  console.log(`  Peringatan        : ${r.peringatan}`);
  const bersih = laporkanDiagnostik(hasil);
  console.log(`  Status            : ${bersih ? 'SEMUA KALIMAT MENGIKUTI ALUR CERITA ✔' : 'ADA MASALAH ✗'}`);
  process.exit(bersih ? 0 : 1);
}

function perintahAst(berkas) {
  pastikanAda(berkas);
  const hasil = proses(berkas);
  if (process.env.INSJAY_AST_JSON) {
    process.stdout.write(JSON.stringify(hasil.ast, null, 2) + '\n');
  } else {
    console.log(ringkas(hasil.ast));
  }
}

function perintahLex(berkas) {
  pastikanAda(berkas);
  const hasil = proses(berkas);
  for (const t of hasil.tokens) {
    const isi = t.jenis === 'BAB' ? t.judul : (t.m ? t.m.slice(1).filter(Boolean).join(' | ') : '');
    console.log(`${String(t.baris).padStart(4)}  ${t.jenis.padEnd(14)} ${isi}`);
  }
}

function main() {
  const argv = process.argv.slice(2);
  if (!argv.length) { console.log(BANTUAN); process.exit(0); }

  const perintah = argv[0];
  if (perintah === 'versi' || perintah === '-v' || perintah === '--version') {
    console.log(`insJaY CLI v${VERSI}`); process.exit(0);
  }
  if (perintah === 'bantuan' || perintah === '-h' || perintah === '--help') {
    console.log(BANTUAN); process.exit(0);
  }

  const { sisa, keluaran } = ambilOpsi(argv.slice(1));

  try {
    switch (perintah) {
      case 'jalankan': case 'run': perintahJalankan(sisa[0]); break;
      case 'kompilasi': case 'build': perintahKompilasi(sisa[0], keluaran); break;
      case 'web': case 'html': perintahWeb(sisa[0], keluaran); break;
      case 'periksa': case 'check': perintahPeriksa(sisa[0]); break;
      case 'ast': perintahAst(sisa[0]); break;
      case 'lex': perintahLex(sisa[0]); break;
      default:
        // Pemakaian singkat: insjay berkas.Jay
        if (perintah.endsWith('.Jay') || fs.existsSync(perintah)) perintahJalankan(perintah);
        else { console.error(`Perintah '${perintah}' tidak dikenal.\n${BANTUAN}`); process.exit(2); }
    }
  } catch (e) {
    if (e instanceof GalatInsJay) {
      console.error(`[Gagal] ${e.format()}`);
    } else {
      console.error(`[Gagal] ${e.message}`);
    }
    process.exit(1);
  }
}

main();
