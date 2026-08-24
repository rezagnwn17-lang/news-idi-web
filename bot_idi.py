import os
import telebot
import feedparser
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import base64
import requests
from datetime import datetime

# --- DUMMY SERVER UNTUK RENDER/RAILWAY ---
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot Redaksi IDI Aktif!")

def run_dummy_server():
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()
# ---------------------------------------------

print("Menyalakan Mesin Asisten Redaksi 24 Jam...")

# MENGAMBIL DATA DARI ENVIRONMENT VARIABLES RAILWAY
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_REPO = os.environ.get('GITHUB_REPO', 'rezagnwn17-lang/news-idi-web')

if not BOT_TOKEN:
    print("Error: BOT_TOKEN belum disetel di Environment Variables!")
    exit()

bot = telebot.TeleBot(BOT_TOKEN)

# Penyimpanan sementara berita terakhir yang dicari
latest_entries = []

@bot.message_handler(commands=['start', 'help'])
def sambutan(message):
    teks = "Halo Bos! 🤖 Asisten Redaksi IDI Denpasar siap bertugas!\n\n"
    teks += "Perintah yang tersedia:\n"
    teks += "👉 /cari - Cari berita kesehatan terbaru\n"
    teks += "👉 /publish [nomor] - Auto-publish berita ke website\n"
    bot.reply_to(message, teks)

@bot.message_handler(commands=['cari'])
def cari_berita(message):
    global latest_entries
    bot.reply_to(message, "🔍 Memindai berita kesehatan terpercaya... ⏳")
    
    query = urllib.parse.quote("Kesehatan Indonesia")
    url_feed = f"https://news.google.com/rss/search?q={query}&hl=id&gl=ID&ceid=ID:id"
    
    try:
        feed = feedparser.parse(url_feed)
        if not feed.entries:
            bot.reply_to(message, "Maaf Bos, berita tidak ditemukan.")
            return

        latest_entries = feed.entries[:3]
        pesan = "<b>Laporan Berita Kesehatan Terbaru 🤖📰</b>\n\n"
        for i, entry in enumerate(latest_entries):
            pesan += f"<b>[{i+1}] {entry.title}</b>\n🔗 <a href='{entry.link}'>Sumber Berita</a>\n\n"
            
        pesan += "<i>Ketik /publish 1 (atau 2 / 3) untuk menayangkan langsung ke website!</i>"
        bot.reply_to(message, pesan, parse_mode='HTML', disable_web_page_preview=True)
    except Exception as e:
        bot.reply_to(message, f"Terjadi kesalahan: {e}")

@bot.message_handler(commands=['publish'])
def publish_berita(message):
    global latest_entries
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "⚠️ Format salah, Bos! Ketik contohnya: /publish 1")
            return
            
        index = int(parts[1]) - 1
        if not latest_entries or index < 0 or index >= len(latest_entries):
            bot.reply_to(message, "⚠️ Daftar berita kosong atau nomor pilihan tidak valid. Ketik /cari dulu ya!")
            return
            
        entry = latest_entries[index]
        judul = entry.title
        link_sumber = entry.link
        tanggal = datetime.now().strftime("%Y-%m-%d")
        
        # Nama file HTML unik
        file_name = f"berita-{int(datetime.now().timestamp())}.html"
        
        # Template HTML Cantik untuk Website
        html_content = f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{judul} - IDI Denpasar News</title>
    <link rel="stylesheet" href="style.css">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; background: #f4f4f9;">
    <div style="max-width: 800px; margin: auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <p style="color: #666; font-size: 14px;">📅 {tanggal} | Kategori: Informasi Kesehatan</p>
        <h1 style="color: #004b87;">{judul}</h1>
        <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
        <p>Artikel pilihan redaksi IDI Denpasar mengenai perkembangan dunia medis dan kesehatan terkini.</p>
        <br>
        <a href="{link_sumber}" target="_blank" style="background: #004b87; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Baca Artikel Selengkapnya di Sumber Asli</a>
        <br><br><hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="font-size: 12px; color: #886;"><a href="index.html">← Kembali ke Beranda Berita IDI Denpasar</a></p>
    </div>
</body>
</html>"""

        if not GITHUB_TOKEN:
            bot.reply_to(message, "❌ Gagal: GITHUB_TOKEN belum disetel di Railway Variables!")
            return

        # Mengirim file HTML otomatis ke GitHub Repository via API
        encoded_content = base64.b64encode(html_content.encode('utf-8')).decode('utf-8')
        api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file_name}"
        
        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json"
        }
        data = {
            "message": f"Auto-publish via Telegram Bot: {judul}",
            "content": encoded_content
        }
        
        response = requests.put(api_url, json=data, headers=headers)
        
        if response.status_code in [201, 200]:
            bot.reply_to(message, f"✅ **SUKSES, BOS!**\n\nBerita berhasil ditayangkan otomatis ke *website*!\n📄 Judul: {judul}\n🌐 Cek web Anda beberapa saat lagi di `news.ididenpasar.org`", parse_mode='MARKDOWN')
        else:
            bot.reply_to(message, f"❌ Gagal publish ke GitHub: {response.json().get('message', 'Unknown error')}")
            
    except Exception as e:
        bot.reply_to(message, f"Terjadi error saat proses publish: {e}")

print("Bot siap mendengarkan perintah Bos...")
bot.infinity_polling()
