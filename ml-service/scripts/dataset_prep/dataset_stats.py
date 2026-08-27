"""
dataset_stats.py
------------------
Run this any time to see the current state of your dataset at a glance —
useful to check before every team standup during Phase 2's "ongoing collection"
weeks, and as a final sanity check before moving to Phase 4.

Usage:
    python scripts/dataset_prep/dataset_stats.py
"""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.dataset.annotation_loader import load_annotation_dataset, dataset_summary, AnnotationDatasetError


def report_for(label: str, path: str):
    print(f"\n=== {label} ({path}) ===")
    try:
        ds = load_annotation_dataset(path)
        summary = dataset_summary(ds)
        print(f"  Images: {summary['total_images']}   Labeled regions: {summary['total_regions']}")
        print("  Regions per class:")
        for cls, count in sorted(summary["regions_per_class"].items(), key=lambda x: -x[1]):
            flag = "  <-- LOW, consider collecting more" if count < 15 else ""
            print(f"    {cls:55s} {count:4d}{flag}")
        if summary["classes_with_zero_examples"]:
            print(f"  ZERO examples for: {summary['classes_with_zero_examples']}")
    except AnnotationDatasetError as e:
        print(f"  Not available / invalid: {e}")


if __name__ == "__main__":
    report_for("Full annotated dataset", "data/annotations/dataset.json")
    report_for("Train split", "data/processed/train/annotations.json")
    report_for("Val split", "data/processed/val/annotations.json")
    report_for("Test split", "data/processed/test/annotations.json")
    report_for("Gold test set", "data/gold_test_set/annotations.json")
