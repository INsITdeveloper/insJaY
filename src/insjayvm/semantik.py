class Penganalisis:
    BAWAAN = {
        "akar": 1, "pangkat": 2, "bulat": 1, "lantai": 1, "acak": 0,
        "waktu_sekarang": 0,
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
        if t in ("Wadah", "Panjang", "KeAngka", "HurufKecil", "HurufBesar"):
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
        elif t in ("Kondisi", "Mengandung"):
            self.periksa_ungkapan(n["kiri"], asal)
            self.periksa_ungkapan(n["kanan"], asal)
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
        if f["jumlah"] != jumlah_arg:
            self.galat(asal, "Kebiasaan '%s' menerima %d isian, tetapi diberi %d."
                       % (nama, f["jumlah"], jumlah_arg))

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
            self.fungsi[n["nama"]] = {"jumlah": len(n["params"]), "simpul": n, "dipakai": False}
            self.dorong()
            for p in n["params"]:
                self.deklare(p, n)
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
        elif t == "Ambil":
            self.deklare(n["nama"], n)
        elif t == "Serahkan":
            if n["nama"] not in self.fungsi:
                self.galat(n, "Kebiasaan '%s' diserahkan ke dunia tetapi belum pernah dibuat." % n["nama"])
            else:
                self.fungsi[n["nama"]]["dipakai"] = True


def analisis(program):
    return Penganalisis().analisis(program)
