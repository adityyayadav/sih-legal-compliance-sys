"""
evaluate_detection.py
---------------------
Phase 10 — Evaluates text region detection performance (Precision, Recall, F1 @ IoU >= 0.5)
against ground-truth annotations in data/gold_test_set/ or data/processed/test/.
"""

import argparse
import json
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.dataset.annotation_loader import load_annotation_dataset
from app.detection.text_detector import detect_text_regions
from app.utils.image_io import load_image_sync


def compute_iou(boxA, boxB):
    # box format: [x, y, w, h]
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[0] + boxA[2], boxB[0] + boxB[2])
    yB = min(boxA[1] + boxA[3], boxB[1] + boxB[3])

    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = boxA[2] * boxA[3]
    boxBArea = boxB[2] * boxB[3]
    unionArea = float(boxAArea + boxBArea - interArea)
    if unionArea == 0:
        return 0.0
    return interArea / unionArea


def evaluate_detection(annotations_path: str, images_dir: str, iou_threshold: float = 0.5):
    dataset = load_annotation_dataset(annotations_path)
    total_gt = 0
    total_pred = 0
    true_positives = 0

    print(f"\nEvaluating Detection on {len(dataset.images)} images from {annotations_path}...")

    for img_ann in dataset.images:
        img_path = Path(images_dir) / img_ann.image_filename
        if not img_path.exists():
            continue

        img_np = load_image_sync(img_path)
        gt_boxes = [[r.bbox.x, r.bbox.y, r.bbox.width, r.bbox.height] for r in img_ann.regions]
        total_gt += len(gt_boxes)

        detected_regions = detect_text_regions(img_np)
        pred_boxes = [r["bbox"] for r in detected_regions]
        total_pred += len(pred_boxes)

        # Match predicted boxes to ground truth
        matched_gt = set()
        for p_box in pred_boxes:
            for idx, g_box in enumerate(gt_boxes):
                if idx not in matched_gt:
                    iou = compute_iou(p_box, g_box)
                    if iou >= iou_threshold:
                        true_positives += 1
                        matched_gt.add(idx)
                        break

    precision = true_positives / total_pred if total_pred > 0 else 0.0
    recall = true_positives / total_gt if total_gt > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    metrics = {
        "total_images": len(dataset.images),
        "total_ground_truth_boxes": total_gt,
        "total_predicted_boxes": total_pred,
        "true_positives": true_positives,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "iou_threshold": iou_threshold
    }

    print("=" * 60)
    print("DETECTION EVALUATION RESULTS:")
    print(f"  Total Ground Truth:  {total_gt}")
    print(f"  Total Predictions:   {total_pred}")
    print(f"  Precision:           {precision:.2%}")
    print(f"  Recall:              {recall:.2%}")
    print(f"  F1-Score:            {f1:.4f}")
    print("=" * 60)

    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotations", default="data/gold_test_set/annotations.json")
    parser.add_argument("--images-dir", default="data/gold_test_set")
    parser.add_argument("--iou", type=float, default=0.3)
    args = parser.parse_args()

    evaluate_detection(args.annotations, args.images_dir, args.iou)
