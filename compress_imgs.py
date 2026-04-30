# Vibecoded:  I do not take credit for this code.

import argparse
import io
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError


DEFAULT_ROOT = "imgs"
DEFAULT_MAX_KB = 500
DEFAULT_MIN_KB = 200
JPEG_EXTS = {".jpg", ".jpeg"}
WEBP_EXTS = {".webp"}
PNG_EXTS = {".png"}
SUPPORTED_EXTS = JPEG_EXTS | WEBP_EXTS | PNG_EXTS
EXIF_ORIENTATION_TAG = 274


@dataclass
class Result:
    path: Path
    status: str
    old_bytes: int
    new_bytes: int
    note: str = ""


def human_kb(num_bytes: int) -> str:
    return f"{num_bytes / 1024:.1f}KB"


def normalize_image(img: Image.Image) -> Image.Image:
    img = ImageOps.exif_transpose(img)
    if img.mode in ("RGB", "L"):
        return img.convert("RGB") if img.mode == "L" else img

    if "A" in img.getbands():
        background = Image.new("RGB", img.size, (0, 0, 0))
        background.paste(img, mask=img.getchannel("A"))
        return background

    return img.convert("RGB")


def encode_jpeg(
    img: Image.Image,
    quality: int,
    subsampling: int,
    icc_profile: bytes | None,
    exif_bytes: bytes | None,
) -> bytes:
    buf = io.BytesIO()
    save_kwargs = dict(
        format="JPEG",
        quality=quality,
        optimize=True,
        progressive=True,
        subsampling=subsampling,
    )
    if icc_profile is not None:
        save_kwargs["icc_profile"] = icc_profile
    if exif_bytes is not None:
        save_kwargs["exif"] = exif_bytes

    img.save(buf, **save_kwargs)
    return buf.getvalue()


def encode_webp(
    img: Image.Image,
    quality: int,
    icc_profile: bytes | None,
    exif_bytes: bytes | None,
) -> bytes:
    buf = io.BytesIO()
    save_kwargs = dict(format="WEBP", quality=quality, method=6)
    if icc_profile is not None:
        save_kwargs["icc_profile"] = icc_profile
    if exif_bytes is not None:
        save_kwargs["exif"] = exif_bytes

    img.save(buf, **save_kwargs)
    return buf.getvalue()


def encode_png_lossless(img: Image.Image, icc_profile: bytes | None) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True, compress_level=9, icc_profile=icc_profile)
    return buf.getvalue()


def find_best_with_quality_search(
    img: Image.Image,
    encoder,
    target_bytes: int,
    min_quality: int,
    max_quality: int,
) -> tuple[bytes, int, bool]:
    first_data = encoder(img, max_quality)
    if len(first_data) <= target_bytes:
        return first_data, max_quality, True

    quality = max_quality - 7
    previous_quality = max_quality
    previous_data = first_data

    while quality > min_quality:
        data = encoder(img, quality)
        if len(data) <= target_bytes:
            low = quality
            high = previous_quality - 1
            best_data = data
            best_quality = quality

            while low <= high:
                mid = (low + high) // 2
                candidate = encoder(img, mid)
                if len(candidate) <= target_bytes:
                    best_data = candidate
                    best_quality = mid
                    low = mid + 1
                else:
                    high = mid - 1

            return best_data, best_quality, True

        previous_quality = quality
        previous_data = data
        quality -= 7

    final_data = encoder(img, min_quality)
    if len(final_data) < len(previous_data):
        return final_data, min_quality, False
    return previous_data, previous_quality, False


def process_image(
    path: Path,
    max_bytes: int,
    min_bytes: int,
    min_quality: int,
    max_quality: int,
    jpeg_subsampling: int,
    allow_resize: bool,
    min_scale: float,
    resize_step: float,
    dry_run: bool,
) -> Result:
    old_size = path.stat().st_size
    if old_size < min_bytes:
        return Result(path, "skipped-small", old_size, old_size)

    ext = path.suffix.lower()

    try:
        with Image.open(path) as img:
            icc_profile = img.info.get("icc_profile")
            exif = img.getexif()
            if exif:
                exif[EXIF_ORIENTATION_TAG] = 1
            exif_bytes = exif.tobytes() if exif else None
            img = normalize_image(img)

            if ext in JPEG_EXTS:
                new_data, quality, reached_target = find_best_with_quality_search(
                    img,
                    lambda im, q: encode_jpeg(im, q, jpeg_subsampling, icc_profile, exif_bytes),
                    max_bytes,
                    min_quality,
                    max_quality,
                )
                note = f"q={quality}"
                if not reached_target:
                    note += " (best effort)"

                if not reached_target and allow_resize:
                    scaled = img
                    scale = 1.0
                    while scale > min_scale:
                        scale *= resize_step
                        new_w = max(1, int(img.width * scale))
                        new_h = max(1, int(img.height * scale))
                        scaled = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                        candidate_data, candidate_quality, candidate_reached = find_best_with_quality_search(
                            scaled,
                            lambda im, q: encode_jpeg(im, q, jpeg_subsampling, icc_profile, exif_bytes),
                            max_bytes,
                            min_quality,
                            max_quality,
                        )
                        if len(candidate_data) < len(new_data):
                            new_data = candidate_data
                            quality = candidate_quality
                            reached_target = candidate_reached
                            note = f"q={quality}, resized={new_w}x{new_h}"
                        if candidate_reached:
                            break

            elif ext in WEBP_EXTS:
                new_data, quality, reached_target = find_best_with_quality_search(
                    img,
                    lambda im, q: encode_webp(im, q, icc_profile, exif_bytes),
                    max_bytes,
                    min_quality,
                    max_quality,
                )
                note = f"q={quality}"
                if not reached_target:
                    note += " (best effort)"

                if not reached_target and allow_resize:
                    scaled = img
                    scale = 1.0
                    while scale > min_scale:
                        scale *= resize_step
                        new_w = max(1, int(img.width * scale))
                        new_h = max(1, int(img.height * scale))
                        scaled = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                        candidate_data, candidate_quality, candidate_reached = find_best_with_quality_search(
                            scaled,
                            lambda im, q: encode_webp(im, q, icc_profile, exif_bytes),
                            max_bytes,
                            min_quality,
                            max_quality,
                        )
                        if len(candidate_data) < len(new_data):
                            new_data = candidate_data
                            quality = candidate_quality
                            reached_target = candidate_reached
                            note = f"q={quality}, resized={new_w}x{new_h}"
                        if candidate_reached:
                            break

            elif ext in PNG_EXTS:
                new_data = encode_png_lossless(img, icc_profile)
                note = "lossless"

            else:
                return Result(path, "skipped-unsupported", old_size, old_size)

    except (UnidentifiedImageError, OSError):
        return Result(path, "skipped-invalid", old_size, old_size)

    new_size = len(new_data)
    if new_size >= old_size:
        return Result(path, "kept-original", old_size, old_size)

    if not dry_run:
        path.write_bytes(new_data)

    status = "compressed"
    if new_size > max_bytes:
        status = "compressed-over-target"

    return Result(path, status, old_size, new_size, note)


def iter_image_files(root: Path):
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTS:
            yield path


def run_compression(
    root: Path,
    max_kb: int = DEFAULT_MAX_KB,
    min_kb: int = DEFAULT_MIN_KB,
    min_quality: int = 62,
    max_quality: int = 92,
    jpeg_subsampling: int = 1,
    allow_resize: bool = False,
    min_scale: float = 0.80,
    resize_step: float = 0.95,
    dry_run: bool = False,
    log_every: int = 10,
    show_skip_logs: bool = True,
) -> list[Result]:
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Root folder not found: {root}")

    max_bytes = max_kb * 1024
    min_bytes = min_kb * 1024

    results = []
    for index, image_path in enumerate(iter_image_files(root), start=1):
        result = process_image(
            image_path,
            max_bytes,
            min_bytes,
            min_quality,
            max_quality,
            jpeg_subsampling,
            allow_resize,
            min_scale,
            resize_step,
            dry_run,
        )
        results.append(result)

        if result.status.startswith("skipped") and show_skip_logs:
            reason = result.status.replace("skipped-", "")
            print(f"Skipped ({reason}): {result.path}")
        elif result.status == "kept-original" and show_skip_logs:
            print(f"Skipped (no gain): {result.path}")

        if log_every > 0 and index % log_every == 0:
            print(f"Processed {index} images...")

    compressed = [r for r in results if r.status in {"compressed", "compressed-over-target"}]
    skipped_small = [r for r in results if r.status == "skipped-small"]
    kept_original = [r for r in results if r.status == "kept-original"]
    unsupported = [r for r in results if r.status.startswith("skipped-") and r.status != "skipped-small"]

    total_old = sum(r.old_bytes for r in compressed)
    total_new = sum(r.new_bytes for r in compressed)
    saved = total_old - total_new

    mode = "DRY RUN" if dry_run else "WRITE MODE"
    print(f"\n{mode}")
    print(f"Scanned: {len(results)} images")
    print(f"Compressed: {len(compressed)}")
    print(f"Skipped small (<{min_kb}KB): {len(skipped_small)}")
    print(f"Kept original (no gain): {len(kept_original)}")
    print(f"Skipped invalid/unsupported: {len(unsupported)}")
    print(f"Savings: {human_kb(saved)} ({saved / (1024 * 1024):.2f}MB)")

    offenders = [r for r in compressed if r.new_bytes > max_bytes]
    if offenders:
        print("\nStill over target after compression:")
        for item in offenders[:20]:
            print(
                f"- {item.path}: {human_kb(item.old_bytes)} -> {human_kb(item.new_bytes)} {item.note}".rstrip()
            )

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Compress images to a target max size while keeping resolution unchanged."
    )
    parser.add_argument("--root", default=DEFAULT_ROOT, help="Root directory (default: imgs)")
    parser.add_argument("--max-kb", type=int, default=DEFAULT_MAX_KB, help="Max size in KB")
    parser.add_argument(
        "--min-kb",
        type=int,
        default=DEFAULT_MIN_KB,
        help="Skip files smaller than this size in KB",
    )
    parser.add_argument("--min-quality", type=int, default=62)
    parser.add_argument("--max-quality", type=int, default=92)
    parser.add_argument(
        "--jpeg-subsampling",
        type=int,
        choices=(0, 1, 2),
        default=1,
        help="JPEG chroma subsampling: 0=best color, 1=balanced, 2=smallest",
    )
    parser.add_argument(
        "--allow-resize",
        action="store_true",
        help="Allow gentle downscaling for files that cannot hit target by quality alone",
    )
    parser.add_argument("--min-scale", type=float, default=0.80)
    parser.add_argument("--resize-step", type=float, default=0.95)
    parser.add_argument(
        "--log-every",
        type=int,
        default=10,
        help="Print progress every N images (0 disables periodic progress)",
    )
    parser.add_argument(
        "--quiet-skips",
        action="store_true",
        help="Do not print per-file skip messages",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview only, do not write files")
    args = parser.parse_args()

    root = Path(args.root)
    run_compression(
        root=root,
        max_kb=args.max_kb,
        min_kb=args.min_kb,
        min_quality=args.min_quality,
        max_quality=args.max_quality,
        jpeg_subsampling=args.jpeg_subsampling,
        allow_resize=args.allow_resize,
        min_scale=args.min_scale,
        resize_step=args.resize_step,
        dry_run=args.dry_run,
        log_every=args.log_every,
        show_skip_logs=not args.quiet_skips,
    )


if __name__ == "__main__":
    main()
