import re


class GalatInsJay(Exception):

    def __init__(self, pesan, baris=None, berkas=None, potongan=None):
        super().__init__(pesan)
        self.pesan = pesan
        self.baris = baris
        self.berkas = berkas
        self.potongan = potongan

    def format(self):
        lokasi = self.berkas or ""
        if lokasi and self.baris:
            lokasi += ":%d" % self.baris
        ekor = (" (%s)" % lokasi) if lokasi else ""
        petunjuk = ("\n        Kalimat: \"%s\"" % self.potongan) if self.potongan else ""
        return "%s%s%s" % (self.pesan, ekor, petunjuk)


POLA = [
    ("LET", re.compile(r"^aku\s+menyiapkan\s+wadah\s+bernama\s+(\w+)\s+yang\s+berisi\s+(.+)$", re.I)),
    ("SET", re.compile(r"^aku\s+mengganti\s+isi\s+wadah\s+(\w+)\s+menjadi\s+(.+)$", re.I)),
    ("ADD", re.compile(r"^aku\s+menambahkan\s+(.+?)\s+ke\s+dalam\s+wadah\s+(\w+)$", re.I)),
    ("SUB", re.compile(r"^aku\s+mengurangi\s+wadah\s+(\w+)\s+dengan\s+(.+)$", re.I)),
    ("BERKATA", re.compile(r"^aku\s+berkata:\s*(.+)$", re.I)),
    ("JIKA", re.compile(r"^jika\s+(.+?)\s+maka$", re.I)),
    ("KALAU_TIDAK", re.compile(r"^kalau\s+tidak$", re.I)),
    ("SELAMA", re.compile(r"^selama\s+(.+?),\s*ulangi$", re.I)),
    ("SELESAI", re.compile(r"^selesai$", re.I)),
    ("KEBIASAAN", re.compile(r"^aku\s+membuat\s+kebiasaan\s+bernama\s+(\w+)(?:\s+yang\s+menerima\s+(.+))?$", re.I)),
    ("PANGGIL", re.compile(r"^aku\s+memanggil\s+kebiasaan\s+(\w+)(?:\s+dengan\s+(.+))?$", re.I)),
    ("KEMBALI", re.compile(r"^aku\s+mengembalikan\s+(.+)$", re.I)),
    ("SAMBUNG", re.compile(r'^aku\s+menyambung\s+cerita\s+dari\s+"(.+)"$', re.I)),
    ("TANYA", re.compile(r"^aku\s+bertanya:\s*(.+?)\s+ke\s+dalam\s+wadah\s+(\w+)$", re.I)),
    ("HALAMAN", re.compile(r"^aku\s+menyiapkan\s+halaman\s+bernama\s+(\w+)\s+berjudul\s+(.+)$", re.I)),
    ("JUDUL", re.compile(r"^aku\s+menaruh\s+judul\s+(.+?)\s+ke\s+dalam\s+halaman\s+(\w+)$", re.I)),
    ("PARAGRAF", re.compile(r"^aku\s+menaruh\s+paragraf\s+(.+?)\s+ke\s+dalam\s+halaman\s+(\w+)$", re.I)),
    ("ISIAN", re.compile(r"^aku\s+menaruh\s+kotak\s+isian\s+bernama\s+(\w+)\s+ke\s+dalam\s+halaman\s+(\w+)$", re.I)),
    ("TOMBOL", re.compile(r"^aku\s+menaruh\s+tombol\s+(.+?)\s+yang\s+memanggil\s+kebiasaan\s+(\w+)\s+ke\s+dalam\s+halaman\s+(\w+)$", re.I)),
    ("JAWABAN", re.compile(r"^aku\s+menaruh\s+jawaban\s+(.+?)\s+ke\s+dalam\s+halaman\s+(\w+)$", re.I)),
    ("GANTI_JAWABAN", re.compile(r"^aku\s+mengubah\s+jawaban\s+di\s+halaman\s+(\w+)\s+menjadi\s+(.+)$", re.I)),
    ("BACA_ISIAN", re.compile(r"^aku\s+membaca\s+kotak\s+isian\s+(\w+)\s+ke\s+dalam\s+wadah\s+(\w+)$", re.I)),
    ("DERET", re.compile(r"^aku\s+menyiapkan\s+deret\s+bernama\s+(\w+)\s+yang\s+berisi\s+(.+)$", re.I)),
    ("DERET_KOSONG", re.compile(r"^aku\s+menyiapkan\s+deret\s+bernama\s+(\w+)$", re.I)),
    ("PETA", re.compile(r"^aku\s+menyiapkan\s+peta\s+bernama\s+(\w+)\s+yang\s+berisi\s+(.+)$", re.I)),
    ("PETA_KOSONG", re.compile(r"^aku\s+menyiapkan\s+peta\s+bernama\s+(\w+)$", re.I)),
    ("HIMPUNAN", re.compile(r"^aku\s+menyiapkan\s+himpunan\s+bernama\s+(\w+)$", re.I)),
    ("DERET_TAMBAH", re.compile(r"^aku\s+menambahkan\s+(.+?)\s+ke\s+dalam\s+deret\s+(\w+)$", re.I)),
    ("HIMPUNAN_TAMBAH", re.compile(r"^aku\s+menambahkan\s+(.+?)\s+ke\s+dalam\s+himpunan\s+(\w+)$", re.I)),
    ("PETA_UBAH", re.compile(r'^aku\s+mengubah\s+anggota\s+"(.+)"\s+dari\s+peta\s+(\w+)\s+menjadi\s+(.+)$', re.I)),
    ("DERET_UBAH", re.compile(r"^aku\s+mengubah\s+benda\s+ke-(\d+)\s+dari\s+deret\s+(\w+)\s+menjadi\s+(.+)$", re.I)),
    ("JSON_URAI", re.compile(r"^aku\s+mengurai\s+json\s+dari\s+wadah\s+(\w+)\s+ke\s+dalam\s+wadah\s+(\w+)$", re.I)),
    ("JSON_SUSUN", re.compile(r"^aku\s+menyusun\s+json\s+dari\s+wadah\s+(\w+)\s+ke\s+dalam\s+wadah\s+(\w+)$", re.I)),
    ("HTTP_GET", re.compile(r'^aku\s+meminta\s+get\s+dari\s+("[^"]*"|wadah\s+\w+)\s+ke\s+dalam\s+wadah\s+(\w+)$', re.I)),
    ("HTTP_POST", re.compile(r'^aku\s+meminta\s+post\s+ke\s+("[^"]*"|wadah\s+\w+)\s+dengan\s+isi\s+wadah\s+(\w+)\s+ke\s+dalam\s+wadah\s+(\w+)$', re.I)),
    ("HTTP_KEPALA", re.compile(r"^aku\s+mengatur\s+kepala\s+permintaan\s+dari\s+wadah\s+(\w+)$", re.I)),
    ("HTTP_JEDA", re.compile(r"^aku\s+mengatur\s+jeda\s+permintaan\s+menjadi\s+(\d+)\s+detik$", re.I)),
    ("SELAMA_DERET", re.compile(r"^untuk\s+setiap\s+(\w+)\s+dalam\s+deret\s+(\w+),\s*ulangi$", re.I)),
    ("SELAMA_RENTANG", re.compile(r"^untuk\s+setiap\s+(\w+)\s+dari\s+(.+?)\s+sampai\s+(.+?),\s*ulangi$", re.I)),
    ("COBA", re.compile(r"^coba$", re.I)),
    ("JIKA_GAGAL", re.compile(r"^jika\s+gagal$", re.I)),
    ("ARGUMEN", re.compile(r"^aku\s+membaca\s+argumen\s+ke\s+dalam\s+wadah\s+(\w+)$", re.I)),
    ("KELUAR", re.compile(r"^aku\s+mengakhiri(?:\s+dengan\s+kode\s+(\d+))?$", re.I)),
    ("TUNGGU", re.compile(r"^aku\s+menunggu\s+(\d+)\s+milidetik$", re.I)),
    ("AMBIL", re.compile(r'^aku\s+mengambil\s+dari\s+"(.+)"\s+ke\s+dalam\s+wadah\s+(\w+)$', re.I)),
    ("SERAHKAN", re.compile(r"^aku\s+menyerahkan\s+kebiasaan\s+(\w+)\s+kepada\s+dunia$", re.I)),
]

JENIS_WEB = frozenset([
    "HALAMAN", "JUDUL", "PARAGRAF", "ISIAN", "TOMBOL",
    "JAWABAN", "GANTI_JAWABAN", "BACA_ISIAN",
])


def lex(teks, berkas=None):
    token = []
    for i, mentah in enumerate(teks.split("\n"), 1):
        t = mentah.strip()
        if not t or t.startswith("//"):
            continue
        if t.startswith("#"):
            token.append({"jenis": "BAB", "baris": i, "berkas": berkas,
                          "teks": t, "judul": re.sub(r"^#\s*", "", t)})
            continue
        if t.endswith("."):
            t = t[:-1].strip()
        for jenis, rx in POLA:
            m = rx.match(t)
            if m:
                token.append({"jenis": jenis, "baris": i, "berkas": berkas,
                              "teks": t, "m": list(m.groups())})
                break
        else:
            raise GalatInsJay(
                "Kalimat ini tidak mengikuti alur cerita insJaY sehingga tidak bisa dipahami.",
                i, berkas, t)
    return token


FRASA_PANJANG = "panjang dari wadah"
FRASA_KEWADAH = "angka dari wadah"
FRASA_HURUFKECIL = "huruf kecil dari wadah"
FRASA_HURUFBESAR = "huruf besar dari wadah"
FRASA_VAR = "wadah"
FRASA_PANGGIL = "hasil dari kebiasaan"
FRASA_JALUR = "anggota dalam"
FRASA_PETA = "anggota"
FRASA_DERET = "benda ke-"
FRASA_KETEKS = "teks dari wadah"


def lex_ungkapan(s, berkas=None):
    toks = []
    i = 0
    n = len(s)

    def galat(p):
        raise GalatInsJay(p, None, berkas)

    while i < n:
        c = s[i]
        if c.isspace():
            i += 1
            continue
        if c == '"':
            buf = []
            j = i + 1
            while j < len(s) and s[j] != '"':
                if s[j] == "\\" and j + 1 < len(s):
                    nx = s[j + 1]
                    buf.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(nx, nx))
                    j += 2
                else:
                    buf.append(s[j])
                    j += 1
            if j >= len(s):
                galat("Tanda kutip pembuka tidak pernah ditutup.")
            toks.append(("teks", "".join(buf)))
            i = j + 1
            continue
        cocok = False
        if s.startswith(FRASA_JALUR, i):
            i += len(FRASA_JALUR)
            m = re.match(r'\s*"([^"]*)"\s+dari\s+wadah\s+(\w+)', s[i:])
            if not m:
                galat("'anggota dalam \"jalur\" dari wadah x' tidak lengkap.")
            toks.append(("jalur", m.group(2), m.group(1)))
            i += m.end()
            continue
        if s.startswith(FRASA_PETA, i):
            i += len(FRASA_PETA)
            m = re.match(r'\s*"([^"]*)"\s+dari\s+wadah\s+(\w+)', s[i:])
            if not m:
                galat("'anggota \"kunci\" dari wadah x' tidak lengkap.")
            toks.append(("peta", m.group(2), m.group(1)))
            i += m.end()
            continue
        if s.startswith(FRASA_DERET, i):
            i += len(FRASA_DERET)
            m = re.match(r"\s*(\d+)\s+dari\s+wadah\s+(\w+)", s[i:])
            if not m:
                galat("'benda ke-N dari wadah x' tidak lengkap.")
            toks.append(("deret", m.group(2), int(m.group(1))))
            i += m.end()
            continue
        if s.startswith(FRASA_KETEKS, i):
            i += len(FRASA_KETEKS)
            m = re.match(r"\s*(\w+)", s[i:])
            if not m:
                galat("'teks dari wadah' harus diikuti nama wadah.")
            toks.append(("keteks", m.group(1)))
            i += m.end()
            continue
        for frasa, jenis in (
            (FRASA_PANJANG, "panjang"),
            (FRASA_KEWADAH, "keangka"),
            (FRASA_HURUFKECIL, "hurufkecil"),
            (FRASA_HURUFBESAR, "hurufbesar"),
        ):
            if s.startswith(frasa, i):
                i += len(frasa)
                m = re.match(r"\s*(\w+)", s[i:])
                if not m:
                    galat("'%s' harus diikuti nama wadah." % frasa)
                toks.append((jenis, m.group(1)))
                i += m.end()
                cocok = True
                break
        if cocok:
            continue
        if s.startswith(FRASA_VAR, i):
            i += len(FRASA_VAR)
            m = re.match(r"\s*(\w+)", s[i:])
            if not m:
                galat("'wadah' harus diikuti nama wadah.")
            toks.append(("var", m.group(1)))
            i += m.end()
            continue
        if s.startswith(FRASA_PANGGIL, i):
            i += len(FRASA_PANGGIL)
            m = re.match(r"\s*(\w+)", s[i:])
            if not m:
                galat("'hasil dari kebiasaan' harus diikuti nama kebiasaan.")
            toks.append(("panggil", m.group(1)))
            i += m.end()
            continue
        if c in "+-*/%":
            toks.append(("op", c))
            i += 1
            continue
        if c == "(":
            toks.append(("lp",))
            i += 1
            continue
        if c == ")":
            toks.append(("rp",))
            i += 1
            continue
        if c == ",":
            toks.append(("comma",))
            i += 1
            continue
        m = re.match(r"\d+\.\d+|\d+", s[i:])
        if m:
            v = m.group(0)
            toks.append(("angka", float(v) if "." in v else int(v)))
            i += m.end()
            continue
        m = re.match(r"[A-Za-z_]\w*", s[i:])
        if m:
            toks.append(("ident", m.group(0)))
            i += m.end()
            continue
        galat("Karakter '%s' tidak dikenal dalam ungkapan." % c)
    return toks


def pisah_argumen(teks):
    hasil = []
    depth = 0
    in_str = False
    buf = ""
    for c in teks:
        if c == '"':
            in_str = not in_str
        if not in_str:
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
            elif c == "," and depth == 0:
                hasil.append(buf.strip())
                buf = ""
                continue
        buf += c
    if buf.strip():
        hasil.append(buf.strip())
    return hasil
