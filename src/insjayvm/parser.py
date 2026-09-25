from .lexer import GalatInsJay, lex_ungkapan, pisah_argumen

PERBANDINGAN = [
    ("tidak sama dengan", "!="),
    ("lebih besar atau sama dengan", ">="),
    ("lebih kecil atau sama dengan", "<="),
    ("sama dengan", "=="),
    ("lebih besar dari", ">"),
    ("lebih kecil dari", "<"),
]


def find_top_level(s, phrase):
    depth = 0
    in_str = False
    i = 0
    while i < len(s):
        c = s[i]
        if c == '"':
            in_str = not in_str
        elif not in_str:
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
            elif depth == 0 and s.startswith(phrase, i):
                return i
        i += 1
    return -1


class ParserUngkapan:
    def __init__(self, toks, berkas):
        self.t = toks
        self.p = 0
        self.berkas = berkas

    def peek(self):
        return self.t[self.p] if self.p < len(self.t) else None

    def next(self):
        tok = self.t[self.p]
        self.p += 1
        return tok

    def galat(self, p):
        raise GalatInsJay(p, None, self.berkas)

    def parse(self):
        n = self.atau()
        if self.peek() is not None:
            self.galat("Ungkapan belum selesai dibaca (ada sisa kata).")
        return n

    def atau(self):
        k = self.dan()
        while self.peek() == ("ident", "atau"):
            self.next()
            k = {"t": "Logika", "op": "atau", "kiri": k, "kanan": self.dan()}
        return k

    def dan(self):
        k = self.tidak()
        while self.peek() == ("ident", "dan"):
            self.next()
            k = {"t": "Logika", "op": "dan", "kiri": k, "kanan": self.tidak()}
        return k

    def tidak(self):
        if self.peek() == ("ident", "tidak"):
            self.next()
            return {"t": "Tidak", "anak": self.tidak()}
        return self.tambah()

    def tambah(self):
        k = self.kali()
        while self.peek() in (("op", "+"), ("op", "-")):
            op = self.next()[1]
            k = {"t": "Biner", "op": op, "kiri": k, "kanan": self.kali()}
        return k

    def kali(self):
        k = self.atom()
        while self.peek() in (("op", "*"), ("op", "/"), ("op", "%")):
            op = self.next()[1]
            k = {"t": "Biner", "op": op, "kiri": k, "kanan": self.atom()}
        return k

    def atom(self):
        tok = self.peek()
        if tok is None:
            self.galat("Ada ungkapan yang kosong.")
        jenis = tok[0]
        if jenis == "angka":
            self.next()
            return {"t": "Angka", "nilai": tok[1]}
        if jenis == "teks":
            self.next()
            return {"t": "Teks", "nilai": tok[1]}
        if jenis == "var":
            self.next()
            return {"t": "Wadah", "nama": tok[1]}
        if jenis == "panjang":
            self.next()
            return {"t": "Panjang", "nama": tok[1]}
        if jenis == "keangka":
            self.next()
            return {"t": "KeAngka", "nama": tok[1]}
        if jenis == "hurufkecil":
            self.next()
            return {"t": "HurufKecil", "nama": tok[1]}
        if jenis == "hurufbesar":
            self.next()
            return {"t": "HurufBesar", "nama": tok[1]}
        if jenis == "lp":
            self.next()
            d = self.atau()
            if self.peek() != ("rp",):
                self.galat("Kurung '(' tidak pernah ditutup.")
            self.next()
            return d
        if jenis == "panggil":
            self.next()
            nama = tok[1]
            args = []
            if self.peek() == ("ident", "dengan"):
                self.next()
                args.append(self.atau())
                while self.peek() == ("comma",):
                    self.next()
                    args.append(self.atau())
            return {"t": "Panggilan", "nama": nama, "args": args}
        if jenis == "ident":
            self.next()
            if tok[1] == "benar":
                return {"t": "Benar"}
            if tok[1] == "salah":
                return {"t": "Salah"}
            self.galat("Kata '%s' tidak dikenal. Untuk mengambil isi wadah, tulis 'wadah %s'." % (tok[1], tok[1]))
        self.galat("Ungkapan tidak terduga.")


def parse_ungkapan(s, berkas=None):
    return ParserUngkapan(lex_ungkapan(s, berkas), berkas).parse()


def parse_kondisi(teks, berkas=None):
    s = teks.strip()
    if s[:6].lower() == "tidak ":
        return {"t": "Tidak", "anak": parse_kondisi(s[6:], berkas)}
    idx = find_top_level(s, "mengandung")
    if idx != -1:
        return {
            "t": "Mengandung",
            "kiri": parse_ungkapan(s[:idx], berkas),
            "kanan": parse_ungkapan(s[idx + len("mengandung"):], berkas),
        }
    for frasa, op in PERBANDINGAN:
        idx = find_top_level(s, frasa)
        if idx != -1:
            return {
                "t": "Kondisi", "op": op, "frasa": frasa,
                "kiri": parse_ungkapan(s[:idx], berkas),
                "kanan": parse_ungkapan(s[idx + len(frasa):], berkas),
            }
    low = s.lower()
    if low == "benar":
        return {"t": "Benar"}
    if low == "salah":
        return {"t": "Salah"}
    return {"t": "Kebenaran", "expr": parse_ungkapan(s, berkas)}


class Parser:
    def __init__(self, tokens, berkas=None):
        self.t = tokens
        self.i = 0
        self.berkas = berkas

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else None

    def galat(self, p, tok=None):
        baris = tok["baris"] if tok else None
        potongan = tok["teks"] if tok else None
        bk = tok["berkas"] if tok else self.berkas
        raise GalatInsJay(p, baris, bk, potongan)

    def program(self):
        isi = []
        while self.i < len(self.t):
            isi.append(self.kalimat())
        return {"t": "Program", "isi": isi}

    def blok(self, penutup):
        isi = []
        while self.i < len(self.t) and self.t[self.i]["jenis"] not in penutup:
            isi.append(self.kalimat())
        return isi

    def kalimat(self):
        tok = self.t[self.i]
        self.i += 1
        jenis = tok["jenis"]
        g = tok.get("m") or []
        dasar = {"baris": tok["baris"], "berkas": tok["berkas"]}

        if jenis == "BAB":
            return dict(dasar, t="Bab", judul=tok["judul"])
        if jenis == "LET":
            return dict(dasar, t="Let", nama=g[0], nilai=parse_ungkapan(g[1], tok["berkas"]))
        if jenis == "SET":
            return dict(dasar, t="Set", nama=g[0], nilai=parse_ungkapan(g[1], tok["berkas"]))
        if jenis == "ADD":
            return dict(dasar, t="Tambah", nama=g[1], nilai=parse_ungkapan(g[0], tok["berkas"]))
        if jenis == "SUB":
            return dict(dasar, t="Kurang", nama=g[0], nilai=parse_ungkapan(g[1], tok["berkas"]))
        if jenis == "BERKATA":
            return dict(dasar, t="Berkata", nilai=parse_ungkapan(g[0], tok["berkas"]))
        if jenis == "TANYA":
            return dict(dasar, t="Tanya", nama=g[1], pertanyaan=parse_ungkapan(g[0], tok["berkas"]))
        if jenis == "JIKA":
            kondisi = parse_kondisi(g[0], tok["berkas"])
            tubuh = self.blok(("KALAU_TIDAK", "SELESAI"))
            lain = []
            if self.peek() and self.peek()["jenis"] == "KALAU_TIDAK":
                self.i += 1
                lain = self.blok(("SELESAI",))
            if not self.peek() or self.peek()["jenis"] != "SELESAI":
                self.galat("Blok 'jika' belum ditutup dengan 'selesai'.", tok)
            self.i += 1
            return dict(dasar, t="Jika", kondisi=kondisi, tubuh=tubuh, lain=lain)
        if jenis == "SELAMA":
            kondisi = parse_kondisi(g[0], tok["berkas"])
            tubuh = self.blok(("SELESAI",))
            if not self.peek() or self.peek()["jenis"] != "SELESAI":
                self.galat("Blok 'selama' belum ditutup dengan 'selesai'.", tok)
            self.i += 1
            return dict(dasar, t="Selama", kondisi=kondisi, tubuh=tubuh)
        if jenis == "KEBIASAAN":
            nama = g[0]
            params = [p.strip() for p in pisah_argumen(g[1]) if p.strip()] if g[1] else []
            tubuh = self.blok(("SELESAI",))
            if not self.peek() or self.peek()["jenis"] != "SELESAI":
                self.galat("Kebiasaan '%s' belum ditutup dengan 'selesai'." % nama, tok)
            self.i += 1
            return dict(dasar, t="Kebiasaan", nama=nama, params=params, tubuh=tubuh)
        if jenis == "PANGGIL":
            args = [parse_ungkapan(a, tok["berkas"]) for a in pisah_argumen(g[1])] if g[1] else []
            return dict(dasar, t="Panggil", nama=g[0], args=args)
        if jenis == "KEMBALI":
            return dict(dasar, t="Kembali", nilai=parse_ungkapan(g[0], tok["berkas"]))
        if jenis == "SAMBUNG":
            return dict(dasar, t="Sambung", berkas=g[0])
        if jenis == "HALAMAN":
            return dict(dasar, t="Halaman", nama=g[0], judul=parse_ungkapan(g[1], tok["berkas"]))
        if jenis == "JUDUL":
            return dict(dasar, t="Judul", target=g[1], nilai=parse_ungkapan(g[0], tok["berkas"]))
        if jenis == "PARAGRAF":
            return dict(dasar, t="Paragraf", target=g[1], nilai=parse_ungkapan(g[0], tok["berkas"]))
        if jenis == "ISIAN":
            return dict(dasar, t="Isian", nama=g[0], target=g[1])
        if jenis == "TOMBOL":
            return dict(dasar, t="Tombol", target=g[2], label=parse_ungkapan(g[0], tok["berkas"]), fungsi=g[1])
        if jenis == "JAWABAN":
            return dict(dasar, t="Jawaban", target=g[1], nilai=parse_ungkapan(g[0], tok["berkas"]))
        if jenis == "GANTI_JAWABAN":
            return dict(dasar, t="GantiJawaban", target=g[0], nilai=parse_ungkapan(g[1], tok["berkas"]))
        if jenis == "BACA_ISIAN":
            return dict(dasar, t="BacaIsian", nama=g[0], sasaran=g[1])
        if jenis == "AMBIL":
            return dict(dasar, t="Ambil", modul=g[0], nama=g[1])
        if jenis == "SERAHKAN":
            return dict(dasar, t="Serahkan", nama=g[0])
        if jenis in ("SELESAI", "KALAU_TIDAK"):
            self.galat("'%s' ini tidak punya pasangan." % ("selesai" if jenis == "SELESAI" else "kalau tidak"), tok)
        self.galat("Kalimat jenis '%s' belum bisa diurai." % jenis, tok)
