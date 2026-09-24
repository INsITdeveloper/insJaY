# -*- coding: utf-8 -*-
"""insJaY — compiler + runtime sendiri.

Paket ini berisi:
    lexer       TAHAP 1  Lexing
    parser      TAHAP 2  Parsing  ->  TAHAP 3 AST
    semantik    TAHAP 4  Penganalisis Semantik
    kompilator  TAHAP 5  Kompilasi ke bytecode
    vm          RUNTIME  Mesin virtual insJaY
    pipa        orkestrasi seluruh tahap
    cli         antarmuka baris perintah (`insjay`)
"""

__version__ = "0.5.0"

from .lexer import GalatInsJay  # noqa: F401
from .pipa import proses, simpan_bytecode, muat_bytecode  # noqa: F401
from .vm import Mesin, jalankan_bytecode  # noqa: F401
