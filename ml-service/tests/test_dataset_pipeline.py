"""
test_dataset_pipeline.py
--------------------------
Phase 2 is "done" when these pass. Run with:
    pytest tests/test_dataset_pipeline.py -v

Uses a small synthetic dataset generated on the fly (no dependency on your
real photos), so this test suite runs the same on every machine/CI, fast.
"""

import json
import shutil
from pathlib import Path

import pytest
from PIL import Image

from app.dataset.annotation_schema import AnnotationDataset, VALID_DECLARATION_CLASSES
from app.dataset.annotation_loader import (
    load_annotation_dataset,
    dataset_summary,
    AnnotationDatasetError,
)


@pytest.fixture()
def tmp_dataset(tmp_path):
    """Builds a tiny valid annotation file + matching image on disk."""
    img_dir = tmp_path / "images"
    img_dir.mkdir()
    img = Image.new("RGB", (800, 1000), (255, 255, 255))
    img.save(img_dir / "sample_001.jpg")

    ann = {
        "dataset_version": "test-0.0.1",
        "images": [
            {
                "image_filename": "sample_001.jpg",
                "image_width": 800,
                "image_height": 1000,
                "regions": [
                    {
                        "category": "net_quantity",
                        "bbox": {"x": 10, "y": 10, "width": 100, "height": 30},
                        "transcribed_text": "500 g",
                    },
                    {
                        "category": "mrp",
                        "bbox": {"x": 10, "y": 60, "width": 120, "height": 30},
                        "transcribed_text": "Rs. 120",
                    },
                ],
            }
        ],
    }
    ann_path = tmp_path / "dataset.json"
    ann_path.write_text(json.dumps(ann), encoding="utf-8")
    return ann_path, img_dir


def test_valid_annotation_file_loads(tmp_dataset):
    ann_path, _ = tmp_dataset
    ds = load_annotation_dataset(str(ann_path))
    assert isinstance(ds, AnnotationDataset)
    assert len(ds.images) == 1
    assert len(ds.images[0].regions) == 2


def test_summary_counts_are_correct(tmp_dataset):
    ann_path, _ = tmp_dataset
    ds = load_annotation_dataset(str(ann_path))
    summary = dataset_summary(ds)
    assert summary["total_images"] == 1
    assert summary["total_regions"] == 2
    assert summary["regions_per_class"]["net_quantity"] == 1
    assert summary["regions_per_class"]["mrp"] == 1


def test_unknown_category_is_rejected(tmp_path):
    bad = {
        "dataset_version": "test",
        "images": [{
            "image_filename": "x.jpg", "image_width": 100, "image_height": 100,
            "regions": [{"category": "totally_made_up_field",
                         "bbox": {"x": 0, "y": 0, "width": 10, "height": 10}}]
        }]
    }
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(AnnotationDatasetError):
        load_annotation_dataset(str(p))


def test_out_of_bounds_bbox_is_rejected(tmp_path):
    bad = {
        "dataset_version": "test",
        "images": [{
            "image_filename": "x.jpg", "image_width": 100, "image_height": 100,
            "regions": [{"category": "mrp",
                         "bbox": {"x": 90, "y": 90, "width": 50, "height": 50}}]
        }]
    }
    p = tmp_path / "bad_bbox.json"
    p.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(AnnotationDatasetError):
        load_annotation_dataset(str(p))


def test_negative_or_zero_size_bbox_is_rejected(tmp_path):
    bad = {
        "dataset_version": "test",
        "images": [{
            "image_filename": "x.jpg", "image_width": 100, "image_height": 100,
            "regions": [{"category": "mrp",
                         "bbox": {"x": 0, "y": 0, "width": 0, "height": 10}}]
        }]
    }
    p = tmp_path / "bad_zero.json"
    p.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(AnnotationDatasetError):
        load_annotation_dataset(str(p))


def test_missing_file_raises_clear_error():
    with pytest.raises(AnnotationDatasetError):
        load_annotation_dataset("data/annotations/this_file_does_not_exist.json")


def test_annotation_classes_match_rules_config_fields():
    """
    Keeps Phase 1 (rules_config.json) and Phase 2 (annotation taxonomy) in sync.
    If this fails, someone added/removed a declaration field in one place and
    not the other — fix VALID_DECLARATION_CLASSES or rules_config.json to match.
    """
    from app.compliance.rules_loader import get_rules_config
    rules_fields = {d.field for d in get_rules_config().declarations}
    annotation_fields = set(VALID_DECLARATION_CLASSES) - {"other_non_mandatory_text"}
    assert rules_fields == annotation_fields, (
        f"Mismatch between rules_config.json fields and annotation classes.\n"
        f"In rules_config but not annotations: {rules_fields - annotation_fields}\n"
        f"In annotations but not rules_config: {annotation_fields - rules_fields}"
    )
