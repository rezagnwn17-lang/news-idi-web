import os
import sys
import requests
import feedparser
import urllib.parse

print("Mempersiapkan Robot Redaksi IDI Denpasar...")

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("Error: Kunci rahasia Telegram tidak ditemukan!")
    sys.exit(1)

def kirim_pesan_telegram(pesan):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': pesan, 'parse_mode': 'HTML', 'disable_web_page_preview': True}
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("Status: Berita berhasil dikirim ke Telegram!")
        else:
            print(f"Error dari Telegram: {response.text}")
    except Exception as e:
        print(f"Gagal kirim pesan: {e}")

def cari_berita_kesehatan():
    print("Mencari berita dari Google News...")
    
    # Mencari berita spesifik tentang "Kesehatan Indonesia" di Google News
    query = urllib.parse.quote("Kesehatan Indonesia")
    url_feed = f"https://news.google.com/rss/search?q={query}&hl=id&gl=ID&ceid=ID:id"
    
    try:
        # Google tidak memblokir akses, jadi ini sangat aman
        feed = feedparser.parse(url_feed)

        if not feed.entries:
            return "Maaf Bos, sumber berita Google sedang gangguan. 😔"
        
        pesan = "<b>Laporan Jurnalis Robot! 🤖📰</b>\n"
        pesan += "Berikut 3 berita kesehatan terhangat (via Google News):\n\n"
        
        for i in range(min(3, len(feed.entries))):
            judul = feed.entries[i].title
            link = feed.entries[i].link
            pesan += f"{i+1}. <b>{judul}</b>\n<a href='{link}'>🔗 Baca di sini</a>\n\n"
            
        pesan += "<i>(Fitur selanjutnya: Ketik nomor berita untuk publikasi otomatis!)</i>"
        return pesan
        
    except Exception as e:
        return f"Waduh Bos, mesin scrapernya error: {e}"

if __name__ == "__main__":
    draft_berita = cari_berita_kesehatan()
    kirim_pesan_telegram(draft_berita)
