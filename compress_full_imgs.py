# Vibecoded:  I do not take credit for this code.

import argparse
from pathlib import Path

from compress_imgs import run_compression


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a full compression pass on imgs/ with album defaults."
    )
    parser.add_argument("--root", default="imgs")
    parser.add_argument("--max-kb", type=int, default=500)
    parser.add_argument("--min-kb", type=int, default=200)
    parser.add_argument("--min-quality", type=int, default=62)
    parser.add_argument("--max-quality", type=int, default=92)
    parser.add_argument("--jpeg-subsampling", type=int, choices=(0, 1, 2), default=1)
    parser.add_argument("--allow-resize", action="store_true")
    parser.add_argument("--min-scale", type=float, default=0.80)
    parser.add_argument("--resize-step", type=float, default=0.95)
    parser.add_argument("--log-every", type=int, default=10)
    parser.add_argument("--quiet-skips", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    run_compression(
        root=Path(args.root),
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
