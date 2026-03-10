import argparse
from datetime import datetime
from pathlib import Path

from compress_imgs import SUPPORTED_EXTS, process_image


STAGING_DIR = Path("0_INSERT_HERE")
DEST_BASE = Path("imgs")


def ensure_staging_folder() -> Path:
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    return STAGING_DIR


def parse_date_input(raw: str) -> tuple[str, str, str]:
    dt = datetime.strptime(raw.strip(), "%d/%m/%Y")
    return dt.strftime("%Y"), dt.strftime("%m"), dt.strftime("%d")


def unique_destination_path(dest_dir: Path, filename: str) -> Path:
    candidate = dest_dir / filename
    if not candidate.exists():
        return candidate

    stem = Path(filename).stem
    suffix = Path(filename).suffix
    counter = 1
    while True:
        next_candidate = dest_dir / f"{stem}_{counter}{suffix}"
        if not next_candidate.exists():
            return next_candidate
        counter += 1


def iter_staging_images(staging: Path):
    for path in sorted(staging.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTS:
            yield path


def iter_staging_non_images(staging: Path):
    for path in sorted(staging.rglob("*")):
        if path.is_file() and path.suffix.lower() not in SUPPORTED_EXTS:
            yield path


def run_import(
    date_str: str,
    max_kb: int,
    min_kb: int,
    min_quality: int,
    max_quality: int,
    jpeg_subsampling: int,
    allow_resize: bool,
    min_scale: float,
    resize_step: float,
    dry_run: bool,
) -> None:
    staging = ensure_staging_folder()
    image_paths = list(iter_staging_images(staging))
    non_image_paths = list(iter_staging_non_images(staging))

    for non_image in non_image_paths:
        print(f"Skipped (non-image): {non_image}")

    if not image_paths:
        print("No images found in 0_INSERT_HERE.")
        print("Put files in 0_INSERT_HERE and run again.")
        return

    year, month, day = parse_date_input(date_str)
    destination_dir = DEST_BASE / year / month / day
    destination_dir.mkdir(parents=True, exist_ok=True)

    print(f"Staging folder: {staging}")
    print(f"Destination: {destination_dir}")

    max_bytes = max_kb * 1024
    min_bytes = min_kb * 1024

    moved_count = 0
    compressed_count = 0
    skipped_small = 0
    skipped_other = 0

    for index, source_path in enumerate(image_paths, start=1):
        destination_path = unique_destination_path(destination_dir, source_path.name)

        if not dry_run:
            source_path.rename(destination_path)

        moved_count += 1

        result = process_image(
            destination_path if not dry_run else source_path,
            max_bytes=max_bytes,
            min_bytes=min_bytes,
            min_quality=min_quality,
            max_quality=max_quality,
            jpeg_subsampling=jpeg_subsampling,
            allow_resize=allow_resize,
            min_scale=min_scale,
            resize_step=resize_step,
            dry_run=dry_run,
        )

        if result.status in {"compressed", "compressed-over-target"}:
            compressed_count += 1
        elif result.status == "skipped-small":
            skipped_small += 1
            print(f"Skipped (small): {source_path.name}")
        else:
            skipped_other += 1
            print(f"Skipped ({result.status}): {source_path.name}")

        if index % 10 == 0:
            print(f"Processed {index} images...")

    print("\nIMPORT SUMMARY")
    print(f"Moved/sorted: {moved_count}")
    print(f"Compressed: {compressed_count}")
    print(f"Skipped small (<{min_kb}KB): {skipped_small}")
    print(f"Skipped other: {skipped_other}")
    if dry_run:
        print("Dry run used: files were not moved or modified.")



def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create 0_INSERT_HERE workflow: prompt for date, sort images into imgs/YYYY/MM/DD, compress only large files."
    )
    parser.add_argument("--date", help="Date in DD/MM/YYYY. If omitted, script prompts interactively.")
    parser.add_argument("--max-kb", type=int, default=500)
    parser.add_argument("--min-kb", type=int, default=200)
    parser.add_argument("--min-quality", type=int, default=62)
    parser.add_argument("--max-quality", type=int, default=92)
    parser.add_argument("--jpeg-subsampling", type=int, choices=(0, 1, 2), default=1)
    parser.add_argument("--allow-resize", action="store_true")
    parser.add_argument("--min-scale", type=float, default=0.80)
    parser.add_argument("--resize-step", type=float, default=0.95)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    ensure_staging_folder()

    if args.date:
        date_str = args.date
    else:
        date_str = input("Enter date (DD/MM/YYYY): ").strip()

    try:
        datetime.strptime(date_str, "%d/%m/%Y")
    except ValueError:
        raise SystemExit("Invalid date format. Use DD/MM/YYYY.")

    run_import(
        date_str=date_str,
        max_kb=args.max_kb,
        min_kb=args.min_kb,
        min_quality=args.min_quality,
        max_quality=args.max_quality,
        jpeg_subsampling=args.jpeg_subsampling,
        allow_resize=args.allow_resize,
        min_scale=args.min_scale,
        resize_step=args.resize_step,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
