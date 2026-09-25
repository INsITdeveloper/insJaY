__version__ = "0.6.0"

from .lexer import GalatInsJay
from .pipa import proses, simpan_bytecode, muat_bytecode
from .vm import Mesin, jalankan_bytecode
