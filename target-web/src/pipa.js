'use strict';
// ===========================================================================
// PIPA — orkestrasi seluruh tahap:
//   Lexing -> Parsing -> AST -> Penganalisis Semantik -> Kompilasi (JS)
// ===========================================================================

const fs = require('fs');
const path = require('path');

const { lex, GalatInsJay } = require('./lexer');
const { Parser } = require('./parser');
const { analisis } = require('./semantik');
const { kompilasi } = require('./kompilator');

/** Gabungkan semua 'menyambung cerita' menjadi satu AST datar. */
function selesaikanImpor(daftar, dir, dimuat) {
  const hasil = [];
  for (const n of daftar) {
    if (n.t === 'Sambung') {
      const p = path.resolve(dir, n.berkas);
      if (dimuat.has(p)) continue;
      if (!fs.existsSync(p)) {
        throw new GalatInsJay(`Cerita '${n.berkas}' tidak ditemukan.`, n.baris, n.berkas);
      }
      dimuat.add(p);
      const isi = fs.readFileSync(p, 'utf8');
      const ast = new Parser(lex(isi, p), p).program();
      hasil.push(...selesaikanImpor(ast.isi, path.dirname(p), dimuat));
    } else {
      hasil.push(n);
    }
  }
  return hasil;
}

/**
 * Jalankan seluruh pipeline untuk sebuah berkas .Jay.
 * @returns {{tokens, ast, program, analisis, js}}
 */
function proses(berkas) {
  const p = path.resolve(berkas);
  const isi = fs.readFileSync(p, 'utf8');

  // 1) LEXING
  const tokens = lex(isi, p);

  // 2) PARSING  ->  3) AST
  const ast = new Parser(tokens, p).program();

  // Sambung cerita lain (rata-kan AST agar analisis & kompilasi menyeluruh)
  const datar = selesaikanImpor(ast.isi, path.dirname(p), new Set([p]));
  const program = { t: 'Program', isi: datar };

  // 4) PENGANALISIS SEMANTIK
  const hasilAnalisis = analisis(program);

  // 5) KOMPILASI
  const js = kompilasi(program);

  return { tokens, ast, program, analisis: hasilAnalisis, js };
}

module.exports = { proses, selesaikanImpor };
