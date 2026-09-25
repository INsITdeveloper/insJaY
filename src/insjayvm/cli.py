import json
import os
import sys

from . import pipa
from .lexer import GalatInsJay
from .parser import Parser
from .semantik import analisis
from .vm import Mesin
from . import __version__

BANTUAN = """
insJaY v%s — bahasa pemrograman naratif Indonesia (.Jay)
Compiler + runtime sendiri (bytecode + Mesin insJaY, tanpa Node/JS)

PEMAKAIAN
  insjay <berkas.Jay>              jalankan cerita
  insjay jalankan <berkas>         jalankan cerita (alias: run)
  insjay kompilasi <berkas>        kompilasi ke bytecode  (-o keluar.Jayc)
  insjay jalankan <berkas.Jayc>    jalankan bytecode hasil kompilasi
  insjay periksa <berkas>          analisis semantik (galat/peringatan)
  insjay ast <berkas>              tampilkan pohon AST
  insjay lex <berkas>              tampilkan token hasil lexing
  insjay bytecode <berkas>         tampilkan bytecode hasil kompilasi
  insjay versi                     tampilkan versi
  insjay bantuan                   tampilkan bantuan ini

CONTOH
  insjay contoh/halo.Jay
  insjay kompilasi contoh/fizzbuzz.Jay -o fizzbuzz.Jayc
  insjay jalankan fizzbuzz.Jayc
  printf "Budi\\n15\\n" | insjay contoh/sapa_skrip.Jay
""" % __version__


def masukan_stdin(prompt):
    if prompt:
        sys.stdout.write(str(prompt) + " ")
        sys.stdout.flush()
    baris = sys.stdin.readline()
    if baris == "":
        return ""
    return baris.rstrip("\n").rstrip("\r")


def _analisis_saja(berkas):
    p = os.path.abspath(berkas)
    tokens, ast = pipa.baca_ast(p)
    datar = pipa.selesaikan_impor(ast["isi"], os.path.dirname(p), {p})
    program = {"t": "Program", "isi": datar}
    return analisis(program), ast


def laporkan(diagnostik):
    bersih = True
    for d in diagnostik:
        lokasi = d.get("berkas") or ""
        if lokasi and d.get("baris"):
            lokasi = "%s:%s" % (lokasi, d["baris"])
        tail = ("  (%s)" % lokasi) if lokasi else ""
        if d["tingkat"] == "galat":
            bersih = False
            sys.stderr.write("  x [galat] %s%s\n" % (d["pesan"], tail))
        else:
            sys.stderr.write("  ! [peringatan] %s%s\n" % (d["pesan"], tail))
    return bersih


def _u(n):
    t = n["t"]
    if t == "Angka":
        return str(n["nilai"])
    if t == "Teks":
        return json.dumps(n["nilai"], ensure_ascii=False)
    if t == "Benar":
        return "benar"
    if t == "Salah":
        return "salah"
    if t == "Wadah":
        return "wadah %s" % n["nama"]
    if t == "Panjang":
        return "panjang dari wadah %s" % n["nama"]
    if t == "KeAngka":
        return "angka dari wadah %s" % n["nama"]
    if t == "HurufKecil":
        return "huruf kecil dari wadah %s" % n["nama"]
    if t == "HurufBesar":
        return "huruf besar dari wadah %s" % n["nama"]
    if t == "Panggilan":
        return "%s(%s)" % (n["nama"], ", ".join(_u(a) for a in n["args"]))
    if t == "Biner":
        return "(%s %s %s)" % (_u(n["kiri"]), n["op"], _u(n["kanan"]))
    if t == "Logika":
        return "(%s %s %s)" % (_u(n["kiri"]), n["op"], _u(n["kanan"]))
    if t == "Tidak":
        return "tidak %s" % _u(n["anak"])
    if t == "Kondisi":
        return "(%s %s %s)" % (_u(n["kiri"]), n["frasa"], _u(n["kanan"]))
    if t == "Mengandung":
        return "(%s mengandung %s)" % (_u(n["kiri"]), _u(n["kanan"]))
    if t == "Kebenaran":
        return _u(n["expr"])
    return t


def ringkas(n, level=0):
    j = "  " * level
    t = n["t"]
    if t == "Bab":
        return j + "BAB: " + n["judul"]
    if t == "Let":
        return "%sLET %s = %s" % (j, n["nama"], _u(n["nilai"]))
    if t == "Set":
        return "%sSET %s = %s" % (j, n["nama"], _u(n["nilai"]))
    if t == "Tambah":
        return "%sTAMBAH %s += %s" % (j, n["nama"], _u(n["nilai"]))
    if t == "Kurang":
        return "%sKURANG %s -= %s" % (j, n["nama"], _u(n["nilai"]))
    if t == "Berkata":
        return j + "BERKATA " + _u(n["nilai"])
    if t == "Tanya":
        return "%sTANYA -> wadah %s (%s)" % (j, n["nama"], _u(n["pertanyaan"]))
    if t == "Jika":
        baris = ["%sJIKA %s" % (j, _u(n["kondisi"]))]
        baris += [ringkas(a, level + 1) for a in n["tubuh"]]
        if n["lain"]:
            baris.append(j + "KALAU TIDAK")
            baris += [ringkas(a, level + 1) for a in n["lain"]]
        baris.append(j + "SELESAI")
        return "\n".join(baris)
    if t == "Selama":
        baris = ["%sSELAMA %s" % (j, _u(n["kondisi"]))]
        baris += [ringkas(a, level + 1) for a in n["tubuh"]]
        baris.append(j + "SELESAI")
        return "\n".join(baris)
    if t == "Kebiasaan":
        baris = ["%sKEBIASAAN %s(%s)" % (j, n["nama"], ", ".join(n["params"]))]
        baris += [ringkas(a, level + 1) for a in n["tubuh"]]
        baris.append(j + "SELESAI")
        return "\n".join(baris)
    if t == "Panggil":
        return "%sPANGGIL %s(%s)" % (j, n["nama"], ", ".join(_u(a) for a in n["args"]))
    if t == "Kembali":
        return j + "KEMBALI " + _u(n["nilai"])
    if t == "Sambung":
        return '%sSAMBUNG "%s"' % (j, n["berkas"])
    return "%s%s" % (j, t)


def ambil_opsi(argv):
    sisa, keluaran = [], None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("-o", "--keluaran"):
            i += 1
            keluaran = argv[i] if i < len(argv) else None
        else:
            sisa.append(a)
        i += 1
    return sisa, keluaran


def pastikan_ada(berkas):
    if not berkas:
        sys.stderr.write("Sebutkan berkas .Jay. Contoh: insjay jalankan contoh/halo.Jay\n")
        sys.exit(2)
    if not os.path.exists(berkas):
        sys.stderr.write("Berkas '%s' tidak ditemukan.\n" % berkas)
        sys.exit(2)


def cmd_jalankan(berkas):
    pastikan_ada(berkas)
    if berkas.endswith(".Jayc") or pipa.apakah_bytecode(berkas):
        bytecode = pipa.muat_bytecode(berkas)
    else:
        hasil = pipa.proses(berkas)
        if not laporkan(hasil["analisis"]["diagnostik"]):
            sys.stderr.write("\n[Kisah terhenti] Perbaiki galat di atas dahulu.\n")
            sys.exit(1)
        bytecode = hasil["bytecode"]
    Mesin(bytecode, masukan=masukan_stdin).jalankan()


def cmd_kompilasi(berkas, keluaran):
    pastikan_ada(berkas)
    hasil = pipa.proses(berkas)
    laporkan(hasil["analisis"]["diagnostik"])
    if keluaran:
        pipa.simpan_bytecode(hasil["bytecode"], keluaran)
        print("Berhasil ditulis: %s" % keluaran)
    else:
        sys.stdout.write(json.dumps(hasil["bytecode"], ensure_ascii=False, indent=1) + "\n")


def cmd_periksa(berkas):
    pastikan_ada(berkas)
    hasil, _ = _analisis_saja(berkas)
    r = hasil["ringkasan"]
    print("Periksa semantik: %s" % os.path.basename(berkas))
    print("  Bab (narasi)      : %d" % r["bab"])
    print("  Kalimat perintah  : %d" % (r["kalimat"] - r["bab"]))
    print("  Kebiasaan (fungsi): %d" % r["fungsi"])
    print("  Galat             : %d" % r["galat"])
    print("  Peringatan        : %d" % r["peringatan"])
    bersih = laporkan(hasil["diagnostik"])
    print("  Status            : %s" % ("SEMUA KALIMAT MENGIKUTI ALUR CERITA OK" if bersih else "ADA MASALAH"))
    sys.exit(0 if bersih else 1)


def cmd_ast(berkas):
    pastikan_ada(berkas)
    _, ast = pipa.baca_ast(os.path.abspath(berkas))
    if os.environ.get("INSJAY_AST_JSON"):
        sys.stdout.write(json.dumps(ast, ensure_ascii=False, indent=2) + "\n")
    else:
        print("\n".join(ringkas(n) for n in ast["isi"]))


def cmd_lex(berkas):
    pastikan_ada(berkas)
    tokens, _ = pipa.baca_ast(os.path.abspath(berkas))
    for t in tokens:
        isi = t["judul"] if t["jenis"] == "BAB" else " | ".join(g for g in (t["m"] or []) if g)
        print("%4d  %-14s %s" % (t["baris"], t["jenis"], isi))


def cmd_bytecode(berkas):
    pastikan_ada(berkas)
    hasil = pipa.proses(berkas)
    sys.stdout.write(json.dumps(hasil["bytecode"], ensure_ascii=False, indent=1) + "\n")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print(BANTUAN)
        return 0
    perintah = argv[0]
    if perintah in ("versi", "-v", "--version"):
        print("insJaY CLI v%s (compiler + runtime sendiri)" % __version__)
        return 0
    if perintah in ("bantuan", "-h", "--help"):
        print(BANTUAN)
        return 0

    sisa, keluaran = ambil_opsi(argv[1:])
    try:
        if perintah in ("jalankan", "run"):
            cmd_jalankan(sisa[0] if sisa else None)
        elif perintah in ("kompilasi", "build"):
            cmd_kompilasi(sisa[0] if sisa else None, keluaran)
        elif perintah in ("periksa", "check"):
            cmd_periksa(sisa[0] if sisa else None)
        elif perintah == "ast":
            cmd_ast(sisa[0] if sisa else None)
        elif perintah == "lex":
            cmd_lex(sisa[0] if sisa else None)
        elif perintah == "bytecode":
            cmd_bytecode(sisa[0] if sisa else None)
        else:
            if perintah.endswith(".Jay") or perintah.endswith(".Jayc") or os.path.exists(perintah):
                cmd_jalankan(perintah)
            else:
                sys.stderr.write("Perintah '%s' tidak dikenal.\n%s\n" % (perintah, BANTUAN))
                return 2
    except GalatInsJay as e:
        sys.stderr.write("[Gagal] %s\n" % e.format())
        return 1
    except RecursionError:
        sys.stderr.write("[Gagal] Cerita terlalu dalam / berputar.\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
