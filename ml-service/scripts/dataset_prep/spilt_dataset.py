"""
split_dataset.py
------------------
Takes your annotated dataset (data/annotations/dataset.json, validated against
annotation_schema.py) and splits it into train/val/test sets, then copies the
corresponding image files into data/processed/{train,val,test}/ and writes a
per-split annotation JSON alongside them.

Split is randomized but seeded (reproducible) and light-touch stratified: it
tries to keep the ratio of each declaration class roughly even across splits
by sorting images by their "rarest class present" before splitting, so a rare
class (e.g. country_of_origin, likely to appear in relatively few images)
doesn't end up entirely in one split.

Usage:
    python scripts/dataset_prep/split_dataset.py \\
        --annotations data/annotations/dataset.json \\
        --images-dir data/raw_images \\
        --output-dir data/processed \\
        --train 0.70 --val 0.15 --test 0.15 --seed 42
"""

import argparse
import json
import random
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # allow `app.` imports when run standalone

from app.dataset.annotation_loader import load_annotation_dataset
from app.dataset.annotation_schema import AnnotationDataset, ImageAnnotation


def stratified_split(images: list[ImageAnnotation], train_ratio, val_ratio, test_ratio, seed) -> dict:
    assert abs((train_ratio + val_ratio + test_ratio) - 1.0) < 1e-6, "Ratios must sum to 1.0"

    class_freq = Counter()
    for img in images:
        for r in img.regions:
            class_freq[r.category] += 1

    def rarity_key(img: ImageAnnotation):
        cats = {r.category for r in img.regions}
        if not cats:
            return float("inf")
        return min(class_freq[c] for c in cats)

    rng = random.Random(seed)
    sorted_images = sorted(images, key=rarity_key)  # rarest-class images first

    buckets = {"train": [], "val": [], "test": []}
    # Round-robin the rarest-class images across all three buckets first so no
    # split is starved of a rare class, then randomly assign the remainder.
    n = len(sorted_images)
    rare_cutoff = max(1, n // 10)  # roughly the rarest 10% get round-robined
    rare_images = sorted_images[:rare_cutoff]
    remaining = sorted_images[rare_cutoff:]
    rng.shuffle(remaining)

    split_names = ["train", "val", "test"]
    ratios = [train_ratio, val_ratio, test_ratio]
    for i, img in enumerate(rare_images):
        buckets[split_names[i % 3]].append(img)

    n_remaining = len(remaining)
    train_end = int(n_remaining * train_ratio)
    val_end = train_end + int(n_remaining * val_ratio)
    buckets["train"].extend(remaining[:train_end])
    buckets["val"].extend(remaining[train_end:val_end])
    buckets["test"].extend(remaining[val_end:])

    return buckets


def write_split(split_name: str, images: list[ImageAnnotation], images_dir: Path, output_dir: Path, dataset_version: str):
    split_dir = output_dir / split_name
    split_dir.mkdir(parents=True, exist_ok=True)

    copied, missing = 0, []
    for img in images:
        src = images_dir / img.image_filename
        if not src.exists():
            missing.append(img.image_filename)
            continue
        shutil.copy2(src, split_dir / img.image_filename)
        copied += 1

    out_json = {
        "dataset_version": dataset_version,
        "images": [
            {**json.loads(img.model_dump_json()), "split": split_name} for img in images
        ],
    }
    (split_dir / "annotations.json").write_text(json.dumps(out_json, indent=2), encoding="utf-8")

    return copied, missing


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotations", default="data/annotations/dataset.json")
    parser.add_argument("--images-dir", default="data/raw_images")
    parser.add_argument("--output-dir", default="data/processed")
    parser.add_argument("--train", type=float, default=0.70)
    parser.add_argument("--val", type=float, default=0.15)
    parser.add_argument("--test", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    dataset: AnnotationDataset = load_annotation_dataset(args.annotations)
    buckets = stratified_split(dataset.images, args.train, args.val, args.test, args.seed)

    images_dir = Path(args.images_dir)
    output_dir = Path(args.output_dir)

    print(f"Splitting {len(dataset.images)} annotated images "
          f"({args.train:.0%}/{args.val:.0%}/{args.test:.0%}) with seed={args.seed}\n")

    for split_name in ["train", "val", "test"]:
        copied, missing = write_split(split_name, buckets[split_name], images_dir, output_dir, dataset.dataset_version)
        print(f"  {split_name:6s}: {len(buckets[split_name]):4d} images "
              f"({copied} copied, {len(missing)} missing image files)")
        if missing:
            print(f"           missing: {missing[:5]}{'...' if len(missing) > 5 else ''}")

    print(f"\nDone. Output written to {output_dir}/{{train,val,test}}/")


if __name__ == "__main__":
    main()
