import os
import telebot
import feedparser
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import base64
import requests
from datetime import datetime
import re

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
user_news_data = {}

# ==========================================
# FUNGSI PUBLISH KE GITHUB
# ==========================================
def eksekusi_publish_github(message, judul, link_sumber, gambar_url, tanggal, ringkasan, is_local=False, isi_berita="", link_sumber_html=""):
    try:
        slug_judul = re.sub(r'[^a-z0-9]+', '-', judul.lower()).strip('-')
        if not slug_judul:
            slug_judul = f"berita-{int(datetime.now().timestamp())}"
            
        file_name = f"{slug_judul}.html"
        link_tujuan = file_name
        
        html_content = f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{judul} - IDI Denpasar News</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {{
            theme: {{ 
                extend: {{ 
                    fontFamily: {{ sans: ['Inter', 'sans-serif'] }},
                    colors: {{ medical: '#004b87', 'medical-dark': '#003366', 'medical-light': '#e6f0fa', 'accent-green': '#00a651' }} 
                }} 
            }}
        }}
    </script>
</head>
<body class="bg-slate-50 antialiased text-slate-800 flex flex-col min-h-screen">
    <header class="bg-white/80 backdrop-blur-md shadow-sm sticky top-0 z-50 border-b border-slate-200">
        <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
            <div class="flex items-center space-x-3">
                <img src="logo.png" alt="Logo IDI" class="h-10 w-auto object-contain">
                <h1 class="text-xl md:text-2xl font-bold text-medical tracking-tight">IDI Cabang Denpasar</h1>
            </div>
            <a href="index.html" class="text-sm font-semibold text-slate-500 hover:text-medical transition duration-300 flex items-center gap-1">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path></svg>
                <span class="hidden sm:inline">Kembali ke Beranda</span>
            </a>
        </div>
    </header>

    <main class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-12 flex-grow">
        <article class="bg-white rounded-3xl shadow-xl shadow-slate-200/50 overflow-hidden border border-slate-100">
            <div class="relative w-full h-64 md:h-[450px]">
                <img src="{gambar_url}" alt="Cover Berita" class="w-full h-full object-cover">
                <div class="absolute inset-0 bg-gradient-to-t from-slate-900/90 via-slate-900/20 to-transparent"></div>
                <div class="absolute bottom-6 left-6 md:bottom-8 md:left-10 text-white pr-6">
                    <span class="inline-block bg-accent-green text-white text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider mb-3 shadow-lg">Berita Terkini</span>
                    <h1 class="text-3xl md:text-5xl font-extrabold text-white mb-4 leading-tight tracking-tight drop-shadow-md">{judul}</h1>
                    <div class="flex items-center text-sm font-medium text-slate-300 space-x-2">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
                        <span>{tanggal}</span>
                    </div>
                </div>
            </div>
            <div class="p-6 md:p-10 lg:px-12">
                <div class="prose prose-lg md:prose-xl prose-slate max-w-none leading-relaxed prose-a:text-medical hover:prose-a:text-medical-dark prose-img:rounded-2xl prose-img:shadow-md">
                    {isi_berita}
                </div>
                {link_sumber_html}
            </div>
            <div class="bg-slate-50 border-t border-slate-100 p-6 md:p-10 flex flex-col md:flex-row justify-between items-center gap-6">
                <div class="flex items-center gap-4">
                    <div class="w-14 h-14 rounded-full bg-medical-light flex items-center justify-center text-medical font-bold text-xl shadow-inner">ID</div>
                    <div>
                        <p class="text-sm text-slate-500 font-medium mb-0.5">Ditulis oleh</p>
                        <p class="text-lg font-bold text-slate-900">Redaksi IDI Denpasar</p>
                    </div>
                </div>
                <div class="flex gap-3 items-center">
                    <span class="text-sm text-slate-500 font-semibold mr-1">Bagikan:</span>
                    <a href="https://api.whatsapp.com/send?text={urllib.parse.quote(judul)}%20-%20Baca%20selengkapnya%20di%20website%20IDI%20Denpasar" target="_blank" class="w-10 h-10 rounded-full bg-white border border-slate-200 flex items-center justify-center text-slate-600 hover:bg-[#25D366] hover:text-white hover:border-transparent transition-all shadow-sm">
                        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
                    </a>
                </div>
            </div>
        </article>
    </main>

    <footer class="bg-white border-t border-slate-200 mt-8 py-10">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row justify-between items-center md:items-start gap-8">
            <div class="flex-1 text-center md:text-left">
                <div class="flex items-center justify-center md:justify-start space-x-3 mb-5">
                    <img src="logo.png" alt="Logo IDI" class="h-10 w-auto object-contain">
                    <h2 class="text-xl font-bold text-medical tracking-tight">IDI Cabang Denpasar</h2>
                </div>
                <div class="space-y-3">
                    <p class="text-slate-600 text-sm flex items-center justify-center md:justify-start"><span class="mr-3 text-lg">📍</span> Pertokoan Grand Sudirman Blok C-36 Jl. PB Sudirman Denpasar</p>
                    <p class="text-slate-600 text-sm flex items-center justify-center md:justify-start"><span class="mr-3 text-lg">📞</span> 087751444330</p>
                    <p class="text-slate-600 text-sm flex items-center justify-center md:justify-start"><span class="mr-3 text-lg">✉️</span> ididenpasar@gmail.com</p>
                </div>
            </div>
            <div class="flex-1 text-center md:text-right text-slate-400 text-sm flex flex-col md:justify-end h-full mt-4 md:mt-10">
                <p>&copy; 2026 Ikatan Dokter Indonesia Cabang Denpasar.</p>
                <p>All rights reserved.</p>
            </div>
        </div>
    </footer>
</body>
</html>"""

        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json"
        }

        # Simpan file artikel HTML
        encoded_content = base64.b64encode(html_content.encode('utf-8')).decode('utf-8')
        api_url_file = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file_name}"
        requests.put(api_url_file, json={"message": f"Auto-publish: {judul}", "content": encoded_content}, headers=headers)

        # Ambil index.html
        api_url_index = f"https://api.github.com/repos/{GITHUB_REPO}/contents/index.html"
        res_index = requests.get(api_url_index, headers=headers)
        
        if res_index.status_code != 200:
            bot.reply_to(message, "⚠️ File index.html tidak ditemukan di GitHub.")
            return

        index_data = res_index.json()
        index_sha = index_data.get("sha", "")
        index_content_decoded = base64.b64decode(index_data.get("content", "")).decode('utf-8')

        # Beri penanda unik (data-file) pada card artikel agar bisa dihapus otomatis nanti
        new_card_item = f'''
        <article data-file="{file_name}" class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden flex flex-col hover:shadow-md transition">
            <div class="h-48 bg-gray-200 relative overflow-hidden group">
                <a href="{link_tujuan}">
                    <img src="{gambar_url}" alt="Thumbnail" class="w-full h-full object-cover group-hover:scale-105 transition duration-300">
                </a>
                <span class="absolute top-4 left-4 bg-white/90 text-medical text-xs font-semibold px-3 py-1 rounded-full shadow">Berita Terkini</span>
            </div>
            <div class="p-6 flex flex-col flex-1">
                <div class="flex items-center text-xs text-gray-500 mb-3 space-x-2">
                    <span>📅 {tanggal}</span><span>•</span><span>Redaksi IDI</span>
                </div>
                <h3 class="font-bold text-lg text-gray-900 mb-2 leading-snug">
                    <a href="{link_tujuan}" class="hover:text-medical">{judul}</a>
                </h3>
                <p class="text-sm text-gray-600 leading-relaxed flex-1">{ringkasan}</p>
                <a href="{link_tujuan}" class="mt-4 inline-flex items-center text-sm font-semibold text-medical hover:text-accent-green transition">
                    Baca selengkapnya <span class="ml-1">→</span>
                </a>
            </div>
        </article>
        '''

        if '<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">' in index_content_decoded:
            index_content_updated = index_content_decoded.replace(
                '<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">',
                f'<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">\n    {new_card_item}'
            )
        else:
            index_content_updated = index_content_decoded + f"\n<div>{new_card_item}</div>"

        encoded_index = base64.b64encode(index_content_updated.encode('utf-8')).decode('utf-8')
        res_update_index = requests.put(api_url_index, json={"message": f"Update Berita: {judul}", "content": encoded_index, "sha": index_sha}, headers=headers)

        if res_update_index.status_code in [201, 200]:
            link_artikel = f"https://news.ididenpasar.org/{file_name}"
            pesan_sukses = f"✅ **SUKSES! ARTIKEL TELAH TAYANG DI WEB!**\n\n📄 **Judul:** {judul}\n\n🔗 **Link Berita Anda:**\n{link_artikel}\n\n*(Ketik `/list` jika ingin melihat daftar artikel untuk ditarik/dihapus)*"
            bot.reply_to(message, pesan_sukses, parse_mode='MARKDOWN')
        else:
            bot.reply_to(message, "⚠️ Berita terkirim, tapi gagal memperbarui index.html.")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Terjadi error saat proses publish: {e}")

# ==========================================
# COMMAND TELEGRAM & FITUR PULL OUT (HAPUS)
# ==========================================
@bot.message_handler(commands=['start', 'help'])
def sambutan(message):
    teks = "Halo Bos! 🤖 Asisten Redaksi IDI Denpasar siap bertugas!\n\n"
    teks += "👉 /cari & /publish [nomor] - Tarik berita otomatis\n"
    teks += "👉 /buat - Tulis artikel utuh manual\n"
    teks += "👉 /list - Lihat daftar artikel aktif di web (untuk hapus/tarik)\n"
    teks += "👉 /hapus [nomor] - Tarik/Hapus berita dari web\n"
    teks += "👉 /cancel - Membatalkan proses\n"
    bot.reply_to(message, teks)

@bot.message_handler(commands=['cancel'])
def batal_proses(message):
    chat_id = message.chat.id
    if chat_id in user_news_data:
        del user_news_data[chat_id]
    bot.reply_to(message, "❌ **Proses dibatalkan.**", parse_mode='Markdown')

# FITUR LIST ARTIKEL UNTUK PULL OUT
@bot.message_handler(commands=['list'])
def list_artikel_web(message):
    try:
        headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
        res_index = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/contents/index.html", headers=headers)
        if res_index.status_code != 200:
            bot.reply_to(message, "⚠️ Gagal membaca data website.")
            return
            
        index_content = base64.b64decode(res_index.json().get("content", "")).decode('utf-8')
        
        # Cari semua card artikel yang ada di index.html berdasarkan penanda data-file
        matches = re.findall(r'data-file="([^"]+)"', index_content)
        titles = re.findall(r'<h3 class="font-bold text-lg text-gray-900 mb-2 leading-snug">\s*<a href="[^"]+" class="hover:text-medical">([^<]+)</a>', index_content)
        
        if not matches:
            bot.reply_to(message, "📭 Belum ada artikel aktif di halaman utama website.")
            return
            
        user_news_data[message.chat.id] = {"active_articles": matches}
        
        teks = "📋 **DAFTAR ARTIKEL AKTIF DI WEBSITE:**\n\n"
        for i, filename in enumerate(matches):
            title_text = titles[i] if i < len(titles) else filename
            teks += f"<b>[{i+1}]</b> {title_text}\n<code>File: {filename}</code>\n\n"
        teks += "<i>Ketik <b>/hapus [nomor]</b> untuk menarik/menghapus artikel dari web! (Contoh: /hapus 1)</i>"
        
        bot.reply_to(message, teks, parse_mode='HTML')
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

# FITUR HAPUS / PULL OUT BERITA
@bot.message_handler(commands=['hapus'])
def hapus_artikel_web(message):
    chat_id = message.chat.id
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "⚠️ Format salah! Ketik `/list` dulu untuk melihat nomor urut, lalu ketik `/hapus [nomor]`.")
            return
            
        idx = int(parts[1]) - 1
        active_list = user_news_data.get(chat_id, {}).get("active_articles", [])
        
        if not active_list:
            # Jika user belum sempat /list, kita coba ambil data otomatis langsung dari GitHub
            headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
            res_index = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/contents/index.html", headers=headers)
            if res_index.status_code == 200:
                index_content = base64.b64decode(res_index.json().get("content", "")).decode('utf-8')
                active_list = re.findall(r'data-file="([^"]+)"', index_content)
                
        if not active_list or idx < 0 or idx >= len(active_list):
            bot.reply_to(message, "⚠️ Nomor artikel tidak valid atau daftar kosong. Silakan ketik `/list` terlebih dahulu.")
            return
            
        target_file = active_list[idx]
        headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
        
        bot.reply_to(message, f"🗑️ Sedang menarik/menghapus artikel `{target_file}` dari website... ⏳")
        
        # 1. Hapus file HTML spesifik artikel tersebut dari GitHub
        file_res = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/contents/{target_file}", headers=headers)
        if file_res.status_code == 200:
            file_sha = file_res.json().get("sha")
            requests.delete(f"https://api.github.com/repos/{GITHUB_REPO}/contents/{target_file}", 
                            json={"message": f"Hapus artikel: {target_file}", "sha": file_sha}, headers=headers)
                            
        # 2. Hapus card artikel tersebut dari index.html
        res_index = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/contents/index.html", headers=headers)
        if res_index.status_code == 200:
            index_data = res_index.json()
            index_sha = index_data.get("sha")
            index_content = base64.b64decode(index_data.get("content", "")).decode('utf-8')
            
            # Hapus blok <article data-file="target_file">...</article>
            pattern = re.compile(rf'<article data-file="{target_file}".*?</article>', re.DOTALL)
            updated_content = pattern.sub('', index_content)
            
            encoded_index = base64.b64encode(updated_content.encode('utf-8')).decode('utf-8')
            requests.put(f"https://api.github.com/repos/{GITHUB_REPO}/contents/index.html", 
                         json={"message": f"Pull out artikel: {target_file}", "content": encoded_index, "sha": index_sha}, headers=headers)
                         
        bot.reply_to(message, f"✅ **BERHASIL!** Artikel nomor {idx+1} (`{target_file}`) telah ditarik dan dihapus dari website.", parse_mode='MARKDOWN')
    except Exception as e:
        bot.reply_to(message, f"❌ Terjadi error saat menghapus: {e}")

# --- JALUR 1: BERITA OTOMATIS (GOOGLE NEWS) ---
@bot.message_handler(commands=['cari'])
def cari_berita(message):
    global latest_entries
    bot.reply_to(message, "🔍 Memindai berita kesehatan terpercaya... ⏳")
    query = urllib.parse.quote("Kesehatan Indonesia")
    url_feed = f"https://news.google.com/rss/search?q={query}&hl=id&gl=ID&ceid=ID:id"
    try:
        feed = feedparser.parse(url_feed)
        if not feed.entries:
            bot.reply_to(message, "⚠️ Maaf, berita tidak ditemukan.")
            return
        latest_entries = feed.entries[:3]
        pesan = "<b>Laporan Berita Kesehatan Terbaru 🤖📰</b>\n\n"
        for i, entry in enumerate(latest_entries):
            pesan += f"<b>[{i+1}] {entry.title}</b>\n🔗 <a href='{entry.link}'>Sumber Berita</a>\n\n"
        pesan += "<i>Ketik /publish 1 (atau 2 / 3) untuk menayangkan ke website!</i>"
        bot.reply_to(message, pesan, parse_mode='HTML', disable_web_page_preview=True)
    except Exception as e:
        bot.reply_to(message, f"❌ Terjadi kesalahan: {e}")

@bot.message_handler(commands=['publish'])
def publish_berita(message):
    global latest_entries
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "⚠️ Format salah! Ketik: /publish 1")
            return
        index = int(parts[1]) - 1
        if not latest_entries or index < 0 or index >= len(latest_entries):
            bot.reply_to(message, "⚠️ Daftar berita kosong. Ketik /cari dulu!")
            return
            
        entry = latest_entries[index]
        judul = entry.title
        link_sumber = entry.link
        tanggal = datetime.now().strftime("%d %B %Y")
        ringkasan = "Liputan dan informasi penting seputar dunia kesehatan terkini."
        
        gambar_url = "https://images.unsplash.com/photo-1505751172876-fa1923c5c528?auto=format&fit=crop&w=600&q=80"
        if 'description' in entry:
            if 'img src="' in entry.description:
                try:
                    gambar_url = entry.description.split('img src="')[1].split('"')[0]
                except:
                    pass
        
        isi_berita = f"Ini adalah layanan rangkuman berita otomatis dari redaksi IDI Denpasar. Mengingat kebijakan hak cipta dari penerbit media asli, kami tidak dapat menampilkan seluruh isi teks di halaman ini."
        link_sumber_html = f'<br><a href="{link_sumber}" target="_blank" style="display: inline-block; background: #004b87; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; margin-top: 10px;">Baca Artikel Asli Selengkapnya &rarr;</a><br><br><hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;"><p style="color: #666; font-size: 14px;"><strong>Sumber berita:</strong> <a href="{link_sumber}" target="_blank" style="color: #004b87; text-decoration: underline;">{link_sumber}</a></p>'
        
        bot.reply_to(message, "🚀 Sedang merakit Halaman Berita ke website... ⏳")
        eksekusi_publish_github(message, judul, link_sumber, gambar_url, tanggal, ringkasan, is_local=True, isi_berita=isi_berita, link_sumber_html=link_sumber_html)
    except Exception as e:
        bot.reply_to(message, f"Terjadi error: {e}")

# --- JALUR 2: PORTAL BERITA MANDIRI (ARTIKEL UTUH) ---
@bot.message_handler(commands=['buat'])
def buat_berita_manual(message):
    chat_id = message.chat.id
    user_news_data[chat_id] = {}
    msg = bot.reply_to(message, "📝 *BUAT ARTIKEL UTUH + FOTO*\n\nLangkah 1: Silakan balas pesan ini dengan **JUDUL** berita Anda:\n*(Ketik /cancel jika batal)*", parse_mode='Markdown')
    bot.register_next_step_handler(msg, proses_judul_manual)

def proses_judul_manual(message):
    chat_id = message.chat.id
    if message.text and message.text.startswith('/cancel'): return batal_proses(message)
    user_news_data[chat_id]['judul'] = message.text
    msg = bot.reply_to(message, "✨ Bagus! Langkah 2: Ketik **RINGKASAN SINGKAT**:")
    bot.register_next_step_handler(msg, proses_ringkasan_manual)

def proses_ringkasan_manual(message):
    chat_id = message.chat.id
    if message.text and message.text.startswith('/cancel'): return batal_proses(message)
    user_news_data[chat_id]['ringkasan'] = message.text
    msg = bot.reply_to(message, "📰 Mantap! Langkah 3: Ketik **ISI BERITA LENGKAP**:")
    bot.register_next_step_handler(msg, proses_isi_berita_manual)

def proses_isi_berita_manual(message):
    chat_id = message.chat.id
    if message.text and message.text.startswith('/cancel'): return batal_proses(message)
    user_news_data[chat_id]['isi_berita'] = message.text
    msg = bot.reply_to(message, "📸 Langkah 4: **Kirim/Upload FOTO** dari galeri HP Anda ke chat ini:")
    bot.register_next_step_handler(msg, proses_foto_manual)

def proses_foto_manual(message):
    chat_id = message.chat.id
    if message.text and message.text.startswith('/cancel'): return batal_proses(message)
        
    try:
        if message.photo:
            file_id = message.photo[-1].file_id
            file_info = bot.get_file(file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            foto_nama = f"img-{int(datetime.now().timestamp())}.jpg"
            gh_headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
            encoded_img = base64.b64encode(downloaded_file).decode('utf-8')
            api_url_img = f"https://api.github.com/repos/{GITHUB_REPO}/contents/images/{foto_nama}"
            
            res_img = requests.put(api_url_img, json={"message": f"Upload foto: {foto_nama}", "content": encoded_img}, headers=gh_headers)
            
            if res_img.status_code in [201, 200]:
                user_news_data[chat_id]['gambar_url'] = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/images/{foto_nama}"
            else:
                user_news_data[chat_id]['gambar_url'] = "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&w=600&q=80"
        else:
            user_news_data[chat_id]['gambar_url'] = "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&w=600&q=80"
            
        msg = bot.reply_to(message, "🔗 Terakhir! Langkah 5: Masukkan **LINK SUMBER ASLI** (Atau ketik `-` jika buatan sendiri):")
        bot.register_next_step_handler(msg, proses_link_sumber_manual)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Terjadi kesalahan: {e}")

def proses_link_sumber_manual(message):
    chat_id = message.chat.id
    if message.text and message.text.startswith('/cancel'): return batal_proses(message)
    
    link = message.text.strip()
    if link == '-' or link == '':
        link_sumber_html = "" 
    else:
        link_sumber_html = f'<br><br><hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;"><p style="color: #666; font-size: 14px;"><strong>Sumber asli artikel:</strong> <a href="{link}" target="_blank" style="color: #004b87; text-decoration: underline;">{link}</a></p>'

    judul = user_news_data[chat_id]['judul']
    ringkasan = user_news_data[chat_id]['ringkasan']
    isi_berita = user_news_data[chat_id]['isi_berita']
    gambar_url = user_news_data[chat_id]['gambar_url']
    tanggal = datetime.now().strftime("%d %B %Y")
    
    bot.reply_to(message, "🚀 Sedang merakit Halaman Artikel Utuh ke website... ⏳")
    eksekusi_publish_github(message, judul, link, gambar_url, tanggal, ringkasan, is_local=True, isi_berita=isi_berita, link_sumber_html=link_sumber_html)

print("Bot siap mendengarkan perintah Bos...")
bot.infinity_polling()
