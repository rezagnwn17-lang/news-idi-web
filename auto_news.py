import os
import sys
import urllib.request
import urllib.parse

print("Mempersiapkan Robot Redaksi IDI Denpasar...")

# Mengambil Rahasia dari Brankas GitHub
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    print("Error: Kunci rahasia Telegram tidak ditemukan di GitHub Secrets!")
    sys.exit(1)

print("Kunci Telegram berhasil dimuat!")

# --- Fungsi Kirim Pesan ke Telegram ---
def kirim_pesan_telegram(pesan):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({'chat_id': TELEGRAM_CHAT_ID, 'text': pesan}).encode('utf-8')
    try:
        urllib.request.urlopen(url, data=data)
        print("Status: Pesan berhasil dikirim ke Telegram!")
    except Exception as e:
        print(f"Error: Gagal kirim pesan karena {e}")

# --- Test Kirim Pesan Perdana ---
pesan_perdana = "Halo Bos! Saya Robot Redaksi IDI Denpasar. Saya sudah bangun, sistem nyambung 100%, dan saya siap bekerja mencari berita! 🤖🔥"

kirim_pesan_telegram(pesan_perdana)

# TODO: 1. Fungsi Scraping Berita Kemenkes/WHO (Whitelist Domain)
# TODO: 2. Fungsi AI Rewrite (Gaya Bahasa IDI Denpasar)
# TODO: 3. Fungsi Penerima Keputusan dari Telegram
