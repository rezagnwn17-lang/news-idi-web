import os
import telebot
import feedparser
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import base64
import requests
from datetime import datetime

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

print("Menyalakan Mesin Asisten Redaksi 24 Jam...")

BOT_TOKEN = os.environ.get('BOT_TOKEN')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_REPO = os.environ.get('GITHUB_REPO', 'rezagnwn17-lang/news-idi-web')

if not BOT_TOKEN:
    print("Error: BOT_TOKEN belum disetel di Environment Variables!")
    exit()

bot = telebot.TeleBot(BOT_TOKEN)
latest_entries = []

@bot.message_handler(commands=['start', 'help'])
def sambutan(message):
    teks = "Halo Bos! 🤖 Asisten Redaksi IDI Denpasar siap bertugas!\n\n"
    teks += "Perintah yang tersedia:\n"
    teks += "👉 /cari - Cari berita kesehatan terbaru\n"
    teks += "👉 /publish [nomor] - Auto-publish berita & update index web\n"
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
            bot.reply_to(message, "⚠️ Maaf Bos, berita tidak ditemukan.")
            return

        latest_entries = feed.entries[:3]
        pesan = "<b>Laporan Berita Kesehatan Terbaru 🤖📰</b>\n\n"
        for i, entry in enumerate(latest_entries):
            pesan += f"<b>[{i+1}] {entry.title}</b>\n🔗 <a href='{entry.link}'>Sumber Berita</a>\n\n"
            
        pesan += "<i>Ketik /publish 1 (atau 2 / 3) untuk menayangkan langsung ke website!</i>"
        bot.reply_to(message, pesan, parse_mode='HTML', disable_web_page_preview=True)
    except Exception as e:
        bot.reply_to(message, f"❌ Terjadi kesalahan saat mencari berita: {e}")

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
        tanggal = datetime.now().strftime("%d %B %Y")
        
        # 1. LOGIKA MENCARI GAMBAR (Ambil dari RSS Google atau pakai Default Medis)
        gambar_url = "https://images.unsplash.com/photo-1505751172876-fa1923c5c528?auto=format&fit=crop&w=600&q=80" # Gambar cadangan stetoskop elegan
        if 'description' in entry:
            deskripsi = entry.description
            if 'img src="' in deskripsi:
                try:
                    gambar_url = deskripsi.split('img src="')[1].split('"')[0]
                except:
                    pass
        
        file_name = f"berita-{int(datetime.now().timestamp())}.html"
        
        # Script Pintar: Jika ada pengunjung nyasar ke file ini, langsung di-redirect ke sumber asli
        html_content = f"""<!DOCTYPE html>
<html lang="id">
<head><meta charset="UTF-8"><title>Redirecting...</title></head>
<body><script>window.location.href="{link_sumber}";</script></body>
</html>"""

        if not GITHUB_TOKEN:
            bot.reply_to(message, "❌ Gagal: GITHUB_TOKEN belum disetel!")
            return

        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json"
        }

        # Upload File Berita HTML Redirector
        encoded_content = base64.b64encode(html_content.encode('utf-8')).decode('utf-8')
        api_url_file = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file_name}"
        res_file = requests.put(api_url_file, json={"message": f"Auto-publish: {judul}", "content": encoded_content}, headers=headers)

        # Ambil index.html
        api_url_index = f"https://api.github.com/repos/{GITHUB_REPO}/contents/index.html"
        res_index = requests.get(api_url_index, headers=headers)
        
        if res_index.status_code != 200:
            bot.reply_to(message, "⚠️ File index.html tidak ditemukan.")
            return

        index_data = res_index.json()
        index_sha = index_data.get("sha", "")
        index_content_decoded = base64.b64decode(index_data.get("content", "")).decode('utf-8')

        # 3. Format Card Layout BARU DENGAN GAMBAR!
        new_card_item = f'''
        <article class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden flex flex-col hover:shadow-md transition">
            <!-- Bagian Gambar Preview -->
            <div class="h-48 bg-gray-200 relative overflow-hidden group">
                <img src="{gambar_url}" alt="Thumbnail" class="w-full h-full object-cover group-hover:scale-105 transition duration-300">
                <span class="absolute top-4 left-4 bg-white/90 text-medical text-xs font-semibold px-3 py-1 rounded-full shadow">Berita Terkini</span>
            </div>
            <!-- Bagian Teks Bawah -->
            <div class="p-6 flex flex-col flex-1">
                <div class="flex items-center text-xs text-gray-500 mb-3 space-x-2">
                    <span>📅 {tanggal}</span>
                    <span>•</span>
                    <span>Google News</span>
                </div>
                <h3 class="font-bold text-lg text-gray-900 mb-2 leading-snug">
                    <a href="{link_sumber}" target="_blank" class="hover:text-medical">{judul}</a>
                </h3>
                <p class="text-sm text-gray-600 leading-relaxed flex-1">Liputan dan informasi penting seputar dunia kesehatan terkini untuk masyarakat.</p>
                <a href="{link_sumber}" target="_blank" class="mt-4 inline-flex items-center text-sm font-semibold text-medical hover:text-accent-green transition">
                    Baca selengkapnya <span class="ml-1">→</span>
                </a>
            </div>
        </article>
        '''

        # Masukkan card baru ke dalam grid section
        if '<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">' in index_content_decoded:
            index_content_updated = index_content_decoded.replace(
                '<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">',
                f'<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">\n    {new_card_item}'
            )
        else:
            index_content_updated = index_content_decoded + f"\n<div>{new_card_item}</div>"

        # 4. Commit pembaruan index.html
        encoded_index = base64.b64encode(index_content_updated.encode('utf-8')).decode('utf-8')
        res_update_index = requests.put(api_url_index, json={"message": f"Update Berita Bergambar: {judul}", "content": encoded_index, "sha": index_sha}, headers=headers)

        if res_update_index.status_code in [201, 200]:
            bot.reply_to(message, f"✅ **SUKSES! BERITA BERGAMBAR TELAH TAYANG, BOS!**\n\n📄 Judul: {judul}\n🌐 Cek website utama Anda di `news.ididenpasar.org`", parse_mode='MARKDOWN')
        else:
            bot.reply_to(message, "⚠️ Berita terkirim, tapi gagal memperbarui index.html.")
            
    except Exception as e:
        bot.reply_to(message, f"Terjadi error saat proses publish: {e}")

print("Bot siap mendengarkan perintah Bos...")
bot.infinity_polling()
