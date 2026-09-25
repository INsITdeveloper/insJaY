#!/usr/bin/env node
'use strict';














const fs = require('fs');
const path = require('path');
const readline = require('readline');

function muatBot(berkas) {
  const p = path.resolve(berkas);
  if (!fs.existsSync(p)) {
    console.error(`Berkas bot '${berkas}' tidak ditemukan.`);
    console.error('Kompilasi dulu:  insjay kompilasi whatsapp.Jay -o bot.js');
    process.exit(1);
  }
  const mod = require(p);
  if (typeof mod.balas !== 'function') {
    console.error("Bot harus menyerahkan kebiasaan 'balas'.");
    console.error("Tambahkan baris:  aku menyerahkan kebiasaan balas kepada dunia.");
    process.exit(1);
  }
  return mod;
}

async function modeWhatsApp(bot) {
  let baileys;
  try {
    baileys = require('@whiskeysockets/baileys');
  } catch (e) {
    console.error('Paket @whiskeysockets/baileys belum dipasang.');
    console.error('Jalankan:  npm install @whiskeysockets/baileys');
    process.exit(1);
  }
  const makeWASocket = baileys.default || baileys.makeWASocket;
  const { useMultiFileAuthState, DisconnectReason } = baileys;

  const { state, saveCreds } = await useMultiFileAuthState('sesi-wa');
  const sock = makeWASocket({ auth: state, printQRInTerminal: true });

  sock.ev.on('creds.update', saveCreds);
  sock.ev.on('connection.update', (u) => {
    if (u.connection === 'close') {
      const code = u.lastDisconnect && u.lastDisconnect.error && u.lastDisconnect.error.output
        ? u.lastDisconnect.error.output.statusCode : 0;
      console.log('Koneksi tertutup. Jalankan ulang untuk menyambung kembali.');
      if (code !== DisconnectReason.loggedOut) process.exit(0);
    }
  });

  sock.ev.on('messages.upsert', async ({ messages }) => {
    for (const m of messages) {
      if (!m.message) continue;
      const teks =
        m.message.conversation ||
        (m.message.extendedTextMessage && m.message.extendedTextMessage.text) ||
        '';
      if (!teks) continue;
      const dari = m.key.remoteJid;
      let balasan = '';
      try {
        balasan = bot.balas(teks) || '';
      } catch (err) {
        console.error('[galat bot]', err.message);
      }
      if (balasan) {
        try { await sock.sendMessage(dari, { text: String(balasan) }); }
        catch (err) { console.error('[galat kirim]', err.message); }
      }
    }
  });

  console.log('Bot WhatsApp insJaY aktif. Pindai QR yang muncul untuk masuk.');
}

function modeDemo(bot) {
  console.log('Mode demo insJaY — ketik pesan lalu tekan Enter (Ctrl+C untuk keluar).\n');
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout, terminal: false });
  rl.on('line', (baris) => {
    let balasan = '';
    try { balasan = bot.balas(baris) || ''; }
    catch (err) { balasan = '[galat] ' + err.message; }
    console.log('Pengguna > ' + baris);
    console.log('Bot      > ' + (balasan === '' ? '(diam)' : balasan) + '\n');
  });
}

const berkasBot = process.argv[2] || path.join(__dirname, 'bot.js');
const bot = muatBot(berkasBot);
if (process.argv.includes('--whatsapp')) modeWhatsApp(bot); else modeDemo(bot);
