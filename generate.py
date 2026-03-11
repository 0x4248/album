# Vibecoded:  I do not take credit for this code.

import os
import html
import json
from datetime import datetime

from PIL import Image, ImageOps, UnidentifiedImageError

BASE_DIR = "imgs"
THUMB_BASE_DIR = "imgs_thumb"
TEMPLATE_FILE = "template.html"
OUTPUT_FILE = "index.html"
FULLSCREEN_OUTPUT_FILE = "fullscreen.html"
TEMPLATES_DIR = "templates"
ALBUM_HEADER_TEMPLATE_FILE = os.path.join(TEMPLATES_DIR, "album_header.html")
FULLSCREEN_TEMPLATE_FILE = os.path.join(TEMPLATES_DIR, "fullscreen_template.html")
THUMB_MAX_SIZE = (640, 640)
THUMB_QUALITY = 90
YOUTUBE_VIDEO_ID = "J1NEO3vWU0c"

def read_template(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


HEADERS = read_template(ALBUM_HEADER_TEMPLATE_FILE)
FULLSCREEN_TEMPLATE = read_template(FULLSCREEN_TEMPLATE_FILE)

def month_name(year, month):
    return datetime(int(year), int(month), 1).strftime("%B %Y")

def to_html_text(text):
    return html.escape(text).replace("\n", "<br>")

def build_thumb_paths(year, month, day, filename):
    stem = filename.rsplit(".", 1)[0]
    thumb_dir = os.path.join(THUMB_BASE_DIR, year, month, day)
    thumb_file = f"{stem}.jpg"
    thumb_disk_path = os.path.join(thumb_dir, thumb_file)
    thumb_web_path = f"/album/{THUMB_BASE_DIR}/{year}/{month}/{day}/{thumb_file}"
    return thumb_dir, thumb_disk_path, thumb_web_path

def create_thumbnail(source_disk_path, year, month, day, filename):
    thumb_dir, thumb_disk_path, thumb_web_path = build_thumb_paths(year, month, day, filename)

    source_mtime = os.path.getmtime(source_disk_path)
    if os.path.exists(thumb_disk_path) and os.path.getmtime(thumb_disk_path) >= source_mtime:
        return thumb_web_path

    os.makedirs(thumb_dir, exist_ok=True)

    try:
        with Image.open(source_disk_path) as img:
            img = ImageOps.exif_transpose(img)

            if img.mode not in ("RGB", "L"):
                if "A" in img.getbands():
                    background = Image.new("RGB", img.size, (0, 0, 0))
                    background.paste(img, mask=img.getchannel("A"))
                    img = background
                else:
                    img = img.convert("RGB")
            elif img.mode == "L":
                img = img.convert("RGB")

            img.thumbnail(THUMB_MAX_SIZE, Image.Resampling.LANCZOS)
            img.save(
                thumb_disk_path,
                format="JPEG",
                quality=THUMB_QUALITY,
                optimize=True,
                progressive=True,
                subsampling=0,
            )
    except (UnidentifiedImageError, OSError):
        return f"/album/{BASE_DIR}/{year}/{month}/{day}/{filename}"

    return thumb_web_path

def collect_album_data():
    months = []

    for year in sorted(os.listdir(BASE_DIR), reverse=True):
        year_path = os.path.join(BASE_DIR, year)
        if not os.path.isdir(year_path):
            continue

        for month in sorted(os.listdir(year_path), reverse=True):
            month_path = os.path.join(year_path, month)
            if not os.path.isdir(month_path):
                continue

            days = []
            month_photo_count = 0

            for day in sorted(os.listdir(month_path), reverse=True):
                day_path = os.path.join(month_path, day)
                if not os.path.isdir(day_path):
                    continue

                full_day_name = datetime(int(year), int(month), int(day)).strftime("%A %d %B %Y")

                day_note = ""
                index_txt_path = os.path.join(day_path, "index.txt")
                if os.path.exists(index_txt_path):
                    with open(index_txt_path, "r", encoding="utf-8") as f:
                        day_note = f.read().strip()

                images = []
                for file in sorted(os.listdir(day_path)):
                    if not file.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")):
                        continue

                    source_disk_path = os.path.join(day_path, file)
                    img_path = f"/album/{BASE_DIR}/{year}/{month}/{day}/{file}"
                    thumb_path = create_thumbnail(source_disk_path, year, month, day, file)
                    caption_path = os.path.join(day_path, file.rsplit(".", 1)[0] + ".txt")
                    caption = ""
                    if os.path.exists(caption_path):
                        with open(caption_path, "r", encoding="utf-8") as f:
                            caption = f.read().strip()

                    images.append(
                        {
                            "path": img_path,
                            "thumb_path": thumb_path,
                            "name": file,
                            "caption": caption,
                        }
                    )

                if not images:
                    continue

                day_photo_count = len(images)
                month_photo_count += day_photo_count
                days.append(
                    {
                        "title": full_day_name,
                        "note": day_note,
                        "images": images,
                        "count": day_photo_count,
                    }
                )

            if not days:
                continue

            months.append(
                {
                    "anchor": f"m-{year}-{month}",
                    "title": month_name(year, month),
                    "days": days,
                    "count": month_photo_count,
                }
            )

    return months

def flatten_photo_data(months):
    photos = []
    for month in months:
        for day in month["days"]:
            for image in day["images"]:
                photos.append(
                    {
                        "path": image["path"],
                        "name": image["name"],
                        "date": day["title"],
                        "caption": image["caption"],
                    }
                )
    return photos

def generate_album_html(months):
    html_parts = [HEADERS]

    if months:
        html_parts.append('<div class="album-jump"><b>Jump to month:</b>')
        jump_links = [f'<a href="#{month["anchor"]}">{month["title"]}</a>' for month in months]
        html_parts.append(" [ " + " | ".join(jump_links) + " ]")
        html_parts.append("</div>")

    for month in months:
        html_parts.append(f'<section class="album-month" id="{month["anchor"]}">')
        html_parts.append(
            f'<h2>{month["title"]}<span class="album-count">{month["count"]} photos</span></h2>'
        )

        for day in month["days"]:
            html_parts.append('<article class="album-day">')
            html_parts.append(
                f'<h3>{day["title"]}<span class="album-count">{day["count"]} photos</span></h3>'
            )

            if day["note"]:
                html_parts.append(f'<p class="album-day-note">{to_html_text(day["note"])}</p>')

            html_parts.append('<div class="album-grid">')
            for image in day["images"]:
                escaped_caption = to_html_text(image["caption"]) if image["caption"] else '<span class="album-empty-caption">No caption.</span>'
                escaped_alt = html.escape(image["name"])
                html_parts.append(f"""
<figure>
  <a href="{image['path']}">
        <img src="{image['thumb_path']}" loading="lazy" alt="{escaped_alt}">
  </a>
  <figcaption>{escaped_caption}</figcaption>
</figure>
""")
            html_parts.append("</div>")
            html_parts.append("</article>")

        html_parts.append("</section>")

    html_parts.append("</div>")

    return "\n".join(html_parts)

def generate_fullscreen_html(months):
    photo_data_json = json.dumps(flatten_photo_data(months), ensure_ascii=False)
    html_text = FULLSCREEN_TEMPLATE.replace("{{ photo_data_json }}", photo_data_json)
    html_text = html_text.replace("{{ youtube_video_id }}", YOUTUBE_VIDEO_ID)
    return html_text


def generate():
    months = collect_album_data()

    # Read template
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        template = f.read()

    album_html = generate_album_html(months)

    # Replace placeholder
    final_html = template.replace("{{ content}}", album_html)
    final_html = final_html.replace("{{ content }}", album_html)

    # Write output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(final_html)

    fullscreen_html = generate_fullscreen_html(months)
    with open(FULLSCREEN_OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(fullscreen_html)

    print("Album pages generated successfully.")

if __name__ == "__main__":
    generate()
