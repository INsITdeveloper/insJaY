# insJaY CLI — v0.3

Compiler & runner resmi bahasa **insJaY**: bahasa pemrograman naratif berbahasa
Indonesia. Berkas sumber berekstensi `.Jay`.

Pipeline lengkap:

```
 .Jay  →  LEXING  →  PARSING  →  AST  →  PENGANALISIS SEMANTIK  →  KOMPILASI  →  JavaScript
```

Kompilasi menghasilkan JavaScript, sehingga cerita `.Jay` bisa dijalankan **di
terminal (Node.js)** maupun **di browser** (HTML mandiri).

---

## Pasang ke Terminal

```bash
# dari dalam folder insjay-cli
npm install -g .

# atau tanpa memindahkan folder
npm link
```

Setelah itu perintah `insjay` tersedia di terminal mana pun:

```bash
insjay contoh/halo.Jay
```

> Butuh Node.js 16 ke atas. Tidak ada dependensi lain.

---

## Perintah

| Perintah | Guna |
|----------|------|
| `insjay <berkas.Jay>` | jalankan cerita |
| `insjay jalankan <berkas>` | jalankan cerita (alias `run`) |
| `insjay kompilasi <berkas> -o keluar.js` | terjemah ke JavaScript |
| `insjay web <berkas> -o index.html` | terjemah ke HTML mandiri |
| `insjay periksa <berkas>` | analisis semantik (galat/peringatan) |
| `insjay ast <berkas>` | tampilkan pohon AST |
| `insjay lex <berkas>` | tampilkan token hasil lexing |
| `insjay versi` / `insjay bantuan` | info |

---

## Contoh Pemakaian

```bash
# 1) Jalankan cerita biasa
insjay contoh/halo.Jay

# 2) Skrip interaktif (masukan pengguna)
printf "Budi\n15\n" | insjay contoh/skrip/sapa_skrip.Jay

# 3) Jadikan aplikasi web
insjay web contoh/web/kalkulator_web.Jay -o index.html
# buka index.html di peramban — langsung jalan

# 4) Lihat pipeline-nya bekerja
insjay lex contoh/kalkulator.Jay
insjay ast contoh/kalkulator.Jay
insjay periksa contoh/kalkulator.Jay
```

---

## Struktur Paket (memetakan tahap pipeline)

```
insjay-cli/
├── bin/insjay.js        # CLI
└── src/
    ├── lexer.js         # TAHAP 1 — Lexing (+ lexer ungkapan)
    ├── parser.js        # TAHAP 2 — Parsing  →  TAHAP 3 AST
    ├── ast.js           # TAHAP 3 — bentuk simpul AST + peringkas
    ├── semantik.js      # TAHAP 4 — Penganalisis Semantik
    ├── kompilator.js    # TAHAP 5 — Kompilasi ke JavaScript
    ├── runtime.js       # pustaka bantu saat JS dijalankan + pembungkus HTML
    └── pipa.js          # orkestrasi seluruh tahap
```

---

## Bot WhatsApp dengan insJaY (v0.4)

insJaY **bukan pengganti Node.js** — ia meng-*compile* ke JavaScript, dan JS
butuh Node untuk jalan. Jadi arsitekturnya: **logika bot ditulis 100% dalam
insJaY**, sedangkan urusan sambungan ke WhatsApp ditangani *host* Node kecil.

```bash
# 1) tulis bot: contoh/bot/whatsapp.Jay
# 2) kompilasi
insjay kompilasi contoh/bot/whatsapp.Jay -o bot.js

# 3) coba logikanya tanpa WhatsApp (mode demo)
node contoh/bot/host.js bot.js

# 4) sambung ke WhatsApp sungguhan
npm install @whiskeysockets/baileys
node contoh/bot/host.js bot.js --whatsapp    # pindai QR
```

Fitur bahasa baru yang menunjang ini:

| Maksud | Kalimat |
|--------|---------|
| Ambil modul npm | `aku mengambil dari "fs" ke dalam wadah berkas` |
| Ekspor fungsi ke host | `aku menyerahkan kebiasaan balas kepada dunia` |
| Huruf kecil | `huruf kecil dari wadah pesan` |
| Huruf besar | `huruf besar dari wadah pesan` |
| Mengandung kata | `jika wadah teks mengandung "/menu" maka` |

---

## Yang Diperiksa Penganalisis Semantik

- Wadah dipakai sebelum pernah disiapkan.
- Kebiasaan (fungsi) dipanggil sebelum pernah dibuat.
- Jumlah isian (argumen) tidak cocok dengan jumlah parameter.
- `mengembalikan` dipakai di luar kebiasaan.
- Tombol memanggil kebiasaan yang belum ada.
- **Peringatan**: wadah disiapkan tetapi tidak pernah dipakai; kebiasaan dibuat
  tetapi tidak pernah dipanggil.

---

## Bahasa ringkas

| Maksud | Kalimat |
|--------|---------|
| Wadah baru | `aku menyiapkan wadah bernama x yang berisi 5` |
| Ganti isi | `aku mengganti isi wadah x menjadi 8` |
| Tambah / kurang | `aku menambahkan 1 ke dalam wadah x` / `aku mengurangi wadah x dengan 2` |
| Cetak | `aku berkata: "Halo " + wadah nama` |
| Masukan | `aku bertanya: "Siapa namamu?" ke dalam wadah nama` |
| Jika | `jika <kondisi> maka` … `kalau tidak` … `selesai` |
| Selama | `selama <kondisi>, ulangi` … `selesai` |
| Fungsi | `aku membuat kebiasaan bernama f yang menerima a, b` … `selesai` |
| Kembalikan | `aku mengembalikan wadah a + wadah b` |
| Panggil | `aku memanggil kebiasaan f dengan 1, 2` |
| Sambung berkas | `aku menyambung cerita dari "tokoh.Jay"` |
| Halaman web | `aku menyiapkan halaman bernama utama berjudul "Situsku"` |
| Kotak isian | `aku menaruh kotak isian bernama nama ke dalam halaman utama` |
| Tombol | `aku menaruh tombol "Hitung" yang memanggil kebiasaan hitung ke dalam halaman utama` |
| Ubah jawaban | `aku mengubah jawaban di halaman utama menjadi "Hasil: " + wadah x` |
| Baca kotak isian | `aku membaca kotak isian nama ke dalam wadah nama` |
| Teks → angka | `angka dari wadah umur + 1` |

---

## Uji

```bash
npm run uji
```

---

## Lisensi

MIT.
