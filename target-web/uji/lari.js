'use strict';
// ===========================================================================
// Uji cepat seluruh pipeline insJaY.
// Jalankan: npm run uji
// ===========================================================================

const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const BIN = path.join(__dirname, '..', 'bin', 'insjay.js');
const AKAR = path.join(__dirname, '..');
let lulus = 0, gagal = 0;

function jalankan(args, masukan) {
  const r = spawnSync(process.execPath, [BIN, ...args], {
    input: masukan || '',
    encoding: 'utf8',
    cwd: AKAR,
  });
  return { keluaran: r.stdout.trim(), galat: r.stderr.trim(), kode: r.status };
}

function uji(nama, syarat) {
  if (syarat) { lulus++; console.log(`  ✓ ${nama}`); }
  else { gagal++; console.log(`  ✗ ${nama}`); }
}

console.log('Menguji insJaY CLI...\n');

let r = jalankan(['contoh/halo.Jay']);
uji('halo.Jay berjalan', r.keluaran.includes('Halo, dunia!') && r.kode === 0);

r = jalankan(['contoh/fizzbuzz.Jay']);
uji('fizzbuzz.Jay mencetak FizzBuzz', r.keluaran.includes('FizzBuzz'));

r = jalankan(['contoh/kalkulator.Jay']);
uji('kalkulator.Jay menghitung 12 & 25', r.keluaran.includes('12') && r.keluaran.includes('25'));

r = jalankan(['contoh/cerita/utama.Jay']);
uji('impor multi-berkas nyambung', r.keluaran.includes('Ayu tinggal di Bandung'));

r = jalankan(['contoh/skrip/sapa_skrip.Jay'], 'Budi\n15\n');
uji('masukan pengguna terbaca', r.keluaran.includes('Halo, Budi') && r.keluaran.includes('3 tahun'));

r = jalankan(['periksa', 'contoh/kalkulator.Jay']);
uji('periksa lulus', r.keluaran.includes('ALUR CERITA'));

r = jalankan(['lex', 'contoh/halo.Jay']);
uji('lexing menghasilkan token', r.keluaran.includes('BAB') && r.keluaran.includes('LET'));

r = jalankan(['ast', 'contoh/kalkulator.Jay']);
uji('AST terbentuk', r.keluaran.includes('KEBIASAAN tambah'));

// galat semantik harus terdeteksi
const tmp = path.join(os.tmpdir(), 'insjay-uji-galat.Jay');
fs.writeFileSync(tmp, '# Bab 1\naku berkata: wadah hantu.\n');
r = jalankan(['periksa', tmp]);
uji('galat wadah tak dikenal terdeteksi', r.kode !== 0 && r.galat.includes('belum pernah disiapkan'));

// kalimat ngawur harus ditolak
const tmp2 = path.join(os.tmpdir(), 'insjay-uji-ngawur.Jay');
fs.writeFileSync(tmp2, '# Bab 1\naku berkata: "hai".\nngawur total\n');
r = jalankan(['jalankan', tmp2]);
uji('kalimat tidak koheren ditolak', r.kode !== 0 && r.galat.includes('tidak mengikuti alur cerita'));

// web -> html
const tmp3 = path.join(os.tmpdir(), 'insjay-uji-web.html');
r = jalankan(['web', 'contoh/web/kalkulator_web.Jay', '-o', tmp3]);
const html = fs.existsSync(tmp3) ? fs.readFileSync(tmp3, 'utf8') : '';
uji('kompilasi web menghasilkan HTML', html.includes('ins-tombol') && html.includes('__ins.halaman'));

// ungkapan v0.4: huruf kecil + mengandung
r = jalankan(['periksa', 'contoh/bot/whatsapp.Jay']);
uji('fitur v0.4 (huruf kecil/mengandung) lulus semantik', r.keluaran.includes('ALUR CERITA'));

// bot WhatsApp: kompilasi lalu panggil lewat host (mode demo)
const jsBot = path.join(os.tmpdir(), 'insjay-uji-bot.js');
jalankan(['kompilasi', 'contoh/bot/whatsapp.Jay', '-o', jsBot]);
const hostPath = path.join(AKAR, 'contoh', 'bot', 'host.js');
const rb = spawnSync(process.execPath, [hostPath, jsBot], { input: '/halo\n/menu\n', encoding: 'utf8' });
uji('bot WhatsApp insJaY membalas /halo', rb.stdout.includes('Halo juga!'));
uji('bot WhatsApp insJaY membalas /menu', rb.stdout.includes('Menu:'));

console.log(`\nSelesai: ${lulus} lulus, ${gagal} gagal.`);
process.exit(gagal ? 1 : 0);
