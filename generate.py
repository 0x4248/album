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
THUMB_MAX_SIZE = (640, 640)
THUMB_QUALITY = 90
YOUTUBE_VIDEO_ID = "GA3NJXFjwxc"

HEADERS = """
<style>
.album-wrap {
    border: 1px dashed var(--border-color);
    padding: 12px;
}

.album-wrap .album-title {
    margin-bottom: 8px;
}

.album-wrap .album-intro {
    margin-bottom: 8px;
}

.album-wrap .album-copy i {
    display: block;
    margin-bottom: 4px;
}

.album-wrap .camera-shelf {
    border: 1px solid var(--border-color);
    background-color: color-mix(in srgb, var(--primary-bg) 70%, var(--content-bg));
    padding: 8px;
    margin: 12px 0;
}

.album-wrap .camera-strip {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.album-wrap .camera-strip img {
    width: 180px;
    height: auto;
    border: 1px solid var(--border-color);
}

.album-wrap .album-jump {
    border-top: 1px solid var(--hr-color);
    border-bottom: 1px solid var(--hr-color);
    padding: 8px 0;
    margin: 12px 0;
}

.album-wrap .album-month {
    margin-top: 16px;
}

.album-wrap .album-month h2 {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
}

.album-wrap .album-day {
    margin-bottom: 16px;
    border-top: 1px solid var(--hr-color);
    padding-top: 8px;
}

.album-wrap .album-day h3 {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
}

.album-wrap .album-count {
    font-size: 12px;
    color: var(--italic-color);
}

.album-wrap .album-day-note {
    margin-bottom: 8px;
}

.album-wrap .album-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 10px;
}

.album-wrap figure {
    float: none;
    width: auto;
    margin: 0;
    height: auto;
    overflow: visible;
    border: 1px solid var(--border-color);
    padding: 6px;
    background-color: color-mix(in srgb, var(--primary-bg) 65%, var(--content-bg));
}

.album-wrap figure img {
    width: 100%;
    max-height: 260px;
    object-fit: contain;
    margin-bottom: 4px;
}

.album-wrap figcaption {
    color: var(--italic-color);
    height: auto;
    overflow: visible;
    line-height: 1.2em;
    font-size: 12px;
    text-align: left;
}

.album-wrap .album-empty-caption {
    opacity: 0.6;
}
</style>

<div class="album-wrap">
<p class="logo">My Album</p>
<p class="album-intro">Photos from my life, organised by date with some captions. No AI and real cameras used from the 90s to the present day.</p>
<p class="album-intro">Contains images from 4248 Media and the 4248 Arial Space Photography Laboratory (4248 ASPL).</p>
<div class="album-copy">
<i>© 2026 4248 Media, A part of 0x4248. Licensed under the Creative Commons Attribution-ShareAlike 4.0 License (CC BY-SA 4.0).</i>
<i>© 2026 4248 ASPL (4248 Arial Space Photography Laboratory), A part of 0x4248. Licensed under the Creative Commons Attribution-ShareAlike 4.0 License (CC BY-SA 4.0).</i>
<i>© 2026 0x4248.</i>
</div>

<div class="camera-shelf">
<h2>My camera collection:</h2>
<div class="camera-strip">
<img src="/album/cam_imgs/SONY_Mavica.jpg" loading="lazy" width="200" alt="Sony Mavica camera">
<img src="/album/cam_imgs/Canon_4000D.jpg" loading="lazy" width="200" alt="Canon 4000D camera">
<img src="/album/cam_imgs/Canon_5D.jpg" loading="lazy" width="200" alt="Canon 5D camera">
</div>
</div>

<p><a href="/album/fullscreen.html">Open fullscreen photobook mode</a></p>
"""

FULLSCREEN_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>0x4248 Album — Fullscreen Photobook</title>
    <link rel="stylesheet" href="/style.css">
    <style>
        html, body {
            width: 100%;
            height: 100%;
            overflow: hidden;
        }

        body {
            margin: 0;
            position: relative;
            background: #000;
            color: var(--primary-color);
        }

        .music-bg {
            position: fixed;
            inset: 0;
            z-index: -3;
            pointer-events: none;
            overflow: hidden;
        }

        .music-bg iframe {
            width: 100vw;
            height: 56.25vw;
            min-height: 100vh;
            min-width: 177.78vh;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            opacity: 0.28;
            filter: grayscale(100%);
        }

        .overlay {
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.55);
            z-index: -2;
        }

        .frame {
            height: 100vh;
            width: 100vw;
            max-width: none;
            display: grid;
            grid-template-rows: auto 1fr auto;
            padding: 10px;
            box-sizing: border-box;
            gap: 8px;
        }

        .topline {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border: 1px solid var(--border-color);
            background: rgba(0, 0, 0, 0.35);
            padding: 6px 10px;
        }

        .viewer {
            border: 1px solid var(--border-color);
            background: rgba(0, 0, 0, 0.35);
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 0;
            padding: 10px;
        }

        .viewer img {
            width: 100%;
            height: auto;
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
            border: 1px solid var(--border-color);
            background: #111;
            opacity: 1;
            transition: opacity 320ms ease-in-out;
            image-rendering: pixelated;
        }

        .viewer img.is-fading {
            opacity: 0;
        }

        .meta {
            border: 1px solid var(--border-color);
            background: rgba(0, 0, 0, 0.35);
            padding: 8px 10px;
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 8px;
            align-items: center;
        }

        .date {
            color: var(--h2-color);
            margin-bottom: 4px;
            font-family: 'Departure Mono', monospace;
        }

        .caption {
            color: var(--primary-color);
            min-height: 1.2em;
        }

        .controls {
            display: flex;
            gap: 6px;
            align-items: center;
            white-space: nowrap;
        }

        .controls button {
            font: inherit;
            color: var(--primary-color);
            background: var(--content-bg);
            border: 1px solid var(--border-color);
            padding: 5px 10px;
            cursor: pointer;
        }

        .controls button:hover {
            background: var(--link-hover-bg);
            color: #000;
        }

        .counter {
            color: var(--italic-color);
            font-size: 12px;
            text-align: right;
        }

        @media screen and (max-width: 700px) {
            .meta {
                grid-template-columns: 1fr;
            }

            .controls {
                justify-content: flex-start;
                flex-wrap: wrap;
            }
        }
    </style>
</head>
<body>
    <div class="music-bg">
        <iframe
            id="musicFrame"
            src="https://www.youtube-nocookie.com/embed/{{ youtube_video_id }}?autoplay=1&mute=1&controls=0&loop=1&playlist={{ youtube_video_id }}&modestbranding=1&rel=0&iv_load_policy=3&playsinline=1"
            title="Background music"
            referrerpolicy="strict-origin-when-cross-origin"
            allowfullscreen>
        </iframe>
    </div>
    <div class="overlay"></div>

    <main class="frame">
        <div class="topline">
            <div><span class="logo" style="font-size:22px;">0x4248 MEDIA</span></div>
            <div><a href="/album/">Back to album</a></div>
        </div>

        <section class="viewer">
            <img id="photo" src="" alt="Photobook image" loading="eager">
        </section>

        <section class="meta">
            <div>
                <div class="date" id="dateText"></div>
                <div class="caption" id="captionText"></div>
                <div class="counter" id="counterText"></div>
            </div>
            <div class="controls">
                <button id="prevBtn" type="button">← Prev</button>
                <button id="nextBtn" type="button">Next →</button>
                <button id="muteBtn" type="button">▶ Start music</button>
            </div>
        </section>
    </main>

    <script>
        const photos = {{ photo_data_json }};
        const musicVideoId = '{{ youtube_video_id }}';
        let index = 0;
        let musicMuted = true;
        let musicStarted = false;
        let renderSwapTimer = null;
        const preloadCache = new Map();

        const photoEl = document.getElementById('photo');
        const dateTextEl = document.getElementById('dateText');
        const captionTextEl = document.getElementById('captionText');
        const counterTextEl = document.getElementById('counterText');
        const musicFrameEl = document.getElementById('musicFrame');
        const muteBtnEl = document.getElementById('muteBtn');

        function musicSrc(muted) {
            const muteValue = muted ? '1' : '0';
            return 'https://www.youtube-nocookie.com/embed/' + musicVideoId
                + '?autoplay=1&mute=' + muteValue
                + '&controls=0&loop=1&playlist=' + musicVideoId
                + '&modestbranding=1&rel=0&iv_load_policy=3&playsinline=1';
        }

        function updateMuteButton() {
            if (!musicStarted) {
                muteBtnEl.textContent = '▶ Start music';
            } else {
                muteBtnEl.textContent = musicMuted ? '🔇 Unmute music' : '🔊 Mute music';
            }
        }

        function toggleMute() {
            if (!musicStarted) {
                musicStarted = true;
                musicMuted = false;
                musicFrameEl.src = musicSrc(false);
                updateMuteButton();
                return;
            }

            if (musicMuted) {
                musicMuted = false;
                musicFrameEl.src = musicSrc(false);
            } else {
                musicMuted = true;
                musicFrameEl.src = musicSrc(true);
            }

            updateMuteButton();
        }

        function applyPhoto(item) {
            photoEl.src = item.path;
            photoEl.alt = item.name;
            dateTextEl.textContent = item.date;
            captionTextEl.textContent = item.caption || 'No caption.';
            counterTextEl.textContent = (index + 1) + ' / ' + photos.length;
            window.location.hash = 'p-' + index;
            preloadAround(index);
        }

        function preloadAt(photoIndex) {
            const photo = photos[photoIndex];
            if (!photo) return;
            if (preloadCache.has(photo.path)) return;

            const img = new Image();
            img.decoding = 'async';
            img.src = photo.path;
            preloadCache.set(photo.path, img);

            if (preloadCache.size > 12) {
                const oldestKey = preloadCache.keys().next().value;
                preloadCache.delete(oldestKey);
            }
        }

        function preloadAround(currentIndex) {
            if (!photos.length) return;
            if (photos.length === 1) {
                preloadAt(currentIndex);
                return;
            }

            const prevIndex = (currentIndex - 1 + photos.length) % photos.length;
            const nextIndex = (currentIndex + 1) % photos.length;
            preloadAt(prevIndex);
            preloadAt(nextIndex);
        }

        function render(withFade = true) {
            if (!photos.length) {
                dateTextEl.textContent = 'No photos found';
                captionTextEl.textContent = '';
                counterTextEl.textContent = '';
                photoEl.removeAttribute('src');
                return;
            }

            const item = photos[index];
            const hasExistingImage = Boolean(photoEl.getAttribute('src'));

            if (renderSwapTimer) {
                clearTimeout(renderSwapTimer);
                renderSwapTimer = null;
            }

            if (withFade && hasExistingImage) {
                photoEl.classList.add('is-fading');
                renderSwapTimer = setTimeout(() => {
                    applyPhoto(item);
                    photoEl.classList.remove('is-fading');
                }, 190);
                return;
            }

            applyPhoto(item);
        }

        function prev() {
            if (!photos.length) return;
            index = (index - 1 + photos.length) % photos.length;
            render();
        }

        function next() {
            if (!photos.length) return;
            index = (index + 1) % photos.length;
            render();
        }

        document.getElementById('prevBtn').addEventListener('click', prev);
        document.getElementById('nextBtn').addEventListener('click', next);
        muteBtnEl.addEventListener('click', toggleMute);
        document.addEventListener('keydown', (event) => {
            if (event.key === 'ArrowLeft') prev();
            if (event.key === 'ArrowRight') next();
            if (event.key.toLowerCase() === 'm') toggleMute();
        });

        if (window.location.hash.startsWith('#p-')) {
            const parsed = Number(window.location.hash.replace('#p-', ''));
            if (Number.isInteger(parsed) && parsed >= 0 && parsed < photos.length) {
                index = parsed;
            }
        }

        updateMuteButton();
        render(false);
    </script>
</body>
</html>
"""

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
