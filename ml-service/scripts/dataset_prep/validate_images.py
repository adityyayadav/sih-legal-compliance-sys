"""
validate_images.py
--------------------
Run this FIRST, every time you add a new batch of photos to data/raw_images/,
before anyone spends time annotating them in Label Studio/CVAT.

Catches the boring-but-costly problems:
  - corrupt/unreadable files
  - resolution too low for text to be legible at all
  - duplicate images (same photo saved twice, wastes annotation effort)
  - wrong/unsupported file format

Usage:
    python scripts/dataset_prep/validate_images.py data/raw_images/
"""

import sys
import hashlib
from pathlib import Path

from PIL import Image

MIN_WIDTH_PX = 600
MIN_HEIGHT_PX = 600
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def file_hash(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def validate_folder(folder: str) -> dict:
    folder_path = Path(folder)
    if not folder_path.exists():
        raise FileNotFoundError(f"Folder not found: {folder}")

    all_files = [p for p in folder_path.iterdir() if p.is_file()]

    report = {
        "total_files_scanned": len(all_files),
        "valid": [],
        "unsupported_format": [],
        "corrupt_or_unreadable": [],
        "too_low_resolution": [],
        "duplicates": [],
    }

    seen_hashes = {}

    for path in sorted(all_files):
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            report["unsupported_format"].append(path.name)
            continue

        try:
            with Image.open(path) as img:
                img.verify()
            # re-open after verify() since verify() invalidates the file handle
            with Image.open(path) as img:
                width, height = img.size
        except Exception as e:
            report["corrupt_or_unreadable"].append(f"{path.name} ({e})")
            continue

        if width < MIN_WIDTH_PX or height < MIN_HEIGHT_PX:
            report["too_low_resolution"].append(f"{path.name} ({width}x{height})")
            continue

        h = file_hash(path)
        if h in seen_hashes:
            report["duplicates"].append(f"{path.name} (duplicate of {seen_hashes[h]})")
            continue
        seen_hashes[h] = path.name

        report["valid"].append(path.name)

    return report


def print_report(report: dict) -> None:
    print(f"Scanned {report['total_files_scanned']} files")
    print(f"  Valid:                 {len(report['valid'])}")
    print(f"  Unsupported format:    {len(report['unsupported_format'])}")
    print(f"  Corrupt/unreadable:    {len(report['corrupt_or_unreadable'])}")
    print(f"  Too low resolution:    {len(report['too_low_resolution'])} (min {MIN_WIDTH_PX}x{MIN_HEIGHT_PX})")
    print(f"  Duplicates:            {len(report['duplicates'])}")

    for category in ["unsupported_format", "corrupt_or_unreadable", "too_low_resolution", "duplicates"]:
        if report[category]:
            print(f"\n--- {category} ---")
            for item in report[category][:20]:
                print(f"  {item}")
            if len(report[category]) > 20:
                print(f"  ...and {len(report[category]) - 20} more")


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else "data/raw_images"
    report = validate_folder(folder)
    print_report(report)
    if report["corrupt_or_unreadable"]:
        sys.exit(1)  # non-zero exit so this can be wired into a CI/pre-commit check later
