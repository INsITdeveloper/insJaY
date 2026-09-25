import json
import math
import random
import re
import time
import urllib.error
import urllib.request
from datetime import datetime

from .lexer import GalatInsJay

MISSING = object()


class KeluarSignal(Exception):
    def __init__(self, kode=0):
        super().__init__("keluar")
        self.kode = kode


def ke_teks(v):
    if isinstance(v, bool):
        return "benar" if v else "salah"
    if v is None or v is MISSING:
        return ""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    if isinstance(v, (list, dict, set)):
        return json.dumps(susun_json(v), ensure_ascii=False)
    return str(v)


def ke_bool(v):
    if isinstance(v, str):
        return v.strip() != "" and v.lower() not in ("salah", "false", "0")
    return bool(v)


def susun_json(v):
    if isinstance(v, set):
        return sorted(v, key=lambda x: str(x))
    if isinstance(v, dict):
        return {k: susun_json(x) for k, x in v.items()}
    if isinstance(v, list):
        return [susun_json(x) for x in v]
    if v is MISSING:
        return None
    return v


class Mesin:
    def __init__(self, bytecode, masukan=None, keluaran=print, argv=None):
        self.konstanta = bytecode["konstanta"]
        self.fungsi = bytecode.get("fungsi", {})
        self.kode = bytecode["kode"]
        self.masukan = masukan or (lambda _prompt: input())
        self.keluaran = keluaran
        self.argv = list(argv or [])
        self.global_ = {}
        self.nilai = []
        self.kepala = {}
        self.jeda = 20
        self.bawaan = self._pustaka()

    def _pustaka(self):
        def http(url, isi=None, metode="GET"):
            data = None
            kepala = dict(self.kepala)
            if isi is not None:
                if isinstance(isi, (dict, list)):
                    data = json.dumps(susun_json(isi), ensure_ascii=False).encode("utf-8")
                    kepala.setdefault("Content-Type", "application/json")
                else:
                    data = ke_teks(isi).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers=kepala, method=metode)
            try:
                with urllib.request.urlopen(req, timeout=self.jeda) as r:
                    teks = r.read().decode("utf-8", "replace")
                    return {"status": r.status, "ok": 200 <= r.status < 300, "teks": teks, "galat": ""}
            except urllib.error.HTTPError as e:
                teks = e.read().decode("utf-8", "replace") if e.fp else ""
                return {"status": e.code, "ok": False, "teks": teks, "galat": str(e)}
            except Exception as e:
                raise GalatInsJay("Permintaan HTTP gagal: %s" % e)

        return {
            "akar": lambda a: math.sqrt(a[0]),
            "pangkat": lambda a: a[0] ** a[1],
            "bulat": lambda a: int(round(a[0])),
            "lantai": lambda a: math.floor(a[0]),
            "acak": lambda a: random.random(),
            "waktu_sekarang": lambda a: datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "pangkas": lambda a: ke_teks(a[0]).strip(),
            "ganti": lambda a: ke_teks(a[0]).replace(ke_teks(a[1]), ke_teks(a[2])),
            "pisah": lambda a: ke_teks(a[0]).split(ke_teks(a[1])),
            "gabung": lambda a: ke_teks(a[1]).join(ke_teks(x) for x in a[0]),
            "cocok_pola": lambda a: re.search(ke_teks(a[1]), ke_teks(a[0])) is not None,
            "ganti_pola": lambda a: re.sub(ke_teks(a[1]), ke_teks(a[2]), ke_teks(a[0])),
            "cari_pola": lambda a: re.findall(ke_teks(a[1]), ke_teks(a[0])),
            "gabung_peta": lambda a: dict(a[0], **a[1]),
            "anggota": lambda a: _ambil(a[0], a[1]),
            "punya": lambda a: _punya(a[0], a[1]),
            "jenis": lambda a: _jenis(a[0]),
            "tidur": lambda a: time.sleep(ke_angka(a[0]) / 1000.0),
            "http_get": lambda a: http(ke_teks(a[0])),
            "http_post": lambda a: http(ke_teks(a[0]), a[1] if len(a) > 1 else None, "POST"),
        }

    def _cari(self, frame, nama):
        f = frame
        while f is not None:
            if nama in f["lokal"]:
                return f["lokal"][nama]
            f = f.get("induk")
        raise GalatInsJay("Wadah '%s' belum pernah disiapkan." % nama)

    def _tempat(self, frame, nama):
        f = frame
        while f is not None:
            if nama in f["lokal"]:
                return f["lokal"]
            f = f.get("induk")
        return frame["lokal"]

    def _banding(self, a, b, op):
        if isinstance(a, bool) or isinstance(b, bool):
            x, y = ke_teks(a), ke_teks(b)
        elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
            x, y = a, b
        elif isinstance(a, str) and isinstance(b, str):
            x, y = a, b
        else:
            x, y = ke_teks(a), ke_teks(b)
        if op == "==":
            return x == y
        if op == "!=":
            return x != y
        if op == ">":
            return x > y
        if op == "<":
            return x < y
        if op == ">=":
            return x >= y
        if op == "<=":
            return x <= y
        raise GalatInsJay("Operator banding '%s' tidak dikenal." % op)

    def _hitung(self, op, a, b=None):
        if op == "+":
            if isinstance(a, str) or isinstance(b, str):
                return ke_teks(a) + ke_teks(b)
            if isinstance(a, list) and isinstance(b, list):
                return a + b
            return a + b
        if op == "-":
            return a - b
        if op == "*":
            return a * b
        if op == "/":
            if b == 0:
                raise GalatInsJay("Tidak bisa membagi dengan nol.")
            return a / b
        if op == "%":
            return a % b
        if op == "dan":
            return ke_bool(a) and ke_bool(b)
        if op == "atau":
            return ke_bool(a) or ke_bool(b)
        if op == "tidak":
            return not ke_bool(a)
        if op == "kebenaran":
            return ke_bool(a)
        if op == "panjang":
            if a is None or a is MISSING:
                return 0
            try:
                return len(a)
            except TypeError:
                return 0
        if op == "keangka":
            return ke_angka(a)
        if op == "keteks":
            return ke_teks(a)
        if op == "hurufkecil":
            return ke_teks(a).lower()
        if op == "hurufbesar":
            return ke_teks(a).upper()
        if op == "mengandung":
            return ke_teks(b) in ke_teks(a)
        if op == "memiliki":
            return _punya(a, b)
        if op == "memuat":
            return _memuat(a, b)
        if op == "adalah":
            return _jenis(a) == ke_teks(b)
        if op == "cocokpola":
            return re.search(ke_teks(b), ke_teks(a)) is not None
        if op == "hilang":
            return a is MISSING
        if op == "anggotapeta":
            return _ambil(a, b)
        if op == "anggotaderet":
            return _ambil(a, ke_angka(b) - 1)
        if op == "aksesderet":
            return _ambil(a, b)
        if op == "jalur":
            return _jalur(a, ke_teks(b))
        if op == "jsonurai":
            try:
                return json.loads(ke_teks(a))
            except Exception as e:
                raise GalatInsJay("Gagal mengurai JSON: %s" % e)
        if op == "jsonsusun":
            return json.dumps(susun_json(a), ensure_ascii=False)
        if op in ("==", "!=", ">", "<", ">=", "<="):
            return self._banding(a, b, op)
        raise GalatInsJay("Operasi '%s' tidak dikenal." % op)

    def jalankan(self):
        utama = {"kode": self.kode, "pc": 0, "lokal": self.global_, "induk": None}
        tumpukan = [utama]
        nilai = self.nilai
        penangkap = []
        while tumpukan:
            f = tumpukan[-1]
            kode = f["kode"]
            if f["pc"] >= len(kode):
                tumpukan.pop()
                if tumpukan:
                    nilai.append(None)
                continue
            ins = kode[f["pc"]]
            f["pc"] += 1
            op = ins["op"]
            try:
                if op == "PUSH":
                    nilai.append(self.konstanta[ins["arg"]])
                elif op == "LOAD":
                    nilai.append(self._cari(f, ins["arg"]))
                elif op == "STORE":
                    f["lokal"][ins["arg"]] = nilai.pop()
                elif op == "SIMPAN":
                    self._tempat(f, ins["arg"])[ins["arg"]] = nilai.pop()
                elif op == "POP":
                    nilai.pop()
                elif op == "BUAT_DERET":
                    jml = ins["arg"]
                    isi = nilai[-jml:] if jml else []
                    if jml:
                        del nilai[-jml:]
                    nilai.append(list(isi))
                elif op == "BUAT_PETA":
                    kunci = ins["arg"]
                    jml = len(kunci)
                    isi = nilai[-jml:] if jml else []
                    if jml:
                        del nilai[-jml:]
                    nilai.append({k: v for k, v in zip(kunci, isi)})
                elif op == "BUAT_HIMPUNAN":
                    nilai.append(set())
                elif op == "DERET_TAMBAH":
                    v = nilai.pop()
                    nilai.pop().append(v)
                elif op == "HIMPUNAN_TAMBAH":
                    v = nilai.pop()
                    nilai.pop().add(_hashable(v))
                elif op == "PETA_SET":
                    v = nilai.pop()
                    k = nilai.pop()
                    nilai.pop()[ke_teks(k)] = v
                elif op == "DERET_SET":
                    v = nilai.pop()
                    i = ke_angka(nilai.pop()) - 1
                    obj = nilai.pop()
                    if 0 <= i < len(obj):
                        obj[i] = v
                elif op == "HTTP_GET":
                    nilai.append(self.bawaan["http_get"]([nilai.pop()]))
                elif op == "HTTP_POST":
                    isi = nilai.pop()
                    nilai.append(self.bawaan["http_post"]([nilai.pop(), isi]))
                elif op == "HTTP_KEPALA":
                    self.kepala = dict(nilai.pop() or {})
                elif op == "ARGUMEN":
                    nilai.append(list(self.argv))
                elif op == "OP":
                    operasi = ins["arg"]
                    if operasi in ("tidak", "kebenaran", "panjang", "keangka", "keteks",
                                   "hurufkecil", "hurufbesar", "hilang", "jsonurai", "jsonsusun"):
                        nilai.append(self._hitung(operasi, nilai.pop()))
                    else:
                        b = nilai.pop()
                        a = nilai.pop()
                        nilai.append(self._hitung(operasi, a, b))
                elif op == "CETAK":
                    self.keluaran(ke_teks(nilai.pop()))
                elif op == "TANYA":
                    prompt = ke_teks(nilai.pop())
                    jawab = self.masukan(prompt)
                    nilai.append("" if jawab is None else str(jawab))
                elif op == "LONCAT":
                    f["pc"] = ins["arg"]
                elif op == "JIKA_SALAH":
                    if not ke_bool(nilai.pop()):
                        f["pc"] = ins["arg"]
                elif op == "COBA_MULAI":
                    penangkap.append({"frame": f, "pc": ins["arg"],
                                      "tinggi": len(nilai), "dalam": len(tumpukan)})
                elif op == "COBA_SELESAI":
                    if penangkap:
                        penangkap.pop()
                elif op == "HTTP_JEDA":
                    self.jeda = ins["arg"]
                elif op == "TUNGGU":
                    time.sleep(ins["arg"] / 1000.0)
                elif op == "KELUAR":
                    raise KeluarSignal(ins["arg"])
                elif op == "CALL":
                    nama, argc = ins["arg"]
                    args = nilai[-argc:] if argc else []
                    if argc:
                        del nilai[-argc:]
                    self._panggil(nama, args, tumpukan, nilai)
                elif op == "KEMBALI":
                    v = nilai.pop()
                    tumpukan.pop()
                    if tumpukan:
                        nilai.append(v)
                elif op == "SELESAI":
                    tumpukan.pop()
                else:
                    raise GalatInsJay("Perintah bytecode '%s' tidak dikenal." % op)
            except KeluarSignal:
                raise
            except Exception as e:
                if not penangkap:
                    if isinstance(e, GalatInsJay):
                        raise
                    raise GalatInsJay(str(e))
                p = penangkap.pop()
                while len(tumpukan) > p["dalam"]:
                    tumpukan.pop()
                del nilai[p["tinggi"]:]
                nilai.append(e.pesan if isinstance(e, GalatInsJay) else str(e))
                p["frame"]["pc"] = p["pc"]

    def _panggil(self, nama, args, tumpukan, nilai):
        if nama in self.bawaan:
            nilai.append(self.bawaan[nama](args))
            return
        if nama not in self.fungsi:
            raise GalatInsJay("Kebiasaan '%s' tidak ada di dalam bytecode." % nama)
        fn = self.fungsi[nama]
        lokal = {}
        for i, p in enumerate(fn["params"]):
            lokal[p] = args[i] if i < len(args) else MISSING
        tumpukan.append({"kode": fn["kode"], "pc": 0, "lokal": lokal, "induk": self.global_})


def ke_angka(v):
    try:
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return v
        t = ke_teks(v).strip()
        return int(t) if t.lstrip("-").isdigit() else float(t)
    except (ValueError, TypeError):
        raise GalatInsJay("Isi '%s' bukan angka sehingga tidak bisa dihitung." % ke_teks(v))


def _hashable(v):
    if isinstance(v, (list, dict, set)):
        return json.dumps(susun_json(v), ensure_ascii=False)
    return v


def _ambil(obj, kunci):
    if obj is None or obj is MISSING:
        return None
    try:
        if isinstance(obj, dict):
            return obj.get(ke_teks(kunci))
        if isinstance(obj, (list, tuple)):
            i = ke_angka(kunci)
            return obj[i] if 0 <= i < len(obj) else None
        return None
    except Exception:
        return None


def _punya(obj, kunci):
    if isinstance(obj, dict):
        return ke_teks(kunci) in obj
    if isinstance(obj, set):
        return _hashable(kunci) in obj
    if isinstance(obj, (list, tuple)):
        return kunci in obj
    if isinstance(obj, str):
        return ke_teks(kunci) in obj
    return False


def _memuat(obj, nilai):
    if obj is None or obj is MISSING:
        return False
    if isinstance(obj, set):
        return _hashable(nilai) in obj
    if isinstance(obj, dict):
        return ke_teks(nilai) in obj
    if isinstance(obj, (list, tuple, str)):
        try:
            return nilai in obj
        except Exception:
            return False
    return False


def _jalur(obj, jalur):
    kini = obj
    for bagian in str(jalur).split("."):
        if kini is None or kini is MISSING:
            return None
        kini = _ambil(kini, bagian)
    return kini


def _jenis(v):
    if v is None or v is MISSING:
        return "kosong"
    if isinstance(v, bool):
        return "logika"
    if isinstance(v, (int, float)):
        return "angka"
    if isinstance(v, str):
        return "teks"
    if isinstance(v, list):
        return "deret"
    if isinstance(v, dict):
        return "peta"
    if isinstance(v, set):
        return "himpunan"
    return "lain"


def jalankan_bytecode(bytecode, masukan=None, keluaran=print, argv=None):
    return Mesin(bytecode, masukan=masukan, keluaran=keluaran, argv=argv).jalankan()
