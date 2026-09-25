from .lexer import GalatInsJay, JENIS_WEB

VERSI_BYTECODE = "0.7.0"

PESAN_WEB = (
    "Perintah 'halaman' hanya hidup di target web (cli-node), "
    "bukan di Mesin insJaY. Gunakan mesin JS/web untuk web app."
)
PESAN_MODUL = (
    "Perintah '%s' hanya didukung target JS (Node/npm). "
    "Mesin insJaY berdiri sendiri tanpa modul luar; pakai pustaka bawaan "
    "(akar, pangkat, bulat, lantai, acak, waktu_sekarang)."
)



class Kompilator:
    def __init__(self):
        self.konstanta = []
        self.peta = {}
        self.fungsi = {}
        self.tmp = 0

    def k(self, v):
        kunci = (type(v).__name__, v)
        if kunci in self.peta:
            return self.peta[kunci]
        idx = len(self.konstanta)
        self.konstanta.append(v)
        self.peta[kunci] = idx
        return idx

    def emit(self, out, op, arg=None):
        if arg is None:
            out.append({"op": op})
        else:
            out.append({"op": op, "arg": arg})
        return len(out) - 1

    def kompil_ungkapan(self, node, out):
        t = node["t"]
        if t in ("Angka", "Teks"):
            self.emit(out, "PUSH", self.k(node["nilai"]))
        elif t == "Benar":
            self.emit(out, "PUSH", self.k(True))
        elif t == "Salah":
            self.emit(out, "PUSH", self.k(False))
        elif t == "Wadah":
            self.emit(out, "LOAD", node["nama"])
        elif t == "Panjang":
            self.emit(out, "LOAD", node["nama"])
            self.emit(out, "OP", "panjang")
        elif t == "KeAngka":
            self.emit(out, "LOAD", node["nama"])
            self.emit(out, "OP", "keangka")
        elif t == "HurufKecil":
            self.emit(out, "LOAD", node["nama"])
            self.emit(out, "OP", "hurufkecil")
        elif t == "HurufBesar":
            self.emit(out, "LOAD", node["nama"])
            self.emit(out, "OP", "hurufbesar")
        elif t == "KeTeks":
            self.emit(out, "LOAD", node["nama"])
            self.emit(out, "OP", "keteks")
        elif t == "AnggotaPeta":
            self.emit(out, "LOAD", node["nama"])
            self.emit(out, "PUSH", self.k(node["kunci"]))
            self.emit(out, "OP", "anggotapeta")
        elif t == "AnggotaDeret":
            self.emit(out, "LOAD", node["nama"])
            self.emit(out, "PUSH", self.k(node["indeks"]))
            self.emit(out, "OP", "anggotaderet")
        elif t == "AnggotaJalur":
            self.emit(out, "LOAD", node["nama"])
            self.emit(out, "PUSH", self.k(node["jalur"]))
            self.emit(out, "OP", "jalur")
        elif t == "Panggilan":
            for a in node["args"]:
                self.kompil_ungkapan(a, out)
            self.emit(out, "CALL", [node["nama"], len(node["args"])])
        elif t == "Biner":
            self.kompil_ungkapan(node["kiri"], out)
            self.kompil_ungkapan(node["kanan"], out)
            self.emit(out, "OP", node["op"])
        elif t == "Logika":
            self.kompil_ungkapan(node["kiri"], out)
            self.kompil_ungkapan(node["kanan"], out)
            self.emit(out, "OP", node["op"])
        elif t == "Tidak":
            self.kompil_ungkapan(node["anak"], out)
            self.emit(out, "OP", "tidak")
        elif t == "Kondisi":
            self.kompil_ungkapan(node["kiri"], out)
            self.kompil_ungkapan(node["kanan"], out)
            self.emit(out, "OP", node["op"])
        elif t == "Mengandung":
            self.kompil_ungkapan(node["kiri"], out)
            self.kompil_ungkapan(node["kanan"], out)
            self.emit(out, "OP", "mengandung")
        elif t in ("Memiliki", "Memuat", "CocokPola"):
            self.kompil_ungkapan(node["kiri"], out)
            self.kompil_ungkapan(node["kanan"], out)
            self.emit(out, "OP", {"Memiliki": "memiliki", "Memuat": "memuat", "CocokPola": "cocokpola"}[t])
        elif t == "Adalah":
            self.kompil_ungkapan(node["kiri"], out)
            self.emit(out, "PUSH", self.k(node["jenis"]))
            self.emit(out, "OP", "adalah")
        elif t == "Kebenaran":
            self.kompil_ungkapan(node["expr"], out)
            self.emit(out, "OP", "kebenaran")
        else:
            raise GalatInsJay("Ungkapan '%s' belum bisa dikompilasi." % t)

    def kompil_kalimat(self, node, out):
        t = node["t"]
        if t == "Bab":
            return
        if t == "Let":
            self.kompil_ungkapan(node["nilai"], out)
            self.emit(out, "STORE", node["nama"])
        elif t == "Assign":
            self.kompil_ungkapan(node["nilai"], out)
            self.emit(out, "ASSIGN", node["nama"])
        elif t == "Set":
            self.kompil_ungkapan(node["nilai"], out)
            self.emit(out, "SIMPAN", node["nama"])
        elif t == "Tambah":
            self.emit(out, "LOAD", node["nama"])
            self.kompil_ungkapan(node["nilai"], out)
            self.emit(out, "OP", "+")
            self.emit(out, "SIMPAN", node["nama"])
        elif t == "Kurang":
            self.emit(out, "LOAD", node["nama"])
            self.kompil_ungkapan(node["nilai"], out)
            self.emit(out, "OP", "-")
            self.emit(out, "SIMPAN", node["nama"])
        elif t == "Berkata":
            self.kompil_ungkapan(node["nilai"], out)
            self.emit(out, "CETAK")
        elif t == "Tanya":
            self.kompil_ungkapan(node["pertanyaan"], out)
            self.emit(out, "TANYA")
            self.emit(out, "STORE", node["nama"])
        elif t == "Jika":
            self.kompil_ungkapan(node["kondisi"], out)
            lompat_salah = self.emit(out, "JIKA_SALAH", 0)
            for a in node["tubuh"]:
                self.kompil_kalimat(a, out)
            if node["lain"]:
                lompat_akhir = self.emit(out, "LONCAT", 0)
                out[lompat_salah]["arg"] = len(out)
                for a in node["lain"]:
                    self.kompil_kalimat(a, out)
                out[lompat_akhir]["arg"] = len(out)
            else:
                out[lompat_salah]["arg"] = len(out)
        elif t == "Selama":
            mulai = len(out)
            self.kompil_ungkapan(node["kondisi"], out)
            lompat_salah = self.emit(out, "JIKA_SALAH", 0)
            for a in node["tubuh"]:
                self.kompil_kalimat(a, out)
            self.emit(out, "LONCAT", mulai)
            out[lompat_salah]["arg"] = len(out)
        elif t == "Kebiasaan":
            isi = []
            bawaan = node.get("bawaan") or [None] * len(node["params"])
            for nama_p, nilai_b in zip(node["params"], bawaan):
                if nilai_b is None:
                    continue
                self.emit(isi, "LOAD", nama_p)
                self.emit(isi, "OP", "hilang")
                lompat = self.emit(isi, "JIKA_SALAH", 0)
                self.kompil_ungkapan(nilai_b, isi)
                self.emit(isi, "STORE", nama_p)
                isi[lompat]["arg"] = len(isi)
            for a in node["tubuh"]:
                self.kompil_kalimat(a, isi)
            self.fungsi[node["nama"]] = {"params": node["params"], "kode": isi}
        elif t == "Panggil":
            for a in node["args"]:
                self.kompil_ungkapan(a, out)
            self.emit(out, "CALL", [node["nama"], len(node["args"])])
            self.emit(out, "POP")
        elif t == "Kembali":
            self.kompil_ungkapan(node["nilai"], out)
            self.emit(out, "KEMBALI")
        elif t == "Deret":
            for x in node["isi"]:
                self.kompil_ungkapan(x, out)
            self.emit(out, "BUAT_DERET", len(node["isi"]))
            self.emit(out, "STORE", node["nama"])
        elif t == "Peta":
            for _, v in node["pasangan"]:
                self.kompil_ungkapan(v, out)
            self.emit(out, "BUAT_PETA", [k for k, _ in node["pasangan"]])
            self.emit(out, "STORE", node["nama"])
        elif t == "Himpunan":
            self.emit(out, "BUAT_HIMPUNAN")
            self.emit(out, "STORE", node["nama"])
        elif t == "DeretTambah":
            self.emit(out, "LOAD", node["nama"])
            self.kompil_ungkapan(node["nilai"], out)
            self.emit(out, "DERET_TAMBAH")
        elif t == "HimpunanTambah":
            self.emit(out, "LOAD", node["nama"])
            self.kompil_ungkapan(node["nilai"], out)
            self.emit(out, "HIMPUNAN_TAMBAH")
        elif t == "PetaUbah":
            self.emit(out, "LOAD", node["nama"])
            self.emit(out, "PUSH", self.k(node["kunci"]))
            self.kompil_ungkapan(node["nilai"], out)
            self.emit(out, "PETA_SET")
        elif t == "DeretUbah":
            self.emit(out, "LOAD", node["nama"])
            self.emit(out, "PUSH", self.k(node["indeks"]))
            self.kompil_ungkapan(node["nilai"], out)
            self.emit(out, "DERET_SET")
        elif t == "JsonUrai":
            self.emit(out, "LOAD", node["sumber"])
            self.emit(out, "OP", "jsonurai")
            self.emit(out, "STORE", node["sasaran"])
        elif t == "JsonSusun":
            self.emit(out, "LOAD", node["sumber"])
            self.emit(out, "OP", "jsonsusun")
            self.emit(out, "STORE", node["sasaran"])
        elif t == "HttpGet":
            self.kompil_ungkapan(node["url"], out)
            self.emit(out, "HTTP_GET")
            self.emit(out, "STORE", node["sasaran"])
        elif t == "HttpPost":
            self.kompil_ungkapan(node["url"], out)
            self.emit(out, "LOAD", node["isi"])
            self.emit(out, "HTTP_POST")
            self.emit(out, "STORE", node["sasaran"])
        elif t == "HttpKepala":
            self.emit(out, "LOAD", node["nama"])
            self.emit(out, "HTTP_KEPALA")
        elif t == "HttpJeda":
            self.emit(out, "HTTP_JEDA", node["detik"])
        elif t == "SelamaDeret":
            self.tmp += 1
            tmp = "__ins_d%d" % self.tmp
            idx = "__ins_i%d" % self.tmp
            self.kompil_ungkapan({"t": "Wadah", "nama": node["deret"]}, out)
            self.emit(out, "STORE", tmp)
            self.emit(out, "PUSH", self.k(0))
            self.emit(out, "STORE", idx)
            mulai = len(out)
            self.emit(out, "LOAD", idx)
            self.emit(out, "LOAD", tmp)
            self.emit(out, "OP", "panjang")
            self.emit(out, "OP", "<")
            lompat = self.emit(out, "JIKA_SALAH", 0)
            self.emit(out, "LOAD", tmp)
            self.emit(out, "LOAD", idx)
            self.emit(out, "OP", "aksesderet")
            self.emit(out, "STORE", node["item"])
            for a in node["tubuh"]:
                self.kompil_kalimat(a, out)
            self.emit(out, "LOAD", idx)
            self.emit(out, "PUSH", self.k(1))
            self.emit(out, "OP", "+")
            self.emit(out, "STORE", idx)
            self.emit(out, "LONCAT", mulai)
            out[lompat]["arg"] = len(out)
        elif t == "SelamaRentang":
            self.tmp += 1
            item = node["item"]
            batas = "__ins_b%d" % self.tmp
            self.kompil_ungkapan(node["dari"], out)
            self.emit(out, "STORE", item)
            self.kompil_ungkapan(node["sampai"], out)
            self.emit(out, "STORE", batas)
            mulai = len(out)
            self.emit(out, "LOAD", item)
            self.emit(out, "LOAD", batas)
            self.emit(out, "OP", "<=")
            lompat = self.emit(out, "JIKA_SALAH", 0)
            for a in node["tubuh"]:
                self.kompil_kalimat(a, out)
            self.emit(out, "LOAD", item)
            self.emit(out, "PUSH", self.k(1))
            self.emit(out, "OP", "+")
            self.emit(out, "STORE", item)
            self.emit(out, "LONCAT", mulai)
            out[lompat]["arg"] = len(out)
        elif t == "Coba":
            mulai_coba = self.emit(out, "COBA_MULAI", 0)
            for a in node["tubuh"]:
                self.kompil_kalimat(a, out)
            self.emit(out, "COBA_SELESAI")
            lompat_akhir = self.emit(out, "LONCAT", 0)
            out[mulai_coba]["arg"] = len(out)
            self.emit(out, "STORE", "galat")
            for a in node["gagal"]:
                self.kompil_kalimat(a, out)
            out[lompat_akhir]["arg"] = len(out)
        elif t == "Argumen":
            self.emit(out, "ARGUMEN")
            self.emit(out, "STORE", node["nama"])
        elif t == "Keluar":
            self.emit(out, "KELUAR", node["kode"])
        elif t == "Tunggu":
            self.emit(out, "TUNGGU", node["milidetik"])
        elif t == "Sambung":
            raise GalatInsJay("Penyambungan cerita '%s' belum diselesaikan." % node["berkas"],
                              node["baris"], node["berkas"])
        elif t.upper() in JENIS_WEB:
            raise GalatInsJay(PESAN_WEB, node["baris"], node.get("berkas"))
        elif t in ("Ambil", "Serahkan"):
            raise GalatInsJay(PESAN_MODUL % ("mengambil dari" if t == "Ambil" else "menyerahkan kebiasaan"),
                              node["baris"], node.get("berkas"))
        else:
            raise GalatInsJay("Kalimat jenis '%s' belum bisa dikompilasi." % t,
                              node["baris"], node.get("berkas"))

    def kompilasi(self, program):
        out = []
        for node in program["isi"]:
            self.kompil_kalimat(node, out)
        self.emit(out, "SELESAI")
        return {
            "versi": VERSI_BYTECODE,
            "konstanta": self.konstanta,
            "fungsi": self.fungsi,
            "kode": out,
        }


def kompilasi(program):
    return Kompilator().kompilasi(program)
