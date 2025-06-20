import os
from bs4 import BeautifulSoup
from collections import defaultdict
from math import ceil

# --- KONSTANTA ---
CERITA_FOLDER = "cerita"
KATEGORI_FOLDER = "kategori"
ARTIKEL_PER_PAGE = 7

# Pastikan folder 'kategori' ada di root
os.makedirs(KATEGORI_FOLDER, exist_ok=True)

# --- FUNGSI UTAMA ---

def parse_cerita():
    """
    Membaca semua file cerita dari CERITA_FOLDER dan mengekstrak metadata.
    Mengembalikan daftar cerita yang sudah diurutkan berdasarkan tanggal 'updated' terbaru.
    """
    daftar_cerita = []
    for filename in os.listdir(CERITA_FOLDER):
        if filename.endswith(".html"):
            filepath = os.path.join(CERITA_FOLDER, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, "html.parser")
            meta = {
                tag['name']: tag['content']
                for tag in soup.find_all("meta", {"name": True, "content": True})
            }
            if "title" in meta and "category" in meta:
                daftar_cerita.append({
                    "title": meta["title"],
                    "category": meta["category"],
                    "thumbnail": meta.get("thumbnail", ""),
                    "updated": meta.get("updated", ""),
                    # URL absolut dari root situs
                    "url": f"/{CERITA_FOLDER}/{filename}"
                })
    return sorted(daftar_cerita, key=lambda x: x['updated'], reverse=True)

def render_related_posts(all_posts, current_post, limit=3):
    """
    Membuat HTML untuk daftar postingan terkait (related posts).
    Menggunakan skema dan thumbnail yang sama dengan artikel utama.
    """
    related = [p for p in all_posts if p['category'] == current_post['category'] and p['url'] != current_post['url']]
    related = related[:limit]
    if not related:
        return ''

    html = '<div class="related-posts"><h3>Baca Juga</h3>\n' # Judul untuk related posts
    for art in related:
        # Link kategori untuk related posts, selalu absolut dari root
        kategori_link_related = f"/{KATEGORI_FOLDER}/{art['category']}.html"
        html += f'''
<div class="kosong"></div>
<div class="song-list related-item">
<table width="100%">
<tbody>
<tr>
<td class="pass">
<img src="{art['thumbnail']}">
</td>
<td valign="top">
<a href="{art['url']}"><strong>{art['title']}</strong></a>
<br/><br/>
<a href="{kategori_link_related}">{art['category']}</a>
</td></tr></tbody></table></div>
'''
    html += '</div>\n'
    return html

def render_articles(articles, all_articles, is_index=True):
    """
    Membuat HTML untuk daftar artikel (digunakan untuk index dan kategori).
    """
    html = '<div class="artikel-terbaru">Cerita Terbaru</div>\n'
    for art in articles:
        # Link kategori: absolut jika dari index, relatif jika dari dalam folder kategori
        kategori_link = f"/{KATEGORI_FOLDER}/{art['category']}.html" if is_index else f"{art['category']}.html"
        html += f'''
<div class="kosong"></div>
<div class="song-list">
<table width="100%">
<tbody>
<tr>
<td class="pass">
<img src="{art['thumbnail']}">
</td>
<td valign="top">
<a href="{art['url']}"><strong>{art['title']}</strong></a>
<br/><br/>{art['updated']}<br/>
<a href="{kategori_link}">{art['category']}</a>
</td></tr></tbody></table></div>
'''
        # Tambahkan related posts setelah setiap artikel utama
        html += render_related_posts(all_articles, art)
    return html

def render_pagination(base_name, total_pages, current_page, subfolder=""):
    """
    Membuat HTML untuk navigasi paginasi.
    """
    nav = '<div class="pagination">'
    for i in range(1, total_pages + 1):
        filename = f"{base_name}_page{i}.html" if i > 1 else f"{base_name}.html"
        full_path = ""
        if subfolder:
            # Jika ada subfolder (misal 'kategori'), link absolut dari root melewati subfolder
            full_path = f"/{subfolder}/{filename}"
        else:
            # Jika tidak ada subfolder (misal index.html), link absolut dari root
            full_path = f"/{filename}"

        label = f"[{i}]"
        if i == current_page:
            nav += f'<strong>{label}</strong> '
        else:
            nav += f'<a href="{full_path}">{label}</a> '
    nav += '</div>'
    return nav

def wrap_full_page(body_content, title="Cerita", custom_head_path="custom/custom_head.html"):
    """
    Menggabungkan header, head, body content, dan footer menjadi halaman HTML lengkap.
    """
    # Pastikan file custom ada
    if not os.path.exists("custom/custom_header.html"):
        raise FileNotFoundError("File custom/custom_header.html tidak ditemukan.")
    if not os.path.exists("custom/custom_footer.html"):
        raise FileNotFoundError("File custom/custom_footer.html tidak ditemukan.")
    if not os.path.exists(custom_head_path):
        raise FileNotFoundError(f"File {custom_head_path} tidak ditemukan.")

    with open("custom/custom_header.html", "r", encoding="utf-8") as f:
        header = f.read()
    with open("custom/custom_footer.html", "r", encoding="utf-8") as f:
        footer = f.read()
    with open(custom_head_path, "r", encoding="utf-8") as f:
        head = f.read()
    return f"""<!DOCTYPE html>
<html lang="id">
<head itemscope itemtype="https://schema.org/WebSite">
  <title>{title}</title>
{head}
</head>
<body itemscope itemtype="https://schema.org/WebPage">
<div class="site-container">
{header}
{body_content}
{footer}
</div>
</body>
</html>"""

def build_index(cerita_list):
    """
    Membangun halaman index.html dan halaman paginasi index_pageX.html.
    """
    total = len(cerita_list)
    total_pages = ceil(total / ARTIKEL_PER_PAGE)
    for i in range(total_pages):
        start = i * ARTIKEL_PER_PAGE
        end = start + ARTIKEL_PER_PAGE
        halaman = cerita_list[start:end]
        content = render_articles(halaman, cerita_list, is_index=True)
        content += render_pagination("index", total_pages, i+1)
        final_html = wrap_full_page(content, title="Index Cerita")
        filename = "index.html" if i == 0 else f"index_page{i+1}.html"
        # Tulis file langsung ke root
        with open(filename, "w", encoding="utf-8") as f:
            f.write(final_html)

def build_kategori(cerita_list):
    """
    Membangun halaman kategori/*.html dan halaman paginasi untuk setiap kategori.
    """
    kategori_map = defaultdict(list)
    for c in cerita_list:
        kategori_map[c['category']].append(c)

    for kategori, items in kategori_map.items():
        total_pages = ceil(len(items) / ARTIKEL_PER_PAGE)
        for i in range(total_pages):
            start = i * ARTIKEL_PER_PAGE
            end = start + ARTIKEL_PER_PAGE
            halaman = items[start:end]
            content = render_articles(halaman, items, is_index=False)
            content += render_pagination(kategori, total_pages, i+1, subfolder=KATEGORI_FOLDER)
            final_html = wrap_full_page(content, title=f"Kategori: {kategori}")
            filename = f"{kategori}.html" if i == 0 else f"{kategori}_page{i+1}.html"
            # Tulis file ke dalam folder 'kategori' di root
            out_path = os.path.join(KATEGORI_FOLDER, filename)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(final_html)

def build_individual_story_pages(cerita_list):
    """
    Membungkus setiap file HTML di folder 'cerita' dengan header, head, dan footer kustom.
    """
    print(f"Membungkus {len(cerita_list)} file cerita di folder '{CERITA_FOLDER}' dengan custom HTML...")
    for story_meta in cerita_list:
        # Dapatkan nama file dari URL cerita
        filename = os.path.basename(story_meta['url'])
        filepath = os.path.join(CERITA_FOLDER, filename)

        if not os.path.exists(filepath):
            print(f"Peringatan: File {filepath} tidak ditemukan, melompati.")
            continue

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                original_soup = BeautifulSoup(f, "html.parser")

            # Ambil semua konten yang ada di dalam tag body dari file asli
            # Jika tidak ada tag body, ambil semua konten
            body_content_tag = original_soup.find('body')
            if body_content_tag:
                # Menggunakan .decode_contents() untuk mendapatkan konten di dalam body
                # tanpa tag body itu sendiri
                article_body_content = "".join(str(item) for item in body_content_tag.contents)
            else:
                # Jika tidak ada tag body, asumsikan seluruh konten adalah body
                article_body_content = str(original_soup)

            # Bungkus konten body dengan header, head, dan footer
            final_html = wrap_full_page(article_body_content, title=story_meta['title'])

            # Timpa file asli di folder 'cerita'
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(final_html)
            print(f"Berhasil membungkus: {filepath}")

        except Exception as e:
            print(f"Error memproses {filepath}: {e}")

# --- EKSEKUSI UTAMA ---
if __name__ == "__main__":
    cerita = parse_cerita()
    build_index(cerita)
    build_kategori(cerita)
    build_individual_story_pages(cerita) # Panggil fungsi baru di sini
    print("\nSitus berhasil dibangun. File index.html, folder 'kategori/', dan file di 'cerita/' telah diperbarui/dibuat.")
