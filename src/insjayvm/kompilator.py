# -*- coding: utf-8 -*-
"""insJaY — TAHAP 5: KOMPILASI ke BYTECODE.

AST -> bytecode untuk Mesin insJaY (runtime sendiri, tanpa Node/JS).

Bentuk bytecode (JSON):
{
  "versi": "0.5.0",
  "konstanta": [ ... ],
  "fungsi": { "nama": {"params": [...], "kode": [ ... ]} },
  "kode": [ {"op": "...", "arg": ...}, ... ]
}
"""

from .lexer import GalatInsJay, JENIS_WEB

VERSI_BYTECODE = "0.5.0"

# Perintah yang hanya hidup di target web (JS), bukan di Mesin insJaY.
PESAN_WEB = (
    "Perintah 'halaman' hanya hidup di target web (cli-node), "
    "bukan di Mesin insJaY. Gunakan mesin JS/web untuk web app."
)
PESAN_MODUL = (
    "Perintah '%s' hanya didukung target JS (Node/npm). "
    "Mesin insJaY berdiri sendiri tanpa modul luar; pakai pustaka bawaan "
    "(akar, pangkat, bulat, lantai, acak, waktu_sekarang)."
)

# Peta jenis kalimat web -> pesan galat yang enak dibaca


class Kompilator:
    def __init__(self):
        self.konstanta = []
        self.peta = {}
        self.fungsi = {}

    # -- utilitas -------------------------------------------------------------
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

    # -- ungkapan -------------------------------------------------------------
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
        elif t == "Kebenaran":
            self.kompil_ungkapan(node["expr"], out)
            self.emit(out, "OP", "kebenaran")
        else:
            raise GalatInsJay("Ungkapan '%s' belum bisa dikompilasi." % t)

    # -- kalimat --------------------------------------------------------------
    def kompil_kalimat(self, node, out):
        t = node["t"]
        if t == "Bab":
            return
        if t == "Let":
            self.kompil_ungkapan(node["nilai"], out)
            self.emit(out, "STORE", node["nama"])
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
