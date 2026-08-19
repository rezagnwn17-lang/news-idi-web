#!/usr/bin/env python3
"""
auto_news.py - Portal Berita Otomatis IDI Cabang Denpasar
==========================================================
Alur Kerja:
1. Mengambil berita terbaru dari RSS Feed Kemenkes/SehatNegeriku
2. Mengirim ringkasan ke DeepSeek API untuk fact-checking & outline
3. Mengirim outline ke Hermes API untuk menulis artikel lengkap
4. Menyimpan artikel dalam format HTML & Markdown dengan metadata

Persyaratan:
- Python 3.8+
- Library: requests, feedparser, python-dotenv (opsional)
- API Keys: DeepSeek & Hermes (OpenRouter compatible)
"""

import os
import re
import json
import time
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from xml.etree import ElementTree

import requests
import feedparser

# ============================================================
# KONFIGURASI & API KEYS - ISI DENGAN API KEY ANDA DI SINI
# ============================================================
# DeepSeek API (untuk fact-checking & outline)
DEEPSEEK_API_KEY = "sk-your-deepseek-api-key-here"  # GANTI DENGAN API KEY DEEPSEEK ANDA
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"  # Endpoint resmi DeepSeek

# Hermes API (untuk drafting artikel) - Sesuaikan dengan endpoint provider Anda
# Hermes biasanya tersedia melalui OpenRouter, Together AI, atau endpoint kustom
HERMES_API_KEY = "your-hermes-api-key-here"  # GANTI DENGAN API KEY HERMES ANDA
HERMES_API_URL = "https://openrouter.ai/api/v1/chat/completions"  # Endpoint untuk Hermes (via OpenRouter)
HERMES_MODEL = "nousresearch/hermes-3-llama-3.1-405b"  # Model Hermes yang digunakan

# ============================================================
# KONFIGURASI RSS FEED & OUTPUT
# ============================================================
# Daftar RSS Feed sumber faktual (Kemenkes RI, SehatNegeriku, WHO Indonesia)
RSS_FEEDS = [
    {
        "name": "SehatNegeriku (Kemenkes)",
        "url": "https://sehatnegeriku.kemkes.go.id/feed/",
        "category": "Kemenkes RI"
    },
    {
        "name": "WHO Indonesia",
        "url": "https://www.who.int/indonesia/news/rss.xml",
        "category": "WHO"
    },
    # Tambahkan RSS feed lain jika diperlukan
]

# Direktori output untuk artikel yang dihasilkan
OUTPUT_DIR = Path("artikel_output")
OUTPUT_DIR.mkdir(exist_ok=True)

# Konfigurasi logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_news.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============================================================
# FUNGSI UTILITY & VALIDASI
# ============================================================
def sanitize_filename(text: str, max_length: int = 80) -> str:
    """
    Membersihkan string untuk digunakan sebagai nama file.
    Menghapus karakter ilegal dan membatasi panjang.
    """
    # Hapus karakter non-alfanumerik (kecuali spasi dan strip)
    cleaned = re.sub(r'[^\w\s-]', '', text)
    # Ganti spasi dengan underscore
    cleaned = re.sub(r'[\s]+', '_', cleaned.strip())
    # Potong jika terlalu panjang
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rstrip('_')
    # Tambahkan timestamp untuk keunikan
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_{cleaned}"


def validate_api_keys() -> bool:
    """Memvalidasi bahwa API keys telah diisi dengan benar."""
    missing_keys = []
    
    if DEEPSEEK_API_KEY == "sk-your-deepseek-api-key-here" or not DEEPSEEK_API_KEY:
        missing_keys.append("DeepSeek API Key")
    
    if HERMES_API_KEY == "your-hermes-api-key-here" or not HERMES_API_KEY:
        missing_keys.append("Hermes API Key")
    
    if missing_keys:
        logger.error(f"❌ API Keys belum dikonfigurasi: {', '.join(missing_keys)}")
        logger.error("Silakan edit file auto_news.py dan isi variabel DEEPSEEK_API_KEY dan HERMES_API_KEY")
        return False
    
    logger.info("✅ API Keys terkonfigurasi")
    return True


# ============================================================
# TAHAP 1: DATA SCRAPING / RSS FETCHING
# ============================================================
def fetch_rss_articles(feed_config: Dict, max_articles: int = 3) -> List[Dict]:
    """
    Mengambil artikel terbaru dari RSS Feed.
    
    Args:
        feed_config: Dictionary berisi 'name', 'url', 'category'
        max_articles: Jumlah maksimal artikel yang diambil
    
    Returns:
        List artikel dengan key: title, link, summary, source, published
    """
    logger.info(f"📡 Mengambil RSS dari: {feed_config['name']}")
    
    try:
        # Parse RSS feed dengan timeout
        feed = feedparser.parse(feed_config['url'])
        
        if feed.bozo and not feed.entries:
            logger.warning(f"⚠️ RSS Feed {feed_config['name']} mungkin tidak valid: {feed.bozo_exception}")
            return []
        
        articles = []
        for entry in feed.entries[:max_articles]:
            # Bersihkan HTML dari summary
            summary = entry.get('summary', entry.get('description', ''))
            # Hapus tag HTML untuk ringkasan bersih
            clean_summary = re.sub(r'<[^>]+>', '', summary)
            
            article = {
                'title': entry.get('title', 'Judul Tidak Tersedia').strip(),
                'link': entry.get('link', ''),
                'summary': clean_summary[:500],  # Batasi panjang ringkasan
                'published': entry.get('published', datetime.now().isoformat()),
                'source_name': feed_config['name'],
                'category': feed_config['category']
            }
            articles.append(article)
        
        logger.info(f"✅ Berhasil mengambil {len(articles)} artikel dari {feed_config['name']}")
        return articles
    
    except Exception as e:
        logger.error(f"❌ Gagal mengambil RSS {feed_config['name']}: {str(e)}")
        return []


def fetch_all_articles(max_total: int = 5) -> List[Dict]:
    """
    Mengambil artikel dari semua RSS feed yang dikonfigurasi.
    
    Returns:
        List artikel gabungan dari semua sumber
    """
    all_articles = []
    
    for feed_config in RSS_FEEDS:
        articles = fetch_rss_articles(feed_config, max_articles=3)
        all_articles.extend(articles)
        time.sleep(1)  # Jeda sopan antar request
    
    logger.info(f"📊 Total artikel terkumpul: {len(all_articles)}")
    return all_articles[:max_total]


# ============================================================
# TAHAP 2: PROSES AI - DEEPSEEK (FACT-CHECKING & OUTLINE)
# ============================================================
def process_with_deepseek(article: Dict) -> Optional[Dict]:
    """
    Mengirim artikel ke DeepSeek API untuk fact-checking dan pembuatan outline.
    
    DeepSeek akan:
    1. Memverifikasi fakta dari sumber Kemenkes/WHO
    2. Membuat outline edukasi kesehatan yang relevan untuk masyarakat Denpasar
    3. Menyusun poin-poin penting dengan konteks lokal
    
    Args:
        article: Dictionary berisi data artikel dari RSS
    
    Returns:
        Dictionary berisi outline dan hasil fact-checking
    """
    logger.info(f"🧠 DeepSeek: Memproses artikel: {article['title'][:60]}...")
    
    if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == "sk-your-deepseek-api-key-here":
        logger.error("❌ DeepSeek API Key tidak valid")
        return None
    
    # Prompt untuk DeepSeek
    system_prompt = """Anda adalah asisten fact-checker medis untuk IDI (Ikatan Dokter Indonesia) Cabang Denpasar, Bali.

TUGAS ANDA:
1. Lakukan fact-checking terhadap berita/ringkasan yang diberikan
2. Buat outline artikel edukasi kesehatan yang:
   - Relevan untuk masyarakat Denpasar dan Bali
   - Menggunakan bahasa yang mudah dipahami awam
   - Mencakup: Latar belakang, poin-poin penting, tips praktis, dan rekomendasi
   - Menyertakan konteks lokal (budaya Bali, fasilitas kesehatan di Denpasar, dll)
3. Berikan 3-5 poin utama untuk outline artikel

OUTPUT FORMAT (JSON):
{
    "fact_check": "Status verifikasi dan catatan faktual",
    "outline": [
        "Poin 1: ...",
        "Poin 2: ...",
        ...
    ],
    "target_audience": "Masyarakat Denpasar umum / lansia / ibu hamil / dll",
    "local_context": "Relevansi untuk wilayah Denpasar dan Bali"
}"""
    
    user_prompt = f"""
Berita dari: {article['source_name']} ({article['category']})
Judul: {article['title']}
Ringkasan: {article['summary']}

Buat fact-check dan outline artikel edukasi kesehatan untuk portal IDI Denpasar.
"""
    
    try:
        # Panggil DeepSeek API
        response = requests.post(
            DEEPSEEK_API_URL,
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.3,  # Rendah untuk fact-checking akurat
                "max_tokens": 1500,
                "response_format": {"type": "json_object"}  # Minta output JSON
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Parse JSON dari response
            try:
                deepseek_output = json.loads(content)
                logger.info("✅ DeepSeek berhasil memproses artikel")
                return {
                    'original_article': article,
                    'deepseek_analysis': deepseek_output,
                    'timestamp': datetime.now().isoformat()
                }
            except json.JSONDecodeError:
                # Fallback jika output bukan JSON valid
                logger.warning("⚠️ Output DeepSeek bukan JSON valid, menggunakan raw text")
                return {
                    'original_article': article,
                    'deepseek_analysis': {
                        'fact_check': 'Diproses oleh AI',
                        'outline': content.split('\n'),
                        'target_audience': 'Masyarakat umum',
                        'local_context': 'Wilayah Denpasar'
                    },
                    'timestamp': datetime.now().isoformat()
                }
        else:
            logger.error(f"❌ DeepSeek API error: {response.status_code} - {response.text[:200]}")
            return None
            
    except requests.exceptions.Timeout:
        logger.error("❌ DeepSeek API timeout")
        return None
    except Exception as e:
        logger.error(f"❌ Error DeepSeek processing: {str(e)}")
        return None


# ============================================================
# TAHAP 3: PROSES AI - HERMES (DRAFTING ARTIKEL LENGKAP)
# ============================================================
def process_with_hermes(deepseek_result: Dict) -> Optional[str]:
    """
    Mengirim outline dari DeepSeek ke Hermes API untuk menulis artikel lengkap.
    
    Hermes akan:
    1. Menulis artikel 400+ kata dengan gaya jurnalis IDI Denpasar
    2. Menggunakan format HTML (h2, p, ul, blockquote)
    3. Memasukkan disclaimer medis
    4. Menyertakan sumber asli
    
    Args:
        deepseek_result: Hasil dari DeepSeek berisi outline dan artikel asli
    
    Returns:
        Artikel lengkap dalam format HTML
    """
    logger.info(f"✍️ Hermes: Menulis artikel untuk: {deepseek_result['original_article']['title'][:60]}...")
    
    if not HERMES_API_KEY or HERMES_API_KEY == "your-hermes-api-key-here":
        logger.error("❌ Hermes API Key tidak valid")
        return None
    
    article = deepseek_result['original_article']
    analysis = deepseek_result['deepseek_analysis']
    
    # Konversi outline ke string yang terbaca
    outline_text = ""
    if 'outline' in analysis:
        if isinstance(analysis['outline'], list):
            outline_text = "\n".join([f"- {point}" for point in analysis['outline']])
        else:
            outline_text = str(analysis['outline'])
    
    system_prompt = """Anda adalah jurnalis kesehatan profesional untuk IDI (Ikatan Dokter Indonesia) Cabang Denpasar, Bali.

GAYA PENULISAN:
- Bahasa Indonesia formal namun ramah dan mudah dipahami
- Nada: Edukatif, profesional, dan empatik
- Target: Masyarakat umum di Denpasar dan Bali
- Panjang: Minimal 400 kata

FORMAT OUTPUT (HTML):
<h2>Judul Artikel</h2>
<p class="lead">Paragraf pembuka yang menarik...</p>
<h3>Sub-judul 1</h3>
<p>Konten paragraf...</p>
<ul>
  <li>Poin penting 1</li>
  <li>Poin penting 2</li>
</ul>
<blockquote class="medical-note">
  <p><strong>Catatan Medis:</strong> ...</p>
</blockquote>
<h3>Sub-judul 2</h3>
<p>Konten paragraf...</p>
<p class="disclaimer"><em>Disclaimer: Artikel ini bersifat informatif dan edukatif. Bukan pengganti konsultasi dokter.</em></p>

PENTING:
- Masukkan fakta yang sudah diverifikasi
- Tambahkan konteks lokal Denpasar/Bali
- Sertakan sumber asli berita
- Gunakan minimal 400 kata"""

    user_prompt = f"""
Buat artikel kesehatan untuk portal IDI Denpasar berdasarkan data berikut:

JUDUL ASLI: {article['title']}
SUMBER: {article['source_name']} ({article['category']})
TANGGAL: {article['published']}

OUTLINE DARI DEEPSEEK:
{outline_text}

TARGET AUDIENCE: {analysis.get('target_audience', 'Masyarakat umum')}
KONTEKS LOKAL: {analysis.get('local_context', 'Denpasar, Bali')}

Tulis artikel lengkap minimal 400 kata dalam format HTML. Gunakan gaya jurnalis IDI Denpasar yang profesional dan edukatif.
"""
    
    try:
        response = requests.post(
            HERMES_API_URL,
            headers={
                "Authorization": f"Bearer {HERMES_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://idi-denpasar.or.id",  # Untuk OpenRouter tracking
                "X-Title": "IDI Denpasar Portal"
            },
            json={
                "model": HERMES_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7,  # Lebih kreatif untuk penulisan
                "max_tokens": 2000,
            },
            timeout=90
        )
        
        if response.status_code == 200:
            result = response.json()
            article_html = result['choices'][0]['message']['content']
            
            # Validasi bahwa output mengandung HTML
            if '<h2>' in article_html or '<p>' in article_html:
                logger.info("✅ Hermes berhasil menulis artikel")
                return article_html
            else:
                logger.warning("⚠️ Output Hermes tidak mengandung HTML yang diharapkan")
                return article_html  # Tetap return meskipun tidak ideal
        else:
            logger.error(f"❌ Hermes API error: {response.status_code} - {response.text[:200]}")
            return None
            
    except requests.exceptions.Timeout:
        logger.error("❌ Hermes API timeout")
        return None
    except Exception as e:
        logger.error(f"❌ Error Hermes processing: {str(e)}")
        return None


# ============================================================
# TAHAP 4: SIMPAN OUTPUT (HTML & METADATA)
# ============================================================
def save_article(original_article: Dict, deepseek_result: Dict, hermes_html: str) -> Optional[Path]:
    """
    Menyimpan artikel lengkap sebagai file HTML dan metadata JSON.
    
    Args:
        original_article: Artikel asli dari RSS
        deepseek_result: Hasil analisis DeepSeek
        hermes_html: Artikel HTML dari Hermes
    
    Returns:
        Path ke file HTML yang disimpan
    """
    logger.info(f"💾 Menyimpan artikel: {original_article['title'][:50]}...")
    
    # Generate nama file yang unik
    base_filename = sanitize_filename(original_article['title'])
    
    # Siapkan metadata
    metadata = {
        'original_title': original_article['title'],
        'original_link': original_article['link'],
        'source': original_article['source_name'],
        'category': original_article['category'],
        'published_date': original_article['published'],
        'processed_date': datetime.now().isoformat(),
        'deepseek_fact_check': deepseek_result.get('deepseek_analysis', {}).get('fact_check', ''),
        'target_audience': deepseek_result.get('deepseek_analysis', {}).get('target_audience', ''),
        'local_context': deepseek_result.get('deepseek_analysis', {}).get('local_context', ''),
        'word_count': len(hermes_html.split()) if hermes_html else 0
    }
    
    # Buat HTML lengkap dengan wrapper dan metadata
    full_html = f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{original_article['title']} - IDI Denpasar</title>
    <meta name="description" content="{original_article['summary'][:160]}">
    <meta name="author" content="IDI Cabang Denpasar">
    <meta name="generator" content="IDI Denpasar AI News System">
    
    <!-- Metadata Artikel -->
    <meta property="article:published_time" content="{metadata['published_date']}">
    <meta property="article:section" content="{metadata['category']}">
    <meta property="article:tag" content="kesehatan, Denpasar, IDI, {metadata['category']}">
    
    <!-- Tailwind CSS untuk preview (opsional) -->
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ font-family: 'Inter', system-ui, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        .article-content h2 {{ color: #0e5e6f; font-size: 1.8rem; margin-top: 2rem; }}
        .article-content h3 {{ color: #0b7b4c; font-size: 1.4rem; margin-top: 1.5rem; }}
        .article-content p {{ line-height: 1.8; margin: 1rem 0; }}
        .article-content blockquote {{ border-left: 4px solid #0e5e6f; padding: 1rem; background: #f0f9f8; }}
        .disclaimer {{ background: #fff3cd; padding: 1rem; border-radius: 8px; font-size: 0.9rem; }}
        .metadata {{ background: #f8f9fa; padding: 1.5rem; border-radius: 8px; margin: 2rem 0; }}
    </style>
</head>
<body>
    <!-- Header Artikel -->
    <header style="border-bottom: 3px solid #0e5e6f; padding-bottom: 1rem; margin-bottom: 2rem;">
        <div style="display: flex; align-items: center; gap: 1rem;">
            <img src="../logo-idi-denpasar.png" alt="IDI Denpasar" style="height: 50px;">
            <div>
                <h1 style="color: #0e5e6f; margin: 0;">IDI Cabang Denpasar</h1>
                <p style="color: #666; margin: 0;">Portal Edukasi Kesehatan Terpercaya</p>
            </div>
        </div>
    </header>
    
    <!-- Konten Artikel -->
    <article class="article-content">
        {hermes_html}
    </article>
    
    <!-- Metadata & Sumber -->
    <div class="metadata">
        <h3 style="color: #0e5e6f;">📋 Informasi Artikel</h3>
        <p><strong>Sumber Asli:</strong> {metadata['source']} ({metadata['category']})</p>
        <p><strong>Tanggal Publikasi:</strong> {metadata['published_date']}</p>
        <p><strong>Target Audiens:</strong> {metadata['target_audience']}</p>
        <p><strong>Konteks Lokal:</strong> {metadata['local_context']}</p>
        <p><strong>Diproses oleh:</strong> Sistem AI IDI Denpasar (DeepSeek + Hermes)</p>
        <p><strong>Status Fact-Check:</strong> ✅ {metadata['deepseek_fact_check'][:200]}</p>
        <p><strong>Jumlah Kata:</strong> {metadata['word_count']}</p>
    </div>
    
    <!-- Footer -->
    <footer style="margin-top: 3rem; padding: 1rem; border-top: 2px solid #eee; text-align: center;">
        <p class="disclaimer">
            <strong>⚠️ Disclaimer Medis:</strong> Portal ini dikelola oleh IDI Cabang Denpasar. 
            Artikel diproduksi dengan bantuan AI dari sumber faktual (Kemenkes, WHO) untuk tujuan edukasi. 
            Bukan pengganti diagnosis dokter.
        </p>
        <p style="color: #999; font-size: 0.9rem;">© {datetime.now().year} IDI Cabang Denpasar</p>
    </footer>
</body>
</html>"""
    
    try:
        # Simpan sebagai HTML
        html_path = OUTPUT_DIR / f"{base_filename}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(full_html)
        
        # Simpan juga metadata sebagai JSON
        json_path = OUTPUT_DIR / f"{base_filename}_metadata.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        # Simpan juga versi Markdown (plain text dari HTML)
        md_path = OUTPUT_DIR / f"{base_filename}.md"
        # Konversi sederhana HTML ke Markdown
        md_content = hermes_html
        md_content = re.sub(r'<h2[^>]*>(.*?)</h2>', r'## \1\n', md_content)
        md_content = re.sub(r'<h3[^>]*>(.*?)</h3>', r'### \1\n', md_content)
        md_content = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', md_content)
        md_content = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1\n', md_content)
        md_content = re.sub(r'<[^>]+>', '', md_content)  # Hapus sisa tag HTML
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(f"# {original_article['title']}\n\n")
            f.write(f"*Sumber: {metadata['source']} | {metadata['published_date']}*\n\n")
            f.write(md_content)
            f.write(f"\n\n---\n*Artikel dibuat otomatis oleh sistem IDI Denpasar*\n")
        
        logger.info(f"✅ Artikel disimpan:")
        logger.info(f"   HTML: {html_path}")
        logger.info(f"   JSON: {json_path}")
        logger.info(f"   MD:   {md_path}")
        
        return html_path
        
    except Exception as e:
        logger.error(f"❌ Gagal menyimpan artikel: {str(e)}")
        return None


# ============================================================
# FUNGSI UTAMA - ORKESTRASI WORKFLOW
# ============================================================
def main():
    """Fungsi utama yang menjalankan seluruh workflow otomatisasi."""
    
    print("""
╔══════════════════════════════════════════════════╗
║   IDI DENPASAR - AUTO NEWS GENERATOR v1.0       ║
║   Otomatisasi Artikel Kesehatan                 ║
╚══════════════════════════════════════════════════╝
    """)
    
    # Validasi API Keys
    if not validate_api_keys():
        return
    
    logger.info("🚀 Memulai workflow otomatisasi berita...")
    
    # Tahap 1: Fetch RSS Articles
    logger.info("\n" + "="*50)
    logger.info("TAHAP 1: Mengambil berita dari RSS Feed")
    logger.info("="*50)
    
    articles = fetch_all_articles(max_total=3)  # Ambil maksimal 3 artikel
    
    if not articles:
        logger.error("❌ Tidak ada artikel yang berhasil diambil. Periksa koneksi internet dan RSS Feed.")
        return
    
    # Proses setiap artikel
    processed_count = 0
    for i, article in enumerate(articles, 1):
        logger.info(f"\n{'='*50}")
        logger.info(f"📰 MEMPROSES ARTIKEL {i}/{len(articles)}")
        logger.info(f"{'='*50}")
        logger.info(f"Judul: {article['title'][:80]}")
        logger.info(f"Sumber: {article['source_name']}")
        
        # Tahap 2: DeepSeek Fact-Check & Outline
        logger.info("\n🔍 TAHAP 2: DeepSeek Fact-Checking & Outline")
        deepseek_result = process_with_deepseek(article)
        
        if not deepseek_result:
            logger.warning(f"⚠️ Gagal memproses dengan DeepSeek, melanjutkan ke artikel berikutnya...")
            continue
        
        # Tahap 3: Hermes Article Writing
        logger.info("\n📝 TAHAP 3: Hermes Menulis Artikel")
        hermes_html = process_with_hermes(deepseek_result)
        
        if not hermes_html:
            logger.warning(f"⚠️ Gagal menulis artikel dengan Hermes, melanjutkan...")
            continue
        
        # Tahap 4: Save Article
        logger.info("\n💾 TAHAP 4: Menyimpan Artikel")
        saved_path = save_article(article, deepseek_result, hermes_html)
        
        if saved_path:
            processed_count += 1
            logger.info(f"✅ Artikel {i} berhasil diproses dan disimpan!")
        
        # Jeda antar artikel untuk menghormati rate limit API
        if i < len(articles):
            logger.info("⏳ Menunggu 3 detik sebelum artikel berikutnya...")
            time.sleep(3)
    
    # Ringkasan akhir
    logger.info(f"\n{'='*50}")
    logger.info(f"🎉 WORKFLOW SELESAI")
    logger.info(f"{'='*50}")
    logger.info(f"📊 Total artikel diambil: {len(articles)}")
    logger.info(f"✅ Artikel berhasil diproses: {processed_count}")
    logger.info(f"📁 Output disimpan di: {OUTPUT_DIR.absolute()}")
    
    if processed_count == 0:
        logger.warning("⚠️ Tidak ada artikel yang berhasil diproses. Periksa log untuk detail error.")
    else:
        logger.info("✅ Artikel siap diunggah ke website IDI Denpasar!")


# ============================================================
# FUNGSI TESTING (untuk development)
# ============================================================
def test_with_sample_data():
    """
    Fungsi testing dengan data sampel jika RSS Feed tidak tersedia.
    Berguna untuk testing workflow tanpa koneksi internet.
    """
    logger.info("🧪 Menjalankan mode TEST dengan data sampel...")
    
    sample_article = {
        'title': 'Kemenkes Imbau Warga Waspada DBD di Musim Hujan',
        'link': 'https://sehatnegeriku.kemkes.go.id/contoh-artikel-dbd',
        'summary': 'Kementerian Kesehatan mengimbau masyarakat untuk meningkatkan kewaspadaan terhadap Demam Berdarah Dengue (DBD) memasuki musim hujan. Data menunjukkan peningkatan kasus di beberapa wilayah, termasuk Bali. PSN 3M Plus menjadi kunci pencegahan.',
        'published': '2026-08-08T10:00:00+07:00',
        'source_name': 'SehatNegeriku (Kemenkes)',
        'category': 'Kemenkes RI'
    }
    
    # Proses dengan DeepSeek
    deepseek_result = process_with_deepseek(sample_article)
    if not deepseek_result:
        logger.error("Test gagal di tahap DeepSeek")
        return
    
    # Proses dengan Hermes
    hermes_html = process_with_hermes(deepseek_result)
    if not hermes_html:
        logger.error("Test gagal di tahap Hermes")
        return
    
    # Simpan
    save_article(sample_article, deepseek_result, hermes_html)
    logger.info("✅ Test mode selesai!")


# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__":
    import sys
    
    # Cek argumen command line
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Mode testing dengan data sampel
        test_with_sample_data()
    else:
        # Mode produksi normal
        main()
