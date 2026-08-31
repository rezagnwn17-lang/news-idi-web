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
user_news_data = {}

# ==========================================
# FUNGSI UPLOAD KE GITHUB (DUA MODE)
# ==========================================
def eksekusi_publish_github(message, judul, link_sumber, gambar_url, tanggal, ringkasan, is_local=False, isi_berita="", link_sumber_html=""):
    try:
        file_name = f"berita-{int(datetime.now().timestamp())}.html"
        
        # 1. TENTUKAN JENIS HALAMAN (Redirect atau Artikel Utuh)
        if is_local:
            # MODE PORTAL MANDIRI (ARTIKEL UTUH SEPERTI IDN TIMES DENGAN SUMBER DI BAWAH)
            html_content = f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{judul} - IDI Denpasar News</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {{
            theme: {{ extend: {{ colors: {{ medical: '#004b87', 'medical-dark': '#003366', 'medical-light': '#e6f0fa', 'accent-green': '#00a651' }} }} }}
        }}
    </script>
</head>
<body class="bg-gray-50 font-sans">
    <header class="bg-white shadow-sm sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
            <h1 class="text-2xl font-bold text-medical">IDI Denpasar News</h1>
            <a href="index.html" class="text-sm font-medium text-gray-600 hover:text-medical">← Kembali ke Beranda</a>
        </div>
    </header>
    <main class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <article class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            <div class="p-8">
                <div class="flex items-center text-sm text-gray-500 mb-4 space-x-3">
                    <span>📅 {tanggal}</span><span>•</span><span>Redaksi IDI Denpasar</span>
                </div>
                <h1 class="text-3xl md:text-4xl font-bold text-gray-900 mb-6 leading-tight">{judul}</h1>
                <img src="{gambar_url}" alt="Cover Berita" class="w-full h-auto max-h-[500px] object-cover rounded-xl mb-8">
                <div class="prose prose-lg max-w-none text-gray-700 leading-relaxed whitespace-pre-wrap">{isi_berita}</div>
                
                {link_sumber_html}
                
            </div>
        </article>
    </main>
</body>
</html>"""
            link_tujuan = file_name
        else:
            # MODE GOOGLE NEWS (REDIRECT KE SUMBER ASLI)
            html_content = f"""<!DOCTYPE html><html lang="id"><head><meta charset="UTF-8"><title>Redirecting...</title></head><body><script>window.location.href="{link_sumber}";</script></body></html>"""
            link_tujuan = link_sumber

        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json"
        }

        # 2. Upload File Berita ke GitHub
        encoded_content = base64.b64encode(html_content.encode('utf-8')).decode('utf-8')
        api_url_file = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file_name}"
        requests.put(api_url_file, json={"message": f"Auto-publish: {judul}", "content": encoded_content}, headers=headers)

        # 3. Ambil dan Update index.html
        api_url_index = f"https://api.github.com/repos/{GITHUB_REPO}/contents/index.html"
        res_index = requests.get(api_url_index, headers=headers)
        
        if res_index.status_code != 200:
            bot.reply_to(message, "⚠️ File index.html tidak ditemukan di GitHub.")
            return

        index_data = res_index.json()
        index_sha = index_data.get("sha", "")
        index_content_decoded = base64.b64decode(index_data.get("content", "")).decode('utf-8')

        new_card_item = f'''
        <article class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden flex flex-col hover:shadow-md transition">
            <div class="h-48 bg-gray-200 relative overflow-hidden group">
                <a href="{link_tujuan}" {"target='_blank'" if not is_local else ""}>
                    <img src="{gambar_url}" alt="Thumbnail" class="w-full h-full object-cover group-hover:scale-105 transition duration-300">
                </a>
                <span class="absolute top-4 left-4 bg-white/90 text-medical text-xs font-semibold px-3 py-1 rounded-full shadow">Berita Terkini</span>
            </div>
            <div class="p-6 flex flex-col flex-1">
                <div class="flex items-center text-xs text-gray-500 mb-3 space-x-2">
                    <span>📅 {tanggal}</span><span>•</span><span>{'Redaksi IDI' if is_local else 'Google News'}</span>
                </div>
                <h3 class="font-bold text-lg text-gray-900 mb-2 leading-snug">
                    <a href="{link_tujuan}" {"target='_blank'" if not is_local else ""} class="hover:text-medical">{judul}</a>
                </h3>
                <p class="text-sm text-gray-600 leading-relaxed flex-1">{ringkasan}</p>
                <a href="{link_tujuan}" {"target='_blank'" if not is_local else ""} class="mt-4 inline-flex items-center text-sm font-semibold text-medical hover:text-accent-green transition">
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
            bot.reply_to(message, f"✅ **SUKSES! ARTIKEL UTUH TELAH TAYANG DI WEB!**\n\n📄 Judul: {judul}\n🌐 Cek website utama Anda di `news.ididenpasar.org`", parse_mode='MARKDOWN')
        else:
            bot.reply_to(message, "⚠️ Berita terkirim, tapi gagal memperbarui index.html.")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Terjadi error saat proses publish: {e}")

# ==========================================
# COMMAND TELEGRAM
# ==========================================
@bot.message_handler(commands=['start', 'help'])
def sambutan(message):
    teks = "Halo Bos! 🤖 Asisten Redaksi IDI Denpasar siap bertugas!\n\n"
    teks += "👉 /cari & /publish [nomor] - Publish otomatis dari Google News (sistem redirect)\n"
    teks += "👉 /buat - Tulis ARTIKEL UTUH di website Anda sendiri!\n"
    teks += "👉 /cancel - Membatalkan proses pembuatan berita\n"
    bot.reply_to(message, teks)

@bot.message_handler(commands=['cancel'])
def batal_proses(message):
    chat_id = message.chat.id
    if chat_id in user_news_data:
        del user_news_data[chat_id]
    bot.reply_to(message, "❌ **Proses dibatalkan.** Ketik `/buat` jika ingin mulai lagi.", parse_mode='Markdown')

# --- JALUR 1: BERITA OTOMATIS (GOOGLE NEWS - REDIRECT) ---
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
        ringkasan = "Liputan dan informasi penting seputar dunia kesehatan terkini untuk masyarakat."
        
        gambar_url = "https://images.unsplash.com/photo-1505751172876-fa1923c5c528?auto=format&fit=crop&w=600&q=80"
        if 'description' in entry:
            if 'img src="' in entry.description:
                try:
                    gambar_url = entry.description.split('img src="')[1].split('"')[0]
                except:
                    pass
        
        bot.reply_to(message, "🚀 Sedang memproses berita ke website... ⏳")
        eksekusi_publish_github(message, judul, link_sumber, gambar_url, tanggal, ringkasan, is_local=False)
    except Exception as e:
        bot.reply_to(message, f"Terjadi error: {e}")

# --- JALUR 2: PORTAL BERITA MANDIRI (ARTIKEL UTUH DENGAN LINK SUMBER) ---
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
    msg = bot.reply_to(message, "✨ Bagus! Langkah 2: Ketik **RINGKASAN SINGKAT** (Untuk teks di kartu halaman depan):")
    bot.register_next_step_handler(msg, proses_ringkasan_manual)

def proses_ringkasan_manual(message):
    chat_id = message.chat.id
    if message.text and message.text.startswith('/cancel'): return batal_proses(message)
    user_news_data[chat_id]['ringkasan'] = message.text
    msg = bot.reply_to(message, "📰 Mantap! Langkah 3: Ketik **ISI BERITA LENGKAP** (Pastikan copy-paste artikelnya sampai selesai ya):")
    bot.register_next_step_handler(msg, proses_isi_berita_manual)

def proses_isi_berita_manual(message):
    chat_id = message.chat.id
    if message.text and message.text.startswith('/cancel'): return batal_proses(message)
    user_news_data[chat_id]['isi_berita'] = message.text
    msg = bot.reply_to(message, "📸 Langkah 4: **Kirim/Upload FOTO** dari galeri HP Anda ke chat ini (sebagai Cover Artikel):")
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
            
        # Minta Link Sumber
        msg = bot.reply_to(message, "🔗 Terakhir! Langkah 5: Masukkan **LINK SUMBER ASLI** (Atau ketik `-` jika berita ini murni buatan sendiri):")
        bot.register_next_step_handler(msg, proses_link_sumber_manual)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Terjadi kesalahan: {e}")

def proses_link_sumber_manual(message):
    chat_id = message.chat.id
    if message.text and message.text.startswith('/cancel'): return batal_proses(message)
    
    link = message.text.strip()
    if link == '-' or link == '':
        link_sumber_html = "" # Dikosongkan jika tidak ada link sumber
    else:
        # Menambahkan garis pembatas dan tulisan sumber asli di bawah artikel
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
