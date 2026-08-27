"""
annotation_loader.py
----------------------
The single safe entry point for reading data/annotations/*.json.
Mirrors app/compliance/rules_loader.py from Phase 1 on purpose — same pattern,
same discipline: validate once, fail loudly, cache, expose clean lookup helpers.

Usage:
    from app.dataset.annotation_loader import load_annotation_dataset
    ds = load_annotation_dataset("data/annotations/dataset.json")
"""

import json
from pathlib import Path
from collections import Counter

from pydantic import ValidationError

from app.dataset.annotation_schema import AnnotationDataset, VALID_DECLARATION_CLASSES


class AnnotationDatasetError(Exception):
    """Raised when an annotation file is missing, malformed, or fails validation."""


def load_annotation_dataset(path: str) -> AnnotationDataset:
    p = Path(path)
    if not p.exists():
        raise AnnotationDatasetError(f"Annotation file not found: {p}")

    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise AnnotationDatasetError(f"{p} is not valid JSON: {e}") from e

    try:
        dataset = AnnotationDataset(**raw)
    except ValidationError as e:
        raise AnnotationDatasetError(f"{p} failed schema validation:\n{e}") from e

    _validate_bboxes_in_bounds(dataset, p)
    return dataset


def _validate_bboxes_in_bounds(dataset: AnnotationDataset, source_path: Path) -> None:
    """Every bbox must fit inside its own image's declared width/height —
    a very common annotation-tool export bug (off-by-one crops, wrong image
    size cached) that silently corrupts training data if not caught here."""
    problems = []
    for img in dataset.images:
        for i, region in enumerate(img.regions):
            b = region.bbox
            if b.x + b.width > img.image_width or b.y + b.height > img.image_height:
                problems.append(
                    f"{img.image_filename} region[{i}] ({region.category}) bbox "
                    f"exceeds image bounds ({img.image_width}x{img.image_height})"
                )
    if problems:
        raise AnnotationDatasetError(
            f"{source_path} has {len(problems)} out-of-bounds bounding box(es):\n"
            + "\n".join(problems[:10])
            + ("\n...(more)" if len(problems) > 10 else "")
        )


def dataset_summary(dataset: AnnotationDataset) -> dict:
    """Quick stats — used by dataset_stats.py and worth eyeballing after every
    annotation batch so you catch class imbalance early (e.g. if nobody ever
    labels 'country_of_origin' because most sample products are domestic)."""
    class_counts = Counter()
    split_counts = Counter()
    for img in dataset.images:
        split_counts[img.split or "unassigned"] += 1
        for region in img.regions:
            class_counts[region.category] += 1

    missing_classes = set(VALID_DECLARATION_CLASSES) - set(class_counts.keys())

    return {
        "total_images": len(dataset.images),
        "total_regions": sum(class_counts.values()),
        "regions_per_class": dict(class_counts),
        "images_per_split": dict(split_counts),
        "classes_with_zero_examples": sorted(missing_classes),
    }


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "data/annotations/dataset.json"
    ds = load_annotation_dataset(target)
    summary = dataset_summary(ds)
    print(f"Loaded {target} — dataset_version={ds.dataset_version}")
    print(json.dumps(summary, indent=2))
