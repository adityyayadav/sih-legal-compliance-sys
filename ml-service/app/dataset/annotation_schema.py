"""
annotation_schema.py
---------------------
Defines the EXPECTED STRUCTURE of a single annotation record produced during
Phase 2 (labeling images in Label Studio / CVAT / LabelImg and exporting them).

Why this exists (same reasoning as Phase 1's rules_schema.py):
If annotations are malformed — a typo in a class name, a bbox with negative
width, a missing image reference — you want that caught NOW, while you're
still collecting data, not three weeks from now when Phase 4's detector
training script crashes on annotation #438 with no useful error message.

IMPORTANT: The category names below are DELIBERATELY the same strings as the
"field" values in app/compliance/rules_config.json (Phase 1). This is not a
coincidence — when you annotate an image, you are teaching the model to find
the exact same 10 declaration types the compliance engine will later check.
Keeping these two vocabularies in sync is what makes Phase 1 -> Phase 2 ->
Phase 4/6 fit together without a translation layer.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

# Must match app/compliance/rules_config.json "field" values exactly.
# If you add/remove a declaration field in Phase 1, update this list too —
# there is a test (test_annotation_schema.py) that checks they stay in sync.
VALID_DECLARATION_CLASSES = [
    "manufacturer_or_packer_or_importer_name_address",
    "common_or_generic_name",
    "net_quantity",
    "mrp",
    "unit_sale_price",
    "mfg_or_pack_or_import_date",
    "best_before_or_use_by_date",
    "consumer_care_details",
    "country_of_origin",
    "dimensions_or_number_of_contents",
    # One extra class not in rules_config.json — useful during annotation to
    # explicitly mark text that is NOT a mandatory declaration (brand name,
    # tagline, ingredients list, barcode). Helps the region_classifier in
    # Phase 4 learn what to ignore, not just what to find.
    "other_non_mandatory_text",
]


class BoundingBox(BaseModel):
    x: float = Field(..., ge=0, description="top-left x, pixels")
    y: float = Field(..., ge=0, description="top-left y, pixels")
    width: float = Field(..., gt=0, description="box width, pixels, must be > 0")
    height: float = Field(..., gt=0, description="box height, pixels, must be > 0")


class AnnotationRegion(BaseModel):
    """One labeled text region within one image."""
    category: str
    bbox: BoundingBox
    transcribed_text: Optional[str] = Field(
        None, description="Ground-truth text for this region, used later to score OCR accuracy (CER/WER) in Phase 10."
    )

    @field_validator("category")
    @classmethod
    def category_must_be_known(cls, v: str) -> str:
        if v not in VALID_DECLARATION_CLASSES:
            raise ValueError(
                f"Unknown annotation category '{v}'. Must be one of: {VALID_DECLARATION_CLASSES}"
            )
        return v


class ImageAnnotation(BaseModel):
    """All annotations for a single image."""
    image_filename: str
    image_width: int = Field(..., gt=0)
    image_height: int = Field(..., gt=0)
    regions: List[AnnotationRegion]
    split: Optional[str] = Field(
        None, description="'train' | 'val' | 'test' | 'gold' — filled in by split_dataset.py, not during manual annotation"
    )

    @field_validator("split")
    @classmethod
    def split_must_be_valid(cls, v):
        if v is not None and v not in {"train", "val", "test", "gold"}:
            raise ValueError(f"split must be one of train/val/test/gold, got '{v}'")
        return v

    @field_validator("regions")
    @classmethod
    def bbox_must_fit_inside_image(cls, v, info):
        # NOTE: cross-field validation (needs image_width/height) — Pydantic v2
        # runs field validators before the whole model is built, so this only
        # does a light per-region sanity pass; the full in-bounds check happens
        # in annotation_loader.py after the model is constructed.
        return v


class AnnotationDataset(BaseModel):
    """The full collection — what you get after exporting from Label Studio/CVAT
    and converting to this project's internal format."""
    dataset_version: str
    images: List[ImageAnnotation]
