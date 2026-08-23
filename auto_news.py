import os
import sys
import requests
import feedparser

print("Mempersiapkan Robot Redaksi IDI Denpasar...")

# Mengambil Rahasia
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("Error: Kunci rahasia Telegram tidak ditemukan!")
    sys.exit(1)

# Fungsi Kirim ke Telegram (Di-upgrade)
def kirim_pesan_telegram(pesan):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': pesan, 'parse_mode': 'HTML'}
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("Status: Berita berhasil dikirim ke Telegram!")
        else:
            print(f"Error dari Telegram: {response.text}")
    except Exception as e:
        print(f"Gagal kirim pesan: {e}")

# Fungsi Mencari Berita
def cari_berita_kemenkes():
    print("Mencari berita terbaru dari Sehat Negeriku Kemenkes...")
    url_feed = "https://sehatnegeriku.kemkes.go.id/feed/"
    feed = feedparser.parse(url_feed)
    
    if not feed.entries:
        return "Maaf Bos, saya tidak menemukan berita terbaru hari ini. 😔"
    
    pesan = "<b>Laporan Jurnalis Robot! 🤖📰</b>\n"
    pesan += "Berikut 3 berita kesehatan terbaru dari Kemenkes RI:\n\n"
    
    # Ambil 3 berita teratas
    for i in range(min(3, len(feed.entries))):
        judul = feed.entries[i].title
        link = feed.entries[i].link
        pesan += f"{i+1}. <b>{judul}</b>\n<a href='{link}'>🔗 Baca di sumber</a>\n\n"
        
    pesan += "<i>(Fitur selanjutnya: Balas nomor berita untuk menulis ulang dan publish otomatis!)</i>"
    return pesan

# --- Eksekusi Utama ---
if __name__ == "__main__":
    draft_berita = cari_berita_kemenkes()
    kirim_pesan_telegram(draft_berita)
