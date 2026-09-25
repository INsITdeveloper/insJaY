import json
import os
import subprocess
import sys
import tempfile

AKAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(AKAR, "src")
ENV = dict(os.environ, PYTHONPATH=SRC)

lulus = 0
gagal = 0


def insjay(args, masukan=""):
    r = subprocess.run(
        [sys.executable, "-m", "insjayvm"] + args,
        input=masukan, capture_output=True, text=True, cwd=AKAR, env=ENV,
    )
    return r.stdout.strip(), r.stderr.strip(), r.returncode


def uji(nama, syarat):
    global lulus, gagal
    if syarat:
        lulus += 1
        print("  OK  " + nama)
    else:
        gagal += 1
        print("  XX  " + nama)


print("Menguji insJaY (Mesin bytecode)...\n")

out, _, kode = insjay(["contoh/halo.Jay"])
uji("halo.Jay berjalan", "Halo, dunia!" in out and kode == 0)

out, _, kode = insjay(["contoh/fizzbuzz.Jay"])
uji("fizzbuzz.Jay mencetak FizzBuzz", "FizzBuzz" in out and kode == 0)

out, _, _ = insjay(["contoh/kalkulator.Jay"])
uji("kalkulator.Jay menghitung 12 & 25", "12" in out and "25" in out)

out, _, _ = insjay(["contoh/cerita/utama.Jay"])
uji("impor multi-berkas nyambung", "Ayu tinggal di Bandung" in out)

out, _, _ = insjay(["contoh/sapa_skrip.Jay"], "Budi\n15\n")
uji("masukan pengguna terbaca", "Halo, Budi" in out and "3 tahun" in out)

out, _, _ = insjay(["contoh/pustaka.Jay"])
uji("pustaka bawaan (akar/pangkat/bulat)", "Akar dari 81 adalah 9" in out and "1024" in out)

out, _, _ = insjay(["periksa", "contoh/kalkulator.Jay"])
uji("periksa semantik lulus", "ALUR CERITA OK" in out)

out, _, _ = insjay(["lex", "contoh/halo.Jay"])
uji("lexing menghasilkan token", "BAB" in out and "LET" in out)

out, _, _ = insjay(["ast", "contoh/kalkulator.Jay"])
uji("AST terbentuk", "KEBIASAAN tambah" in out)

tmp = tempfile.mkdtemp()
bc = os.path.join(tmp, "fizz.Jayc")
insjay(["kompilasi", "contoh/fizzbuzz.Jay", "-o", bc])
uji("kompilasi menghasilkan berkas .Jayc", os.path.exists(bc))
out, _, _ = insjay(["jalankan", bc])
uji("bytecode .Jayc dijalankan Mesin", "FizzBuzz" in out)

with open(bc) as f:
    data = json.load(f)
uji("bytecode berisi instruksi + konstanta", "kode" in data and "konstanta" in data and data["versi"])

p1 = os.path.join(tmp, "g1.Jay")
open(p1, "w").write("# Bab 1\naku berkata: wadah hantu.\n")
out, err, kode = insjay(["periksa", p1])
uji("galat wadah tak dikenal terdeteksi", kode != 0 and "belum pernah disiapkan" in err)

p2 = os.path.join(tmp, "g2.Jay")
open(p2, "w").write('# Bab 1\naku berkata: "hai".\nngawur total\n')
out, err, kode = insjay(["jalankan", p2])
uji("kalimat tidak koheren ditolak", kode != 0 and "tidak mengikuti alur cerita" in err)

p3 = os.path.join(tmp, "g3.Jay")
open(p3, "w").write('# Bab 1\naku menyiapkan halaman bernama utama berjudul "Uji".\n')
out, err, kode = insjay(["jalankan", p3])
uji("perintah web ditolak mesin dengan pesan jelas", kode != 0 and "target web" in err)

print("\nSelesai: %d lulus, %d gagal." % (lulus, gagal))
sys.exit(1 if gagal else 0)
