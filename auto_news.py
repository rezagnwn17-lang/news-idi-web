import os
import sys
import requests
import feedparser
import urllib.parse
from datetime import datetime

print("Mempersiapkan Redaktur AI IDI Denpasar...")

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GITHUB_TOKEN = os.environ.get("GH_PAT") or os.environ.get("GITHUB_TOKEN") # Mengambil token github untuk commit otomatis

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("Error: Kunci rahasia Telegram tidak ditemukan!")
    sys.exit(1)

def kirim_pesan_telegram(pesan):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': pesan, 'parse_mode': 'HTML', 'disable_web_page_preview': True}
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("Status: Berhasil dikirim ke Telegram!")
        else:
            print(f"Error dari Telegram: {response.text}")
    except Exception as e:
        print(f"Gagal kirim pesan: {e}")

def ambil_dan_kirim_berita():
    print("Mencari berita terbaru dari Google News...")
    query = urllib.parse.quote("Kesehatan Indonesia")
    url_feed = f"https://news.google.com/rss/search?q={query}&hl=id&gl=ID&ceid=ID:id"
    
    try:
        feed = feedparser.parse(url_feed)
        if not feed.entries:
            return "Maaf Bos, berita sedang kosong."
        
        pesan = "<b>Laporan Redaktur AI! 🤖📰</b>\n"
        pesan += "Pilih berita yang ingin otomatis dipublish ke web dengan membalas pesan ini atau menjalankan perintah selanjutnya:\n\n"
        
        # Simpan judul & link sementara (bisa dikembangkan dengan database/file log)
        for i in range(min(3, len(feed.entries))):
            judul = feed.entries[i].title
            link = feed.entries[i].link
            pesan += f"<b>[{i+1}] {judul}</b>\n🔗 {link}\n\n"
            
        pesan += "<i>(Robot siap mempublish artikel otomatis ke news.ididenpasar.org!)</i>"
        return pesan
    except Exception as e:
        return f"Error mengambil berita: {e}"

if __name__ == "__main__":
    hasil = ambil_dan_kirim_berita()
    kirim_pesan_telegram(hasil)
