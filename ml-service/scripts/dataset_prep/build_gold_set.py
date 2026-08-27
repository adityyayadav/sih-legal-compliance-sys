"""
build_gold_set.py
-------------------
The "gold test set" (data/gold_test_set/) is a small (30-50 image) subset that
a HUMAN manually double-checks label-by-label. It is NEVER trained on and is
used only in Phase 10 to measure real-world accuracy honestly.

This script does the mechanical part (randomly sampling candidates from the
test split so you don't hand-pick only "easy" images, which would make your
Phase 10 numbers look better than reality). The verification itself is a
manual task — see the printed checklist at the end.

Usage:
    python scripts/dataset_prep/build_gold_set.py --n 40 --seed 7
"""

import argparse
import json
import random
import shutil
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.dataset.annotation_loader import load_annotation_dataset


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-annotations", default="data/processed/test/annotations.json")
    parser.add_argument("--test-images-dir", default="data/processed/test")
    parser.add_argument("--output-dir", default="data/gold_test_set")
    parser.add_argument("--n", type=int, default=40)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    dataset = load_annotation_dataset(args.test_annotations)
    all_images = dataset.images
    if len(all_images) < args.n:
        print(f"WARNING: only {len(all_images)} images in test split, requested {args.n}. "
              f"Using all {len(all_images)}.")
        sample = all_images
    else:
        rng = random.Random(args.seed)
        sample = rng.sample(all_images, args.n)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    images_dir = Path(args.test_images_dir)

    copied = 0
    for img in sample:
        src = images_dir / img.image_filename
        if src.exists():
            shutil.copy2(src, output_dir / img.image_filename)
            copied += 1

    gold_manifest = {
        "dataset_version": dataset.dataset_version,
        "images": [
            {**json.loads(img.model_dump_json()), "split": "gold"} for img in sample
        ],
    }
    (output_dir / "annotations.json").write_text(json.dumps(gold_manifest, indent=2), encoding="utf-8")

    print(f"Gold test set built: {copied}/{len(sample)} images copied to {output_dir}/\n")
    print("MANUAL STEP — do this before trusting any Phase 10 metric against this set:")
    print("  1. Open every image in this folder side-by-side with its annotation.json entry.")
    print("  2. Manually re-verify: is every mandatory field correctly labeled? Is the")
    print("     transcribed_text exactly correct (fix any OCR-assisted pre-fill errors)?")
    print("  3. Manually determine and record the TRUE compliant/non-compliant status")
    print("     for each product yourself, by reading the label like an inspector would.")
    print("  4. Only after this manual pass is this folder actually 'gold' — until then")
    print("     treat it as a draft.")


if __name__ == "__main__":
    main()
