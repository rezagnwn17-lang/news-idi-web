import os
import sys
import requests
import feedparser

print("Mempersiapkan Robot Redaksi IDI Denpasar...")

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("Error: Kunci rahasia Telegram tidak ditemukan!")
    sys.exit(1)

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

def cari_berita_kesehatan():
    print("Mencari berita terbaru...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Kita langsung tembak Antara News Kesehatan yang servernya kuat dan ramah robot
    url_feed = "https://www.antaranews.com/rss/kesehatan.xml"
    
    try:
        response = requests.get(url_feed, headers=headers, timeout=10)
        feed = feedparser.parse(response.content)

        if not feed.entries:
            return "Maaf Bos, sumber berita sedang kosong hari ini. 😔"
        
        pesan = "<b>Laporan Jurnalis Robot! 🤖📰</b>\n"
        pesan += "Berikut 3 berita kesehatan terbaru hari ini (via Antara News):\n\n"
        
        for i in range(min(3, len(feed.entries))):
            judul = feed.entries[i].title
            link = feed.entries[i].link
            pesan += f"{i+1}. <b>{judul}</b>\n<a href='{link}'>🔗 Baca di sini</a>\n\n"
            
        pesan += "<i>(Fitur selanjutnya: Ketik nomor berita untuk publikasi otomatis!)</i>"
        return pesan
        
    except Exception as e:
        return f"Waduh Bos, mesin scrapernya masih error: {e}"

if __name__ == "__main__":
    draft_berita = cari_berita_kesehatan()
    kirim_pesan_telegram(draft_berita)
