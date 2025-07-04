import os
import re
import json
import random
from bs4 import BeautifulSoup # Mengimpor BeautifulSoup

# === Konfigurasi Jalur Folder ===
# Direktori untuk menyimpan data internal (opsional, bisa dihapus jika tidak digunakan)
DATA_DIR = 'data'
# Direktori tempat Anda MENGUNGGAH file HTML postingan mentah Anda
POST_UPLOAD_DIR = 'posts' 
# Direktori untuk menyimpan file template HTML
TEMPLATE_DIR = 'template'
# Direktori untuk menyimpan file HTML kustom
CUSTOM_DIR = 'custom'
# Direktori OUTPUT untuk halaman label
LABEL_OUTPUT_DIR = 'labels' 
# Direktori OUTPUT untuk file HTML artikel individual dan index.html (ini adalah root utama)
ROOT_OUTPUT_DIR = '.' # Titik '.' berarti direktori saat ini (root repositori)

# Nama file JSON untuk caching postingan (opsional)
POSTS_JSON = os.path.join(DATA_DIR, 'posts.json')

POSTS_PER_PAGE = 10 # Jumlah postingan per halaman

# Buat direktori yang dibutuhkan jika belum ada
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(POST_UPLOAD_DIR, exist_ok=True) 
os.makedirs(LABEL_OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMPLATE_DIR, exist_ok=True) # Pastikan folder template ada
os.makedirs(CUSTOM_DIR, exist_ok=True)   # Pastikan folder custom ada

# === Utilitas ===
def extract_thumbnail(html_content_string):
    soup = BeautifulSoup(html_content_string, 'html.parser')
    img_tag = soup.find('img')
    if img_tag and img_tag.has_attr('src'):
        return img_tag['src']
    return 'https://pelukjanda.github.io/tema/no-thumbnail.jpg'

def strip_html_and_divs(html):
    soup = BeautifulSoup(html, 'html.parser')
    for div_tag in soup.find_all('div'):
        div_tag.unwrap()
    return soup.get_text(separator=' ', strip=True)

def remove_anchor_tags(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    for a_tag in soup.find_all('a'):
        a_tag.unwrap()
    return str(soup)

def sanitize_filename(title):
    return re.sub(r'\W+', '-', title.lower()).strip('-')

def render_labels(labels):
    if not labels:
        return ""
    html = ''
    for label in labels:
        filename = sanitize_filename(label)
        # Link ke halaman label yang berada di LABEL_OUTPUT_DIR
        html += f'<span><a href="/{LABEL_OUTPUT_DIR}/{filename}-1.html">{label}</a></span> '
    return html

def load_template(directory, filename):
    path = os.path.join(directory, filename)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def render_template(template, **context):
    rendered_template = template
    for key, value in context.items():
        placeholder = f'{{{{ {key} }}}}'
        if placeholder in rendered_template:
            rendered_template = rendered_template.replace(placeholder, str(value))
    return rendered_template

def paginate(total_items, per_page):
    total_pages = (total_items + per_page - 1) // per_page
    return total_pages

def generate_pagination_links(base_url, current, total):
    html = '<div class="pagination-container">'
    
    if current > 1:
        prev_page_suffix = "" if current - 1 == 1 and "index" in base_url else f"-{current - 1}"
        # Jika base_url adalah "index", ini akan menunjuk ke root "/"
        # Jika base_url adalah "labels/kategori", ini akan menunjuk ke "/labels/kategori-X.html"
        full_url = f"/{prev_page_suffix}.html" if base_url == "index" else f"/{base_url}{prev_page_suffix}.html"
        html += f'<span class="pagination-link older-posts"><a href="{full_url}">Previous Posts</a></span>'

    if current < total:
        next_page_suffix = f"-{current + 1}"
        full_url = f"/{next_page_suffix}.html" if base_url == "index" else f"/{base_url}{next_page_suffix}.html"
        html += f'<span class="pagination-link load-more"><a href="{full_url}">Load More</a></span>'
    
    html += '<span style="clear:both;"></span>'
    html += '</div>'
    return html

# === Komponen Custom (Head, Header, Sidebar, Footer) ===
# Memuat file custom dari CUSTOM_DIR
CUSTOM_HEAD_CONTENT = load_template(CUSTOM_DIR, "custom_head.html") if os.path.exists(os.path.join(CUSTOM_DIR, "custom_head.html")) else ""
CUSTOM_JS = load_template(CUSTOM_DIR, "custom_js.html") if os.path.exists(os.path.join(CUSTOM_DIR, "custom_js.html")) else ""
CUSTOM_HEADER = load_template(CUSTOM_DIR, "custom_header.html") if os.path.exists(os.path.join(CUSTOM_DIR, "custom_header.html")) else ""
CUSTOM_SIDEBAR = load_template(CUSTOM_DIR, "custom_sidebar.html") if os.path.exists(os.path.join(CUSTOM_DIR, "custom_sidebar.html")) else ""
CUSTOM_FOOTER = load_template(CUSTOM_DIR, "custom_footer.html") if os.path.exists(os.path.join(CUSTOM_DIR, "custom_footer.html")) else ""

CUSTOM_HEAD_FULL = CUSTOM_HEAD_CONTENT + CUSTOM_JS

# === Ambil semua postingan dari file HTML di folder 'posts' ===
def fetch_posts_from_html_files():
    all_posts = []
    for filename in os.listdir(POST_UPLOAD_DIR):
        if filename.endswith(".html"):
            filepath = os.path.join(POST_UPLOAD_DIR, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    html_doc = f.read()
                    soup = BeautifulSoup(html_doc, 'html.parser')

                    title_tag = soup.find('title')
                    title = title_tag.get_text(strip=True) if title_tag else None

                    if not title:
                        h1_tag = soup.find('h1')
                        title = h1_tag.get_text(strip=True) if h1_tag else None
                    if not title:
                        h2_tag = soup.find('h2')
                        title = h2_tag.get_text(strip=True) if h2_tag else os.path.splitext(filename)[0]

                    body_content_tag = soup.find('body')
                    content = str(body_content_tag) if body_content_tag else html_doc

                    labels = []
                    labels_container = soup.find(['div'], class_='post-labels') or soup.find(['div'], id='post-labels')
                    if labels_container:
                        for a_tag in labels_container.find_all('a'):
                            label_text = a_tag.get_text(strip=True)
                            if label_text:
                                labels.append(label_text)

                    post_data = {
                        'title': title,
                        'content': content, 
                        'labels': labels,
                        'id': sanitize_filename(title) if title else os.path.splitext(filename)[0],
                        'original_upload_filename': filename, # Nama file HTML yang diunggah
                        # 'date': date_str # Tambahkan jika Anda berhasil mengekstrak tanggal
                    }
                    all_posts.append(post_data)
            except Exception as e:
                print(f"Error processing file '{filename}': {e}")
                continue 

    # Pengurutan Postingan (default: berdasarkan nama file asli terbalik)
    all_posts.sort(key=lambda p: p['original_upload_filename'], reverse=True) 
    
    with open(POSTS_JSON, "w", encoding="utf-8") as f:
        json.dump(all_posts, f, ensure_ascii=False, indent=2)
    
    return all_posts

# === Template (memuat dari folder 'template') ===
POST_TEMPLATE = load_template(TEMPLATE_DIR, "post_template.html") 
INDEX_TEMPLATE = load_template(TEMPLATE_DIR, "index_template.html")
LABEL_TEMPLATE = load_template(TEMPLATE_DIR, "label_template.html")

# === Halaman per postingan ===
def generate_post_page(post, all_posts):
    # Nama file HTML yang akan dibuat di ROOT_OUTPUT_DIR (root utama)
    output_filename = f"{sanitize_filename(post['title'])}.html"
    output_filepath = os.path.join(ROOT_OUTPUT_DIR, output_filename)

    eligible_related = [p for p in all_posts if p['id'] != post['id'] and 'content' in p]
    num_related_posts = min(5, len(eligible_related))
    related_sample = random.sample(eligible_related, num_related_posts) if num_related_posts > 0 else []

    related_items_html = []
    for p_related in related_sample:
        # Link ke artikel terkait juga menunjuk ke ROOT_OUTPUT_DIR
        related_post_absolute_link = f"/{sanitize_filename(p_related['title'])}.html"
        
        related_post_content = p_related.get('content', '')
        thumb = extract_thumbnail(related_post_content)
        snippet = strip_html_and_divs(related_post_content)
        snippet = snippet[:100] + "..." if len(snippet) > 100 else snippet

        first_label_html = ""
        if p_related.get('labels'):
            label_name = p_related['labels'][0]
            sanitized_label_name = sanitize_filename(label_name)
            # Link ke halaman label yang berada di LABEL_OUTPUT_DIR
            first_label_html = f'<span class="category testing"><a href="/{LABEL_OUTPUT_DIR}/{sanitized_label_name}-1.html">{label_name}</a></span>'

        related_items_html.append(f"""
            <div class="post-card">
                <img class="post-image" src="{thumb}" alt="{p_related["title"]}">
                <div class="post-content">
                    <div class="post-meta">
                        {first_label_html}
                    </div>
                    <h2 class="post-title"><a href="{related_post_absolute_link}">{p_related["title"]}</a></h2>
                    <p class="post-author">By Om Sugeng · <a href="{related_post_absolute_link}">Baca Cerita</a></p>
                </div>
            </div>
        """)
    
    related_html = f"""
    <main class="container">
        <div class="post-list">
            {"".join(related_items_html)}
        </div>
    </main>
    """ if related_items_html else "<p>No related posts found.</p>"

    processed_content = post.get('content', '') 

    html = render_template(POST_TEMPLATE,
        title=post['title'],
        content=processed_content,
        labels=render_labels(post.get("labels", [])),
        related=related_html,
        custom_head=CUSTOM_HEAD_FULL,
        custom_header=CUSTOM_HEADER,
        custom_sidebar=CUSTOM_SIDEBAR,
        custom_footer=CUSTOM_FOOTER
    )
    with open(output_filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    return output_filename

# === Halaman index beranda ===
def generate_index(posts):
    total_pages = paginate(len(posts), POSTS_PER_PAGE)
    for page in range(1, total_pages + 1):
        start = (page - 1) * POSTS_PER_PAGE
        end = start + POSTS_PER_PAGE
        items = posts[start:end]

        items_html = ""
        for post in items:
            post_filename = generate_post_page(post, posts)
            # Link ke post individu di root
            post_absolute_link = f"/{post_filename}" 
            
            snippet = strip_html_and_divs(post.get('content', ''))[:100]
            thumb = extract_thumbnail(post.get('content', ''))

            first_label_html = ""
            if post.get('labels'):
                label_name = post['labels'][0]
                sanitized_label_name = sanitize_filename(label_name)
                # Link ke halaman label di LABEL_OUTPUT_DIR
                first_label_html = f'<span class="category testing"><a href="/{LABEL_OUTPUT_DIR}/{sanitized_label_name}-1.html">{label_name}</a></span>'
            
            items_html += f"""
<main class="container">
    <div class="post-list">
        <div class="post-card">
            <img class="post-image" src="{thumb}" alt="thumbnail">
            <div class="post-content">
                <div class="post-meta">
                    {first_label_html}
                </div>
                <h2 class="post-title"><a href="{post_absolute_link}">{post['title']}</a></h2>
                <p class="post-author">By Om Sugeng · <a href="{post_absolute_link}">Baca Cerita</a></p>
            </div>
        </div>
    </div>
</main>
"""
        # Base URL untuk paginasi index adalah "index"
        pagination = generate_pagination_links("index", page, total_pages)
        site_title = "Blog Om Sugeng" # Hardcoded, bisa diambil dari env var GH Actions

        html = render_template(INDEX_TEMPLATE,
            site_title=site_title, 
            items=items_html,
            pagination=pagination,
            custom_head=CUSTOM_HEAD_FULL,
            custom_header=CUSTOM_HEADER,
            custom_sidebar=CUSTOM_SIDEBAR,
            custom_footer=CUSTOM_FOOTER
        )
        # index.html akan dibuat di ROOT_OUTPUT_DIR
        output_file = os.path.join(ROOT_OUTPUT_DIR, f"index.html" if page == 1 else f"index-{page}.html")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

# === Halaman per label ===
def generate_label_pages(posts):
    label_map = {}
    for post in posts:
        if 'labels' in post:
            for label in post['labels']:
                label_map.setdefault(label, []).append(post)

    for label, label_posts in label_map.items():
        total_pages = paginate(len(label_posts), POSTS_PER_PAGE)
        for page in range(1, total_pages + 1):
            start = (page - 1) * POSTS_PER_PAGE
            end = start + POSTS_PER_PAGE
            items = label_posts[start:end]

            items_html = ""
            for post in items:
                post_filename = generate_post_page(post, posts)
                # Link ke post individu di root
                post_absolute_link = f"/{post_filename}"
                
                snippet = strip_html_and_divs(post.get('content', ''))[:100]
                thumb = extract_thumbnail(post.get('content', ''))

                first_label_html = ""
                if post.get('labels'):
                    label_name = post['labels'][0]
                    sanitized_label_name = sanitize_filename(label_name)
                    # Link ke halaman label di LABEL_OUTPUT_DIR
                    first_label_html = f'<span class="category testing"><a href="/{LABEL_OUTPUT_DIR}/{sanitized_label_name}-1.html">{label_name}</a></span>'

                items_html += f"""
<main class="container">
    <div class="post-list">
        <div class="post-card">
            <img class="post-image" src="{thumb}" alt="thumbnail">
            <div class="post-content">
                <div class="post-meta">
                    {first_label_html}
                </div>
                <h2 class="post-title"><a href="{post_absolute_link}">{post['title']}</a></h2>
                <p class="post-author">By Om Sugeng · <a href="{post_absolute_link}">Baca Cerita</a></p>
            </div>
        </div>
    </div>
</main>
"""
            # Base URL untuk paginasi label di dalam folder labels
            pagination = generate_pagination_links(
                f"{LABEL_OUTPUT_DIR}/{sanitize_filename(label)}", page, total_pages
            )
            site_title = "Blog Om Sugeng" # Hardcoded, bisa diambil dari env var GH Actions

            html = render_template(LABEL_TEMPLATE,
                site_title=site_title, 
                label=label,
                items=items_html,
                pagination=pagination,
                custom_head=CUSTOM_HEAD_FULL,
                custom_header=CUSTOM_HEADER,
                custom_sidebar=CUSTOM_SIDEBAR,
                custom_footer=CUSTOM_FOOTER
            )
            # File label akan dibuat di LABEL_OUTPUT_DIR
            output_file = os.path.join(LABEL_OUTPUT_DIR, f"{sanitize_filename(label)}-{page}.html")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)

# === Eksekusi ===
if __name__ == '__main__':
    print("--- Memulai Generator Situs Statis dari HTML ---")
    print(f"Mengunggah file HTML ke: {POST_UPLOAD_DIR}/")
    print(f"Template dimuat dari: {TEMPLATE_DIR}/")
    print(f"Komponen kustom dimuat dari: {CUSTOM_DIR}/")
    print(f"Halaman artikel individu akan muncul di: {ROOT_OUTPUT_DIR}/")
    print(f"Halaman label akan muncul di: {LABEL_OUTPUT_DIR}/")

    print("\n📥 Membaca artikel dari file HTML di folder 'posts'...")
    posts = fetch_posts_from_html_files()
    print(f"✅ Artikel berhasil dibaca: {len(posts)}")
    
    print("\n➡️ Membuat halaman index...")
    generate_index(posts)
    
    print("\n➡️ Membuat halaman label...")
    generate_label_pages(posts)
    
    print("\n--- Pembuatan situs selesai! ---") 
