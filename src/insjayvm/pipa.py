# -*- coding: utf-8 -*-
"""insJaY — pipeline lengkap.

    Lexing -> Parsing -> AST -> Penganalisis Semantik -> Kompilasi (bytecode)

Lalu bytecode dijalankan oleh Mesin insJaY (runtime sendiri).
"""

import json
import os

from .lexer import GalatInsJay, lex
from .parser import Parser
from .semantik import analisis
from .kompilator import kompilasi, VERSI_BYTECODE
from .vm import Mesin, jalankan_bytecode

MAGIS = "INSJAY"


def baca_ast(berkas):
    with open(berkas, "r", encoding="utf-8") as f:
        teks = f.read()
    tokens = lex(teks, berkas)
    ast = Parser(tokens, berkas).program()
    return tokens, ast


def selesaikan_impor(daftar, folder, dimuat):
    """Gabungkan semua 'menyambung cerita' menjadi satu AST datar."""
    hasil = []
    for n in daftar:
        if n["t"] == "Sambung":
            p = os.path.abspath(os.path.join(folder, n["berkas"]))
            if p in dimuat or not os.path.isfile(p):
                if not os.path.isfile(p):
                    raise GalatInsJay("Cerita '%s' tidak ditemukan." % n["berkas"],
                                      n.get("baris"), n.get("berkas"))
                continue
            dimuat.add(p)
            _, ast = baca_ast(p)
            hasil.extend(selesaikan_impor(ast["isi"], os.path.dirname(p), dimuat))
        else:
            hasil.append(n)
    return hasil


def proses(berkas):
    """Jalankan seluruh pipeline untuk berkas .Jay."""
    p = os.path.abspath(berkas)
    tokens, ast = baca_ast(p)
    datar = selesaikan_impor(ast["isi"], os.path.dirname(p), {p})
    program = {"t": "Program", "isi": datar}
    hasil_analisis = analisis(program)
    bytecode = kompilasi(program)
    return {"tokens": tokens, "ast": ast, "program": program,
            "analisis": hasil_analisis, "bytecode": bytecode}


def simpan_bytecode(bytecode, berkas):
    with open(berkas, "w", encoding="utf-8") as f:
        json.dump(bytecode, f, ensure_ascii=False, indent=1)


def muat_bytecode(berkas):
    with open(berkas, "r", encoding="utf-8") as f:
        return json.load(f)


def apakah_bytecode(berkas):
    try:
        with open(berkas, "r", encoding="utf-8") as f:
            awal = f.read(64).lstrip()
        return awal.startswith("{") and '"kode"' in awal
    except OSError:
        return False
