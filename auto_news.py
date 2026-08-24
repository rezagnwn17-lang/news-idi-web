import os
import telebot
import feedparser
import urllib.parse

print("Menyalakan Mesin Asisten Redaksi 24 Jam...")

# Mengambil Kunci Token
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    print("Error: Kunci Token Telegram tidak ditemukan!")
    exit()

# Inisialisasi Bot Pendengar
bot = telebot.TeleBot(BOT_TOKEN)

# Respon saat Bos ketik /start
@bot.message_handler(commands=['start', 'help'])
def sambutan(message):
    teks = "Halo Bos! 🤖 Saya sekarang sudah punya telinga dan *online 24 jam*!\n\n"
    teks += "Silakan perintahkan saya:\n"
    teks += "👉 /cari - Untuk menyedot berita kesehatan terhangat (Google/CNN/dll)\n"
    bot.reply_to(message, teks)

# Respon saat Bos ketik /cari
@bot.message_handler(commands=['cari'])
def cari_berita(message):
    bot.reply_to(message, "🔍 Siap Bos! Memulai pencarian berita kesehatan terpercaya... Mohon tunggu sebentar ⏳")
    
    # Mencari berita kesehatan spesifik
    query = urllib.parse.quote("Kesehatan Indonesia")
    url_feed = f"https://news.google.com/rss/search?q={query}&hl=id&gl=ID&ceid=ID:id"
    
    try:
        feed = feedparser.parse(url_feed)
        if not feed.entries:
            bot.reply_to(message, "Maaf Bos, saya tidak menemukan berita terbaru.")
            return

        pesan = "<b>Laporan Hasil Pencarian! 🤖📰</b>\n\n"
        for i in range(min(3, len(feed.entries))):
            judul = feed.entries[i].title
            link = feed.entries[i].link
            pesan += f"<b>[{i+1}] {judul}</b>\n🔗 <a href='{link}'>Baca di sini</a>\n\n"
            
        pesan += "<i>(Ketik /publish 1 untuk menayangkan berita nomor 1 secara otomatis ke website!)</i>"
        
        bot.reply_to(message, pesan, parse_mode='HTML', disable_web_page_preview=True)
    except Exception as e:
        bot.reply_to(message, f"Aduh Bos, mesin error: {e}")

# Respon saat Bos ketik /publish
@bot.message_handler(commands=['publish'])
def publish_berita(message):
    # Nanti logika publish HTML ke GitHub kita taruh di sini
    bot.reply_to(message, "🚀 Siap Bos! Fitur auto-publish HTML sedang dipasang di tahap selanjutnya. Segera hadir!")

# Menjaga telinga bot tetap terbuka 24/7
print("Bot siap mendengarkan perintah Bos...")
bot.infinity_polling()
