import os
from bs4 import BeautifulSoup
from collections import defaultdict
from math import ceil

# Konstanta
CERITA_FOLDER = "cerita"
KATEGORI_FOLDER = "kategori"
OUTPUT_FOLDER = "output"
ARTIKEL_PER_PAGE = 7

# Buat folder output
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(os.path.join(OUTPUT_FOLDER, KATEGORI_FOLDER), exist_ok=True)

# Baca semua cerita dan parsing metadata
def parse_cerita():
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
                    "url": f"{CERITA_FOLDER}/{filename}"
                })
    return sorted(daftar_cerita, key=lambda x: x['updated'], reverse=True)

# Template artikel + related post
def render_related_posts(all_posts, current_post, limit=3):
    related = [p for p in all_posts if p['category'] == current_post['category'] and p['url'] != current_post['url']]
    related = related[:limit]
    if not related:
        return ''
    html = '<div class="related-posts"><h3>Related Posts</h3>\n<ul>\n'
    for art in related:
        html += f'<li><a href="{art["url"]}">{art["title"]}</a></li>\n'
    html += '</ul></div>\n'
    return html

# Render daftar artikel
def render_articles(articles, all_articles, is_index=True):
    html = '<div class="artikel-terbaru">Cerita Terbaru</div>\n'
    for art in articles:
        kategori_link = f"{KATEGORI_FOLDER}/{art['category']}.html" if is_index else f"{art['category']}.html"
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
<br/><br/>{art['updated']}<br/><br/>
<a href="{kategori_link}">{art['category']}</a>
</td></tr></tbody></table></div>
'''
        html += render_related_posts(all_articles, art)
    return html

# Pagination
def render_pagination(base_name, total_pages, current_page, subfolder=""):
    nav = '<div class="pagination">'
    for i in range(1, total_pages + 1):
        filename = f"{base_name}_page{i}.html" if i > 1 else f"{base_name}.html"
        if subfolder:
            filename = f"{subfolder}/{filename}"
        label = f"[{i}]"
        if i == current_page:
            nav += f'<strong>{label}</strong> '
        else:
            nav += f'<a href="{filename}">{label}</a> '
    nav += '</div>'
    return nav

# Gabungkan header, head, footer
def wrap_full_page(body_content, title="Cerita", custom_head_path="custom/custom_head.html"):
    with open("custom/custom_header.html", "r", encoding="utf-8") as f:
        header = f.read()
    with open("custom/custom_footer.html", "r", encoding="utf-8") as f:
        footer = f.read()
    with open(custom_head_path, "r", encoding="utf-8") as f:
        head = f.read()
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
{head}
</head>
<body>
{header}
{body_content}
{footer}
</body>
</html>"""

# Bangun index.html
def build_index(cerita_list):
    total = len(cerita_list)
    total_pages = ceil(total / ARTIKEL_PER_PAGE)
    for i in range(total_pages):
        start = i * ARTIKEL_PER_PAGE
        end = start + ARTIKEL_PER_PAGE
        halaman = cerita_list[start:end]
        content = render_articles(halaman, cerita_list, is_index=True)
        content += render_pagination("index", total_pages, i+1)
        final_html = wrap_full_page(content, title="Index")
        filename = "index.html" if i == 0 else f"index_page{i+1}.html"
        with open(os.path.join(OUTPUT_FOLDER, filename), "w", encoding="utf-8") as f:
            f.write(final_html)

# Bangun kategori/*.html
def build_kategori(cerita_list):
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
            content += render_pagination(kategori, total_pages, i+1)
            final_html = wrap_full_page(content, title=f"Kategori: {kategori}")
            filename = f"{kategori}.html" if i == 0 else f"{kategori}_page{i+1}.html"
            out_path = os.path.join(OUTPUT_FOLDER, KATEGORI_FOLDER, filename)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(final_html)

# MAIN
if __name__ == "__main__":
    cerita = parse_cerita()
    build_index(cerita)
    build_kategori(cerita)
    print("Situs berhasil dibangun di folder 'output/'")
