<div align="center">

# insJaY

**Bahasa pemrograman naratif berbahasa Indonesia** — dengan **compiler dan runtime sendiri**.

Kode ditulis sebagai *cerita*. Setiap kalimat wajib mengikuti alur, sehingga
sebuah program selalu terbaca lurus seperti buku — bukan tumpukan simbol acak.

`Lexing → Parsing → AST → Penganalisis Semantik → Kompilasi bytecode → Mesin insJaY`

</div>

---

## Mengapa insJaY?

Bahasa pemrograman biasa mengizinkan baris apa pun, sehingga kode mudah berubah
menjadi tumpukan simbol yang tidak terbaca sebagai satu kesatuan. insJaY
membalik pendekatannya:

- **Setiap kalimat wajib mengikuti satu pola cerita.** Baris yang tidak
  dikenali **ditolak**, bukan diabaikan. Tidak ada "sampah acak" di dalam kode.
- **Wadah** (variabel) dan **bab** (narasi) membuat alur program terbaca runtut.
- **Menyambung cerita** antar-berkas membuat proyek besar tetap tersusun rapi.

```
# Bab 1: Sapaan Pertama
aku menyiapkan wadah bernama nama yang berisi "Ayu".
aku berkata: "Halo, " + wadah nama + "!".
```

---

## Compiler + Runtime Sendiri

insJaY **tidak** menerjemahkan ke JavaScript dan **tidak** bergantung pada
Node.js. insJaY punya kompiler bytecode dan mesin virtual (VM) sendiri:

```
 .Jay  ──►  Lexing  ──►  Parsing  ──►  AST  ──►  Penganalisis Semantik
                                                                  │
                                                                  ▼
                                                             KOMPILASI
                                                                  │
                                                       bytecode .Jayc
                                                                  │
                                                                  ▼
                                                     MESIN insJaY (VM)
```

| Tahap | Berkas | Kegunaan |
|-------|--------|----------|
| 1. Lexing | `src/insjayvm/lexer.py` | teks → token kalimat + token ungkapan |
| 2. Parsing | `src/insjayvm/parser.py` | token → AST |
| 3. AST | (di dalam parser) | struktur program |
| 4. Penganalisis Semantik | `src/insjayvm/semantik.py` | cek makna & koherensi |
| 5. Kompilasi | `src/insjayvm/kompilator.py` | AST → bytecode |
| Runtime | `src/insjayvm/vm.py` | Mesin bytecode + pustaka bawaan |
| Pipa | `src/insjayvm/pipa.py` | orkestrasi seluruh tahap |
| CLI | `src/insjayvm/cli.py` | perintah `insjay` |

**Bytecode `.Jayc`** berbentuk JSON sehingga bisa diperiksa manusia:

```json
{
  "versi": "0.5.0",
  "konstanta": [1, 15, "", "FizzBuzz"],
  "fungsi": { "tambah": { "params": ["a", "b"], "kode": [ ... ] } },
  "kode": [ { "op": "PUSH", "arg": 0 }, { "op": "STORE", "arg": "angka" } ]
}
```

---

## Runtime insJaY v1 — satu pasang, semua tersedia

Seperti Node.js: setelah `insJay` terpasang, semua kebutuhan runtime sudah
menempel di dalamnya. Pengguna **tidak** perlu memasang Python, Node.js, axios,
maupun `requests` secara terpisah.

```
                        insJay (satu program)
                                |
        +-----------------------+-----------------------+
        |                       |                       |
   Compiler .Jay            Mesin (VM)            Pustaka bawaan
        |                       |                       |
     bytecode            +--------+--------+      +-------+-------+-------+
                         |        |        |      |       |       |       |
                       HTTP     JSON     Regex   Berkas  Kripto  Proses  Teks
                         |        |        |      |       |       |       |
                         +--------+--------+------+-------+-------+-------+
                                          |
                                     Sistem operasi
```

| Engine | Kalimat / kebiasaan | Status |
|--------|---------------------|--------|
| HTTP (GET/POST, header, timeout) | `aku meminta GET ...`, `aku meminta POST ...` | ada |
| JSON | `aku mengurai JSON ...`, `aku menyusun JSON ...` | ada |
| Regex | `cocok dengan pola`, `ganti_pola`, `cari_pola` | ada |
| Berkas | `baca_berkas`, `tulis_berkas`, `tambah_berkas`, `ada_berkas`, `hapus_berkas`, `daftar_berkas`, `buat_folder`, `ukuran_berkas`, `folder_kerja`, `gabung_jalur` | ada |
| Kripto | `hash_md5`, `hash_sha1`, `hash_sha256`, `base64_susun`, `base64_urai` | ada |
| Proses / OS | `aku membaca argumen ...`, `aku mengakhiri ...`, `lingkungan`, `nama_sistem` | ada |
| Teks & angka | `pangkas`, `ganti`, `pisah`, `gabung`, `angka dari wadah`, `teks dari wadah` | ada |
| Matematika | `akar`, `pangkat`, `bulat`, `lantai`, `acak` | ada |
| Masukan & jeda | `aku bertanya ...`, `aku menunggu ... milidetik`, `tidur` | ada |
| Async/await sejati | (belum) | rencana v0.8 |

Contoh lengkap semua engine: `contoh/runtime.Jay`.

---

## Pemasangan

Butuh **Python 3.8+**. Tidak ada dependensi pihak ketiga.

```bash
git clone https://github.com/INsITdeveloper/insJaY.git
cd insJaY

# pasang sebagai perintah 'insjay'
pip install .
# atau, kalau ingin sekalian mengedit sumbernya:
pip install -e .
```

Tanpa memasang apa pun, bisa langsung dipakai:

```bash
python3 -m insjayvm --help        # dengan PYTHONPATH=src
# atau
PYTHONPATH=src python3 -m insjayvm contoh/halo.Jay
```

### Sekali perintah

```sh
sh install.sh          # memasang Python (bila belum ada) lalu insJay
```

### Program mandiri (tanpa Python sama sekali)

Untuk pengguna akhir, sediakan satu berkas `insjay` hasil build:

```bash
pip install pyinstaller
insjay buat-mandiri          # menghasilkan dist/insjay
```

Binary untuk Linux/macOS/Windows juga dibangun otomatis oleh GitHub Actions
(`.github/workflows/bangun.yml`) setiap kali kamu menandai tag `v*`, lalu
dilampirkan ke halaman *Releases*. Pengguna cukup mengunduh satu berkas itu.

### Butuh Python dulu?

Ya — Mesin insJaY berjalan di atas Python 3. Supaya pengguna **tidak perlu
memasang Python sendiri**, bisa dibuat versi mandiri (satu berkas program):

```bash
pip install pyinstaller
insjay --buat-mandiri          # menghasilkan dist/insjay (satu berkas)
# atau manual:
pyinstaller --onefile --name insjay --paths src masuk.py
```

Satu berkas `dist/insjay` itu bisa dibagikan ke mesin lain (sistem yang sama).
Untuk Android/Termux, cukup `pkg install python && pip install .` satu kali.

---

## Mulai Cepat

```bash
insjay contoh/halo.Jay
insjay contoh/fizzbuzz.Jay
printf "Budi\n15\n" | insjay contoh/sapa_skrip.Jay

# kompilasi ke bytecode, lalu jalankan bytecode-nya
insjay kompilasi contoh/kalkulator.Jay -o kalkulator.Jayc
insjay jalankan kalkulator.Jayc
```

---

## Perintah CLI

| Perintah | Guna |
|----------|------|
| `insjay <berkas.Jay>` | jalankan cerita |
| `insjay jalankan <berkas>` | jalankan (alias `run`) |
| `insjay kompilasi <berkas> -o keluar.Jayc` | kompilasi ke bytecode |
| `insjay jalankan <berkas.Jayc>` | jalankan bytecode hasil kompilasi |
| `insjay periksa <berkas>` | analisis semantik |
| `insjay ast <berkas>` | tampilkan pohon AST |
| `insjay lex <berkas>` | tampilkan token hasil lexing |
| `insjay bytecode <berkas>` | tampilkan bytecode |
| `insjay versi` / `insjay bantuan` | informasi |

---

## Bahasa insJaY

### 1. Bentuk berkas

Berkas berekstensi **`.Jay`**.

- Baris kosong diabaikan.
- Komentar berawalan `//` diabaikan.
- Judul bab berawalan `#`, misalnya `# Bab 1: Perkenalan` (tidak dijalankan,
  dihitung sebagai bab).
- Tanda titik di akhir kalimat opsional.

### 2. Daftar kalimat

| Maksud | Kalimat |
|--------|---------|
| Menyiapkan wadah | `aku menyiapkan wadah bernama x yang berisi 5` |
| Mengganti isi wadah | `aku mengganti isi wadah x menjadi 8` |
| Menambah | `aku menambahkan 1 ke dalam wadah x` |
| Mengurangi | `aku mengurangi wadah x dengan 2` |
| Berkata (cetak) | `aku berkata: "Halo " + wadah nama` |
| Bertanya (masukan) | `aku bertanya: "Siapa namamu?" ke dalam wadah nama` |
| Jika / kalau tidak | `jika <kondisi> maka` … `kalau tidak` … `selesai` |
| Selama | `selama <kondisi>, ulangi` … `selesai` |
| Membuat kebiasaan | `aku membuat kebiasaan bernama f yang menerima a, b` … `selesai` |
| Memanggil kebiasaan | `aku memanggil kebiasaan f dengan 1, 2` |
| Mengembalikan nilai | `aku mengembalikan wadah a + wadah b` |
| Menyambung cerita | `aku menyambung cerita dari "tokoh.Jay"` |

### 3. Ungkapan

| Bentuk | Arti |
|--------|------|
| `123`, `4.5` | angka |
| `"teks apa pun"` | teks |
| `benar` / `salah` | nilai logika |
| `wadah x` | mengambil isi wadah |
| `panjang dari wadah x` | banyaknya karakter |
| `angka dari wadah x` | ubah teks menjadi angka |
| `huruf kecil dari wadah x` | jadikan huruf kecil |
| `huruf besar dari wadah x` | jadikan huruf besar |
| `( ... )` | pengelompokan |

Operator: `+` `-` `*` `/` `%`, serta `dan`, `atau`, `tidak`.
Tanda `+` dengan teks akan menyambung teks.

### 4. Perbandingan

`sama dengan`, `tidak sama dengan`, `lebih besar dari`, `lebih kecil dari`,
`lebih besar atau sama dengan`, `lebih kecil atau sama dengan`, dan
`mengandung` (untuk mencari kata di dalam teks).

```
jika wadah teks mengandung "/menu" maka
    aku berkata: "Ini menu.".
selesai.
```

### 5. Pustaka bawaan Mesin insJaY

Tidak perlu memasang apa pun:

| Kebiasaan | Guna |
|-----------|------|
| `akar` | akar kuadrat |
| `pangkat` | perpangkatan (2 isian) |
| `bulat` | pembulatan |
| `lantai` | pembulatan ke bawah |
| `acak` | angka acak 0–1 |
| `waktu_sekarang` | waktu sekarang |

```
aku berkata: "Akar dari 81 adalah " + hasil dari kebiasaan akar dengan 81.
```

### 6. Struktur data, JSON, dan API

**Deret (array) & himpunan (set)**

| Maksud | Kalimat |
|--------|---------|
| Buat deret | `aku menyiapkan deret bernama buah yang berisi "apel", "mangga"` |
| Deret kosong | `aku menyiapkan deret bernama kosong` |
| Tambah item | `aku menambahkan "pisang" ke dalam deret buah` |
| Ambil item ke-N | `benda ke-1 dari wadah buah` |
| Ubah item ke-N | `aku mengubah benda ke-1 dari deret buah menjadi "anggur"` |
| Buat himpunan | `aku menyiapkan himpunan bernama terlihat` |
| Tambah ke himpunan | `aku menambahkan "x" ke dalam himpunan terlihat` |

**Peta (object)**

| Maksud | Kalimat |
|--------|---------|
| Buat peta | `aku menyiapkan peta bernama data yang berisi nama = "Kaisar", umur = 21` |
| Ambil properti | `anggota "nama" dari wadah data` |
| Ambil jalur aman | `anggota dalam "book.list" dari wadah data` |
| Ubah properti | `aku mengubah anggota "umur" dari peta data menjadi 22` |
| Cek properti | `jika wadah data memiliki "umur" maka` |
| Gabung peta | `hasil dari kebiasaan gabung_peta dengan wadah a, wadah b` |

**JSON**

| Maksud | Kalimat |
|--------|---------|
| Urai JSON | `aku mengurai JSON dari wadah teks ke dalam wadah data` |
| Susun JSON | `aku menyusun JSON dari wadah data ke dalam wadah teks` |

**HTTP**

| Maksud | Kalimat |
|--------|---------|
| GET | `aku meminta GET dari "https://situs/api" ke dalam wadah balasan` |
| GET (URL variabel) | `aku meminta GET dari wadah url ke dalam wadah balasan` |
| POST berisi JSON | `aku meminta POST ke "https://situs/api" dengan isi wadah data ke dalam wadah balasan` |
| Atur kepala (header) | `aku mengatur kepala permintaan dari wadah kepala` |
| Atur jeda (timeout) | `aku mengatur jeda permintaan menjadi 15 detik` |

`wadah balasan` berisi peta: `anggota "status"` (kode HTTP),
`anggota "ok"` (benar/salah), `anggota "teks"` (isi balasan).

**Loop baru**

| Maksud | Kalimat |
|--------|---------|
| Untuk setiap item | `untuk setiap item dalam deret buah, ulangi` … `selesai` |
| Untuk rentang angka | `untuk setiap angka dari 1 sampai 40, ulangi` … `selesai` |

**Teks, pola, dan tipe**

| Maksud | Kalimat / ungkapan |
|--------|--------------------|
| Rapikan spasi | `hasil dari kebiasaan pangkas dengan wadah x` |
| Ganti teks | `hasil dari kebiasaan ganti dengan wadah x, "a", "b"` |
| Pisah / gabung | `hasil dari kebiasaan pisah dengan wadah x, ","` · `hasil dari kebiasaan gabung dengan wadah d, ","` |
| Cocok pola (regex) | `jika wadah x cocok dengan pola "[0-9]+" maka` |
| Ganti pola (regex) | `hasil dari kebiasaan ganti_pola dengan wadah x, "[^A-Za-z ]", ""` |
| Cari pola | `hasil dari kebiasaan cari_pola dengan wadah x, "[0-9]+"` |
| Uji tipe | `wadah x adalah deret` / `adalah peta` / `adalah teks` / `adalah angka` / `adalah himpunan` / `adalah kosong` |
| Teks <-> angka | `teks dari wadah x` · `angka dari wadah x` |

**Galat, argumen, keluar, tunggu**

| Maksud | Kalimat |
|--------|---------|
| Tangkap galat | `coba` … `jika gagal` … `selesai` (pesan tersedia di `wadah galat`) |
| Argumen terminal | `aku membaca argumen ke dalam wadah masuk` |
| Keluar | `aku mengakhiri dengan kode 2` |
| Jeda | `aku menunggu 200 milidetik` |
| Nilai bawaan | `aku membuat kebiasaan bernama f yang menerima a, b = 10` |

### 7. Contoh lengkap

```
# Bab 1: Resep Pertambahan
aku membuat kebiasaan bernama tambah yang menerima a, b
    aku mengembalikan wadah a + wadah b.
selesai.

# Bab 2: Memakai Resep
aku menyiapkan wadah bernama hasil yang berisi hasil dari kebiasaan tambah dengan 7, 5.
aku berkata: "Hasilnya " + wadah hasil.
```

---

## Penganalisis Semantik

`insjay periksa berkas.Jay` memeriksa:

- wadah dipakai sebelum pernah disiapkan;
- kebiasaan dipanggil sebelum pernah dibuat;
- jumlah isian tidak cocok dengan jumlah parameter;
- `mengembalikan` dipakai di luar kebiasaan;
- **peringatan**: wadah/kebiasaan yang tidak pernah dipakai.

---

## Uji

```bash
python3 uji/uji.py
```

---

## Struktur Proyek

```
insJaY/
├── README.md
├── LICENSE
├── pyproject.toml
├── .gitignore
├── src/insjayvm/        # compiler + runtime sendiri
│   ├── lexer.py
│   ├── parser.py
│   ├── semantik.py
│   ├── kompilator.py
│   ├── vm.py
│   ├── pipa.py
│   └── cli.py
├── contoh/              # contoh cerita .Jay
│   ├── halo.Jay
│   ├── fizzbuzz.Jay
│   ├── kalkulator.Jay
│   ├── pustaka.Jay
│   ├── sapa_skrip.Jay
│   └── cerita/
│       ├── tokoh.Jay
│       └── utama.Jay
└── uji/uji.py
```

---

## Target Web (opsional)

Untuk membuat aplikasi web, insJaY juga punya **target JavaScript** di folder
[`target-web/`](target-web/) (compiler `.Jay` → JavaScript/HTML, butuh Node.js).
Itu opsional; inti bahasa tetap berjalan tanpa Node lewat Mesin insJaY di sini.

---

## Peta Jalan

- [x] **v0.1** — inti bahasa: wadah, ungkapan, `jika`, `selama`, `kebiasaan`.
- [x] **v0.2** — masukan pengguna, penyambungan cerita, pemeriksa koherensi.
- [x] **v0.5** — **compiler bytecode + Mesin insJaY sendiri**, pustaka bawaan,
      CLI `insjay`, AST & analisis semantik yang bisa ditampilkan.
- [ ] **v0.6** — daftar (`deret`) dan pengulangan `untuk setiap`.
- [ ] **v0.7** — berkas (`baca dari` / `tulis ke`) dan modul `.Jay` sebagai pustaka.
- [ ] **v1.0** — taman contoh cerita komunitas + situs dokumentasi.

---

## Lisensi

[MIT](LICENSE) — bebas dipakai, diubah, dan dibagikan.
