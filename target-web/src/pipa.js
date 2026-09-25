'use strict';





const fs = require('fs');
const path = require('path');

const { lex, GalatInsJay } = require('./lexer');
const { Parser } = require('./parser');
const { analisis } = require('./semantik');
const { kompilasi } = require('./kompilator');


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


function proses(berkas) {
  const p = path.resolve(berkas);
  const isi = fs.readFileSync(p, 'utf8');


  const tokens = lex(isi, p);


  const ast = new Parser(tokens, p).program();


  const datar = selesaikanImpor(ast.isi, path.dirname(p), new Set([p]));
  const program = { t: 'Program', isi: datar };


  const hasilAnalisis = analisis(program);


  const js = kompilasi(program);

  return { tokens, ast, program, analisis: hasilAnalisis, js };
}

module.exports = { proses, selesaikanImpor };
