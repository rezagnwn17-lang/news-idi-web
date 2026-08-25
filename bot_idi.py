# Bagian ini menggantikan logika penyisipan di dalam def publish_berita(message):
        
        # 3. Sisipkan link berita baru ke dalam index.html dengan rapi di bagian atas daftar
        new_list_item = f'<li style="margin-bottom: 12px;"><a href="{file_name}" style="color: #004b87; font-size: 18px; text-decoration: none; font-weight: bold;">{judul}</a> <span style="color: #666; font-size: 12px;">({tanggal})</span></li>\n'
        
        # Cari tempat list berita di index.html, jika ada tag khusus, masukkan ke situ
        if '<ul id="daftar-berita">' in index_content_decoded:
            index_content_updated = index_content_decoded.replace(
                '<ul id="daftar-berita">',
                f'<ul id="daftar-berita">\n    {new_list_item}'
            )
        elif '<ul>' in index_content_decoded:
            # Masuk ke <ul> pertama yang ditemukan
            index_content_updated = index_content_decoded.replace(
                '<ul>',
                f'<ul>\n    {new_list_item}',
                1
            )
        else:
            # Jika tidak ada tag ul, sisipkan sebelum penutup body agar aman di atas footer
            if '</body>' in index_content_decoded:
                index_content_updated = index_content_decoded.replace(
                    '</body>',
                    f'<div style="max-width: 800px; margin: 20px auto; padding: 0 20px;">\n<h3>Berita Terbaru</h3>\n<ul>\n    {new_list_item}\n</ul>\n</div>\n</body>'
                )
            else:
                index_content_updated = index_content_decoded + f"\n<ul>\n    {new_list_item}\n</ul>"
