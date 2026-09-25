import math
import random
from datetime import datetime

from .lexer import GalatInsJay


def ke_teks(v):
    if isinstance(v, bool):
        return "benar" if v else "salah"
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def ke_bool(v):
    if isinstance(v, str):
        return v.strip() != "" and v.lower() not in ("salah", "false", "0")
    return bool(v)


class Mesin:

    def __init__(self, bytecode, masukan=None, keluaran=print):
        self.konstanta = bytecode["konstanta"]
        self.fungsi = bytecode.get("fungsi", {})
        self.kode = bytecode["kode"]
        self.masukan = masukan or (lambda _prompt: input())
        self.keluaran = keluaran
        self.global_ = {}
        self.nilai = []
        self.bawaan = self._pustaka()

    def _pustaka(self):
        return {
            "akar": lambda a: math.sqrt(a[0]),
            "pangkat": lambda a: a[0] ** a[1],
            "bulat": lambda a: int(round(a[0])),
            "lantai": lambda a: math.floor(a[0]),
            "acak": lambda a: random.random(),
            "waktu_sekarang": lambda a: datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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
            if a is None:
                return 0
            try:
                return len(a)
            except TypeError:
                return 0
        if op == "keangka":
            try:
                t = ke_teks(a).strip()
                return int(t) if t.lstrip("-").isdigit() else float(t)
            except (ValueError, TypeError):
                raise GalatInsJay("Isi '%s' bukan angka sehingga tidak bisa dihitung." % ke_teks(a))
        if op == "hurufkecil":
            return ke_teks(a).lower()
        if op == "hurufbesar":
            return ke_teks(a).upper()
        if op == "mengandung":
            return ke_teks(b) in ke_teks(a)
        if op in ("==", "!=", ">", "<", ">=", "<="):
            return self._banding(a, b, op)
        raise GalatInsJay("Operasi '%s' tidak dikenal." % op)

    def jalankan(self):
        utama = {"kode": self.kode, "pc": 0, "lokal": self.global_, "induk": None}
        tumpukan = [utama]
        nilai = self.nilai
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
            elif op == "OP":
                operasi = ins["arg"]
                if operasi in ("tidak", "kebenaran", "panjang", "keangka", "hurufkecil", "hurufbesar"):
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
            elif op == "CALL":
                nama, argc = ins["arg"]
                args = nilai[-argc:] if argc else []
                if argc:
                    del nilai[-argc:]
                if nama in self.bawaan:
                    nilai.append(self.bawaan[nama](args))
                elif nama in self.fungsi:
                    fn = self.fungsi[nama]
                    lokal = {}
                    for p, v in zip(fn["params"], args):
                        lokal[p] = v
                    tumpukan.append({"kode": fn["kode"], "pc": 0, "lokal": lokal, "induk": self.global_})
                else:
                    raise GalatInsJay("Kebiasaan '%s' tidak ada di dalam bytecode." % nama)
            elif op == "KEMBALI":
                v = nilai.pop()
                tumpukan.pop()
                if tumpukan:
                    nilai.append(v)
            elif op == "SELESAI":
                tumpukan.pop()
            else:
                raise GalatInsJay("Perintah bytecode '%s' tidak dikenal." % op)


def jalankan_bytecode(bytecode, masukan=None, keluaran=print):
    return Mesin(bytecode, masukan=masukan, keluaran=keluaran).jalankan()
