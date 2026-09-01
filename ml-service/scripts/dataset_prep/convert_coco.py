"""
convert_coco.py
------------------
Converts Label Studio COCO JSON export (data/annotations/coco.json) into the
project's standardized AnnotationDataset format (data/annotations/dataset.json)
validated by app/dataset/annotation_schema.py.
"""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.dataset.annotation_schema import AnnotationDataset, ImageAnnotation, AnnotationRegion, BoundingBox
from app.dataset.annotation_loader import load_annotation_dataset, dataset_summary


def convert_coco(coco_path: str = "data/annotations/coco.json", output_path: str = "data/annotations/dataset.json"):
    coco_file = Path(coco_path)
    if not coco_file.exists():
        raise FileNotFoundError(f"COCO file not found at {coco_path}")

    with open(coco_file, "r", encoding="utf-8") as f:
        coco_data = json.load(f)

    # Map category_id -> category_name
    cat_map = {cat["id"]: cat["name"] for cat in coco_data.get("categories", [])}

    # Group annotations by image_id
    ann_by_image = {}
    for ann in coco_data.get("annotations", []):
        img_id = ann["image_id"]
        ann_by_image.setdefault(img_id, []).append(ann)

    images_list = []
    for img_info in coco_data.get("images", []):
        img_id = img_info["id"]
        # Extract plain filename from path (e.g. "upload\\4\\xyz.jpg" -> "xyz.jpg")
        raw_filename = img_info["file_name"]
        filename = Path(raw_filename).name

        width = float(img_info["width"])
        height = float(img_info["height"])

        regions = []
        for ann in ann_by_image.get(img_id, []):
            cat_id = ann["category_id"]
            cat_name = cat_map.get(cat_id)
            if not cat_name:
                continue

            x, y, w, h = ann["bbox"]
            # Ensure coordinates are within valid bounds
            x = max(0.0, float(x))
            y = max(0.0, float(y))
            # Clamp width and height so bbox does not exceed image dimension
            if x + w > width:
                w = max(1.0, width - x)
            if y + h > height:
                h = max(1.0, height - y)

            if w <= 0 or h <= 0:
                continue

            region = AnnotationRegion(
                category=cat_name,
                bbox=BoundingBox(
                    x=round(x, 2),
                    y=round(y, 2),
                    width=round(w, 2),
                    height=round(h, 2)
                ),
                transcribed_text=ann.get("text") or None
            )
            regions.append(region)

        image_ann = ImageAnnotation(
            image_filename=filename,
            image_width=int(width),
            image_height=int(height),
            regions=regions,
            split=None
        )
        images_list.append(image_ann)

    dataset = AnnotationDataset(
        dataset_version="v1.0",
        images=images_list
    )

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(dataset.model_dump_json(indent=2))

    print(f"Successfully converted {len(images_list)} images to {output_path}")
    
    # Validate with loader
    loaded = load_annotation_dataset(output_path)
    summary = dataset_summary(loaded)
    print("Dataset Summary:")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    convert_coco()
