class Penganalisis:
    BAWAAN = {
        "akar": 1, "pangkat": 2, "bulat": 1, "lantai": 1, "acak": 0,
        "waktu_sekarang": 0, "pangkas": 1, "ganti": 3, "pisah": 2, "gabung": 2,
        "cocok_pola": 2, "ganti_pola": 3, "cari_pola": 2, "gabung_peta": 2,
        "anggota": 2, "punya": 2, "jenis": 1, "tidur": 1,
        "http_get": 1, "http_post": 2,
        "baca_berkas": 1, "tulis_berkas": 2, "tambah_berkas": 2, "ada_berkas": 1,
        "hapus_berkas": 1, "daftar_berkas": 1, "buat_folder": 1, "ukuran_berkas": 1,
        "folder_kerja": 0, "gabung_jalur": 2,
        "hash_md5": 1, "hash_sha1": 1, "hash_sha256": 1,
        "base64_susun": 1, "base64_urai": 1,
        "lingkungan": 1, "nama_sistem": 0, "versi_python": 0,
    }

    def __init__(self):
        self.diagnostik = []
        self.kerangka = [{}]
        self.fungsi = {}
        self.dalam_fungsi = 0
        self.jumlah_bab = 0
        self.jumlah_kalimat = 0

    def galat(self, n, pesan):
        self.diagnostik.append({"tingkat": "galat", "pesan": pesan,
                                "baris": n.get("baris"), "berkas": n.get("berkas")})

    def peringatan(self, n, pesan):
        self.diagnostik.append({"tingkat": "peringatan", "pesan": pesan,
                                "baris": n.get("baris"), "berkas": n.get("berkas")})

    def bawah(self):
        return self.kerangka[-1]

    def dorong(self):
        self.kerangka.append({})

    def tarik(self):
        f = self.kerangka.pop()
        for nama, info in f.items():
            if not info["dipakai"]:
                self.peringatan(info["simpul"], "Wadah '%s' disiapkan tetapi tidak pernah dipakai." % nama)

    def deklare(self, nama, simpul):
        self.bawah()[nama] = {"simpul": simpul, "dipakai": False}

    def ada(self, nama):
        return any(nama in f for f in self.kerangka)

    def tandai(self, nama):
        for f in reversed(self.kerangka):
            if nama in f:
                f[nama]["dipakai"] = True
                return

    def periksa_ungkapan(self, n, asal):
        if n is None:
            return
        t = n["t"]
        if t in ("Angka", "Teks", "Benar", "Salah"):
            return
        if t in ("Wadah", "Panjang", "KeAngka", "HurufKecil", "HurufBesar",
                 "KeTeks", "AnggotaPeta", "AnggotaDeret", "AnggotaJalur"):
            if not self.ada(n["nama"]):
                self.galat(asal, "Wadah '%s' dipakai sebelum pernah disiapkan." % n["nama"])
            else:
                self.tandai(n["nama"])
        elif t == "Panggilan":
            for a in n["args"]:
                self.periksa_ungkapan(a, asal)
            self.periksa_panggilan(n["nama"], len(n["args"]), asal)
        elif t in ("Biner", "Logika"):
            self.periksa_ungkapan(n["kiri"], asal)
            self.periksa_ungkapan(n["kanan"], asal)
        elif t == "Tidak":
            self.periksa_ungkapan(n["anak"], asal)
        elif t in ("Kondisi", "Mengandung", "Memiliki", "Memuat", "CocokPola"):
            self.periksa_ungkapan(n["kiri"], asal)
            self.periksa_ungkapan(n["kanan"], asal)
        elif t == "Adalah":
            self.periksa_ungkapan(n["kiri"], asal)
        elif t == "Kebenaran":
            self.periksa_ungkapan(n["expr"], asal)

    def periksa_panggilan(self, nama, jumlah_arg, asal):
        if nama in self.BAWAAN:
            if self.BAWAAN[nama] != jumlah_arg:
                self.galat(asal, "Pustaka '%s' menerima %d isian, tetapi diberi %d."
                           % (nama, self.BAWAAN[nama], jumlah_arg))
            return
        if nama not in self.fungsi:
            self.galat(asal, "Kebiasaan '%s' dipanggil tetapi belum pernah dibuat." % nama)
            return
        f = self.fungsi[nama]
        f["dipakai"] = True
        wajib = f.get("wajib", f["jumlah"])
        if jumlah_arg < wajib or jumlah_arg > f["jumlah"]:
            rentang = "%d" % f["jumlah"] if wajib == f["jumlah"] else "%d sampai %d" % (wajib, f["jumlah"])
            self.galat(asal, "Kebiasaan '%s' menerima %s isian, tetapi diberi %d."
                       % (nama, rentang, jumlah_arg))

    def analisis(self, program):
        for n in program["isi"]:
            self.kalimat(n)
        self.tarik()
        for nama, info in self.fungsi.items():
            if not info["dipakai"]:
                self.peringatan(info["simpul"], "Kebiasaan '%s' dibuat tetapi tidak pernah dipanggil." % nama)
        return {
            "diagnostik": self.diagnostik,
            "ringkasan": {
                "bab": self.jumlah_bab,
                "kalimat": self.jumlah_kalimat,
                "fungsi": len(self.fungsi),
                "galat": sum(1 for d in self.diagnostik if d["tingkat"] == "galat"),
                "peringatan": sum(1 for d in self.diagnostik if d["tingkat"] == "peringatan"),
            },
        }

    def kalimat(self, n):
        self.jumlah_kalimat += 1
        t = n["t"]
        if t == "Bab":
            self.jumlah_bab += 1
        elif t == "Let":
            self.periksa_ungkapan(n["nilai"], n)
            self.deklare(n["nama"], n)
        elif t in ("Set", "Tambah", "Kurang"):
            if not self.ada(n["nama"]):
                self.galat(n, "Wadah '%s' diubah sebelum pernah disiapkan." % n["nama"])
            else:
                self.tandai(n["nama"])
            self.periksa_ungkapan(n["nilai"], n)
        elif t == "Berkata":
            self.periksa_ungkapan(n["nilai"], n)
        elif t == "Tanya":
            self.periksa_ungkapan(n["pertanyaan"], n)
            self.deklare(n["nama"], n)
        elif t == "Jika":
            self.periksa_ungkapan(n["kondisi"], n)
            for a in n["tubuh"]:
                self.kalimat(a)
            for a in n["lain"]:
                self.kalimat(a)
        elif t == "Selama":
            self.periksa_ungkapan(n["kondisi"], n)
            for a in n["tubuh"]:
                self.kalimat(a)
        elif t == "Kebiasaan":
            bawaan_k = n.get("bawaan") or [None] * len(n["params"])
            wajib = sum(1 for b in bawaan_k if b is None)
            self.fungsi[n["nama"]] = {"jumlah": len(n["params"]), "wajib": wajib,
                                       "simpul": n, "dipakai": False}
            self.dorong()
            for p in n["params"]:
                self.deklare(p, n)
            for b in (n.get("bawaan") or []):
                if b is not None:
                    self.periksa_ungkapan(b, n)
            self.dalam_fungsi += 1
            for a in n["tubuh"]:
                self.kalimat(a)
            self.dalam_fungsi -= 1
            self.tarik()
        elif t == "Panggil":
            for a in n["args"]:
                self.periksa_ungkapan(a, n)
            self.periksa_panggilan(n["nama"], len(n["args"]), n)
        elif t == "Kembali":
            if self.dalam_fungsi == 0:
                self.galat(n, "'mengembalikan' hanya boleh dipakai di dalam sebuah kebiasaan.")
            self.periksa_ungkapan(n["nilai"], n)
        elif t == "Sambung":
            self.galat(n, "Penyambungan cerita '%s' belum diselesaikan." % n["berkas"])
        elif t == "Halaman":
            self.periksa_ungkapan(n["judul"], n)
        elif t in ("Judul", "Paragraf", "Jawaban", "GantiJawaban"):
            self.periksa_ungkapan(n["nilai"], n)
        elif t == "Isian":
            pass
        elif t == "Tombol":
            self.periksa_ungkapan(n["label"], n)
            if n["fungsi"] not in self.fungsi:
                self.galat(n, "Tombol memanggil kebiasaan '%s' yang belum pernah dibuat." % n["fungsi"])
            else:
                self.fungsi[n["fungsi"]]["dipakai"] = True
        elif t == "BacaIsian":
            self.deklare(n["sasaran"], n)
        elif t == "Deret":
            for x in n["isi"]:
                self.periksa_ungkapan(x, n)
            self.deklare(n["nama"], n)
        elif t == "Peta":
            for _, v in n["pasangan"]:
                self.periksa_ungkapan(v, n)
            self.deklare(n["nama"], n)
        elif t == "Himpunan":
            self.deklare(n["nama"], n)
        elif t in ("DeretTambah", "HimpunanTambah"):
            if not self.ada(n["nama"]):
                self.galat(n, "Wadah '%s' dipakai sebelum pernah disiapkan." % n["nama"])
            else:
                self.tandai(n["nama"])
            self.periksa_ungkapan(n["nilai"], n)
        elif t in ("PetaUbah", "DeretUbah"):
            if not self.ada(n["nama"]):
                self.galat(n, "Wadah '%s' dipakai sebelum pernah disiapkan." % n["nama"])
            else:
                self.tandai(n["nama"])
            self.periksa_ungkapan(n["nilai"], n)
        elif t in ("JsonUrai", "JsonSusun"):
            if not self.ada(n["sumber"]):
                self.galat(n, "Wadah '%s' dipakai sebelum pernah disiapkan." % n["sumber"])
            else:
                self.tandai(n["sumber"])
            self.deklare(n["sasaran"], n)
        elif t == "HttpGet":
            self.periksa_ungkapan(n["url"], n)
            self.deklare(n["sasaran"], n)
        elif t == "HttpPost":
            self.periksa_ungkapan(n["url"], n)
            if not self.ada(n["isi"]):
                self.galat(n, "Wadah '%s' dipakai sebelum pernah disiapkan." % n["isi"])
            else:
                self.tandai(n["isi"])
            self.deklare(n["sasaran"], n)
        elif t == "HttpKepala":
            if not self.ada(n["nama"]):
                self.galat(n, "Wadah '%s' dipakai sebelum pernah disiapkan." % n["nama"])
            else:
                self.tandai(n["nama"])
        elif t == "HttpJeda" or t == "Keluar" or t == "Tunggu":
            pass
        elif t == "SelamaDeret":
            if not self.ada(n["deret"]):
                self.galat(n, "Wadah '%s' dipakai sebelum pernah disiapkan." % n["deret"])
            else:
                self.tandai(n["deret"])
            self.deklare(n["item"], n)
            for a in n["tubuh"]:
                self.kalimat(a)
        elif t == "SelamaRentang":
            self.periksa_ungkapan(n["dari"], n)
            self.periksa_ungkapan(n["sampai"], n)
            self.deklare(n["item"], n)
            for a in n["tubuh"]:
                self.kalimat(a)
        elif t == "Coba":
            for a in n["tubuh"]:
                self.kalimat(a)
            self.dorong()
            self.deklare("galat", n)
            for a in n["gagal"]:
                self.kalimat(a)
            self.tarik()
        elif t == "Argumen":
            self.deklare(n["nama"], n)
        elif t == "Ambil":
            self.deklare(n["nama"], n)
        elif t == "Serahkan":
            if n["nama"] not in self.fungsi:
                self.galat(n, "Kebiasaan '%s' diserahkan ke dunia tetapi belum pernah dibuat." % n["nama"])
            else:
                self.fungsi[n["nama"]]["dipakai"] = True


def analisis(program):
    return Penganalisis().analisis(program)
