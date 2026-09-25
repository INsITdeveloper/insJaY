from .lexer import GalatInsJay, lex_ungkapan, pisah_argumen

PERBANDINGAN = [
    ("tidak sama dengan", "!="),
    ("lebih besar atau sama dengan", ">="),
    ("lebih kecil atau sama dengan", "<="),
    ("sama dengan", "=="),
    ("lebih besar dari", ">"),
    ("lebih kecil dari", "<"),
]


def _pisah_kunci(bagian):
    depth = 0
    in_str = False
    i = 0
    while i < len(bagian):
        c = bagian[i]
        if c == '"':
            in_str = not in_str
        elif not in_str:
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
            elif depth == 0 and c in "=:":
                nilai = bagian[i + 1:]
                if c == ":" and nilai.startswith("="):
                    nilai = nilai[1:]
                return bagian[:i], nilai
        i += 1
    return None, None


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
        if jenis == "keteks":
            self.next()
            return {"t": "KeTeks", "nama": tok[1]}
        if jenis == "peta":
            self.next()
            return {"t": "AnggotaPeta", "nama": tok[1], "kunci": tok[2]}
        if jenis == "deret":
            self.next()
            return {"t": "AnggotaDeret", "nama": tok[1], "indeks": tok[2]}
        if jenis == "jalur":
            self.next()
            return {"t": "AnggotaJalur", "nama": tok[1], "jalur": tok[2]}
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
    for frasa, nodeT in (("cocok dengan pola", "CocokPola"), ("memiliki", "Memiliki"), ("memuat", "Memuat")):
        idx_khusus = find_top_level(s, frasa)
        if idx_khusus != -1:
            return {
                "t": nodeT,
                "kiri": parse_ungkapan(s[:idx_khusus], berkas),
                "kanan": parse_ungkapan(s[idx_khusus + len(frasa):], berkas),
            }
    idx_adalah = find_top_level(s, "adalah")
    if idx_adalah != -1:
        return {
            "t": "Adalah",
            "kiri": parse_ungkapan(s[:idx_adalah], berkas),
            "jenis": s[idx_adalah + len("adalah"):].strip().lower(),
        }
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
        if jenis in ("LET", "LET_ALIAS"):
            return dict(dasar, t="Let", nama=g[0], nilai=parse_ungkapan(g[1], tok["berkas"]))
        if jenis in ("SET", "SET_ALIAS"):
            return dict(dasar, t="Set", nama=g[0], nilai=parse_ungkapan(g[1], tok["berkas"]))
        if jenis == "ASSIGN":
            return dict(dasar, t="Assign", nama=g[0], nilai=parse_ungkapan(g[1], tok["berkas"]))
        if jenis == "BERKATA_CALL":
            isi = g[0].strip()
            if not isi:
                return dict(dasar, t="Berkata", nilai={"t": "Teks", "nilai": ""})
            return dict(dasar, t="Berkata", nilai=parse_ungkapan(isi, tok["berkas"]))
        if jenis == "BERKATA_ALIAS":
            return dict(dasar, t="Berkata", nilai=parse_ungkapan(g[0], tok["berkas"]))
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
            params, bawaan = [], []
            for p in (pisah_argumen(g[1]) if g[1] else []):
                p = p.strip()
                if not p:
                    continue
                if "=" in p:
                    nm, nilai = p.split("=", 1)
                    params.append(nm.strip())
                    bawaan.append(parse_ungkapan(nilai.strip(), tok["berkas"]))
                else:
                    params.append(p)
                    bawaan.append(None)
            tubuh = self.blok(("SELESAI",))
            if not self.peek() or self.peek()["jenis"] != "SELESAI":
                self.galat("Kebiasaan '%s' belum ditutup dengan 'selesai'." % nama, tok)
            self.i += 1
            return dict(dasar, t="Kebiasaan", nama=nama, params=params, bawaan=bawaan, tubuh=tubuh)
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
        if jenis == "DERET":
            return dict(dasar, t="Deret", nama=g[0],
                        isi=[parse_ungkapan(x, tok["berkas"]) for x in pisah_argumen(g[1])])
        if jenis == "DERET_KOSONG":
            return dict(dasar, t="Deret", nama=g[0], isi=[])
        if jenis == "PETA":
            pasangan = []
            for bagian in pisah_argumen(g[1]):
                kunci, nilai = _pisah_kunci(bagian)
                if kunci is None:
                    self.galat("Isi peta harus berbentuk 'kunci = nilai' atau 'kunci: nilai'.", tok)
                pasangan.append((kunci.strip().strip('"'), parse_ungkapan(nilai.strip(), tok["berkas"])))
            return dict(dasar, t="Peta", nama=g[0], pasangan=pasangan)
        if jenis == "PETA_KOSONG":
            return dict(dasar, t="Peta", nama=g[0], pasangan=[])
        if jenis == "HIMPUNAN":
            return dict(dasar, t="Himpunan", nama=g[0])
        if jenis == "DERET_TAMBAH":
            return dict(dasar, t="DeretTambah", nama=g[1], nilai=parse_ungkapan(g[0], tok["berkas"]))
        if jenis == "HIMPUNAN_TAMBAH":
            return dict(dasar, t="HimpunanTambah", nama=g[1], nilai=parse_ungkapan(g[0], tok["berkas"]))
        if jenis == "PETA_UBAH":
            return dict(dasar, t="PetaUbah", nama=g[1], kunci=g[0], nilai=parse_ungkapan(g[2], tok["berkas"]))
        if jenis == "DERET_UBAH":
            return dict(dasar, t="DeretUbah", nama=g[1], indeks=int(g[0]), nilai=parse_ungkapan(g[2], tok["berkas"]))
        if jenis == "JSON_URAI":
            return dict(dasar, t="JsonUrai", sumber=g[0], sasaran=g[1])
        if jenis == "JSON_SUSUN":
            return dict(dasar, t="JsonSusun", sumber=g[0], sasaran=g[1])
        if jenis == "HTTP_GET":
            return dict(dasar, t="HttpGet", url=parse_ungkapan(g[0], tok["berkas"]), sasaran=g[1])
        if jenis == "HTTP_POST":
            return dict(dasar, t="HttpPost", url=parse_ungkapan(g[0], tok["berkas"]), isi=g[1], sasaran=g[2])
        if jenis == "HTTP_KEPALA":
            return dict(dasar, t="HttpKepala", nama=g[0])
        if jenis == "HTTP_JEDA":
            return dict(dasar, t="HttpJeda", detik=int(g[0]))
        if jenis == "SELAMA_DERET":
            tubuh = self.blok(("SELESAI",))
            if not self.peek() or self.peek()["jenis"] != "SELESAI":
                self.galat("Blok 'untuk setiap' belum ditutup dengan 'selesai'.", tok)
            self.i += 1
            return dict(dasar, t="SelamaDeret", item=g[0], deret=g[1], tubuh=tubuh)
        if jenis == "SELAMA_RENTANG":
            tubuh = self.blok(("SELESAI",))
            if not self.peek() or self.peek()["jenis"] != "SELESAI":
                self.galat("Blok 'untuk setiap' belum ditutup dengan 'selesai'.", tok)
            self.i += 1
            return dict(dasar, t="SelamaRentang", item=g[0],
                        dari=parse_ungkapan(g[1], tok["berkas"]),
                        sampai=parse_ungkapan(g[2], tok["berkas"]), tubuh=tubuh)
        if jenis == "COBA":
            tubuh = self.blok(("JIKA_GAGAL", "SELESAI"))
            gagal = []
            if self.peek() and self.peek()["jenis"] == "JIKA_GAGAL":
                self.i += 1
                gagal = self.blok(("SELESAI",))
            if not self.peek() or self.peek()["jenis"] != "SELESAI":
                self.galat("Blok 'coba' belum ditutup dengan 'selesai'.", tok)
            self.i += 1
            return dict(dasar, t="Coba", tubuh=tubuh, gagal=gagal)
        if jenis == "ARGUMEN":
            return dict(dasar, t="Argumen", nama=g[0])
        if jenis == "KELUAR":
            return dict(dasar, t="Keluar", kode=int(g[0]) if g[0] else 0)
        if jenis == "TUNGGU":
            return dict(dasar, t="Tunggu", milidetik=int(g[0]))
        if jenis == "AMBIL":
            return dict(dasar, t="Ambil", modul=g[0], nama=g[1])
        if jenis == "SERAHKAN":
            return dict(dasar, t="Serahkan", nama=g[0])
        if jenis in ("SELESAI", "KALAU_TIDAK"):
            self.galat("'%s' ini tidak punya pasangan." % ("selesai" if jenis == "SELESAI" else "kalau tidak"), tok)
        self.galat("Kalimat jenis '%s' belum bisa diurai." % jenis, tok)
