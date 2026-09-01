"""
evaluate_ocr.py
---------------
Phase 10 — Evaluates OCR recognition performance:
- Character Error Rate (CER)
- Word Error Rate (WER)
- Recognition Accuracy
"""

import argparse
import json
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.dataset.annotation_loader import load_annotation_dataset
from app.ocr.ocr_engine import run_ocr
from app.utils.image_io import load_image_sync


def levenshtein_distance(seq1, seq2):
    size_x = len(seq1) + 1
    size_y = len(seq2) + 1
    matrix = np.zeros((size_x, size_y), dtype=int)
    for x in range(size_x):
        matrix[x, 0] = x
    for y in range(size_y):
        matrix[0, y] = y

    for x in range(1, size_x):
        for y in range(1, size_y):
            if seq1[x - 1] == seq2[y - 1]:
                matrix[x, y] = matrix[x - 1, y - 1]
            else:
                matrix[x, y] = min(
                    matrix[x - 1, y] + 1,
                    matrix[x - 1, y - 1] + 1,
                    matrix[x, y - 1] + 1
                )
    return matrix[size_x - 1, size_y - 1]


def evaluate_ocr(annotations_path: str, images_dir: str):
    dataset = load_annotation_dataset(annotations_path)
    total_char_dist = 0
    total_chars = 0
    total_word_dist = 0
    total_words = 0
    evaluated_crops = 0

    print(f"\nEvaluating OCR on {len(dataset.images)} images from {annotations_path}...")

    for img_ann in dataset.images:
        img_path = Path(images_dir) / img_ann.image_filename
        if not img_path.exists():
            continue

        img_np = load_image_sync(img_path)
        ih, iw = img_np.shape[:2]

        for reg in img_ann.regions:
            gt_text = reg.transcribed_text
            # If no transcribed text in annotation, test OCR execution on crop
            x, y, w, h = int(reg.bbox.x), int(reg.bbox.y), int(reg.bbox.width), int(reg.bbox.height)
            crop = img_np[max(0, y):min(ih, y + h), max(0, x):min(iw, x + w)]
            if crop.size == 0:
                continue

            pred_res = run_ocr(crop)
            pred_text = pred_res.get("text", "")
            evaluated_crops += 1

            if gt_text:
                ref_chars = len(gt_text)
                if ref_chars > 0:
                    char_dist = levenshtein_distance(gt_text.lower(), pred_text.lower())
                    total_char_dist += char_dist
                    total_chars += ref_chars

                ref_words = gt_text.strip().lower().split()
                pred_words = pred_text.strip().lower().split()
                if ref_words:
                    word_dist = levenshtein_distance(ref_words, pred_words)
                    total_word_dist += word_dist
                    total_words += len(ref_words)

    cer = total_char_dist / total_chars if total_chars > 0 else 0.0
    wer = total_word_dist / total_words if total_words > 0 else 0.0

    print("=" * 60)
    print("OCR EVALUATION RESULTS:")
    print(f"  Total Evaluated Crops: {evaluated_crops}")
    print(f"  Character Error Rate (CER): {cer:.2%}")
    print(f"  Word Error Rate (WER):      {wer:.2%}")
    print(f"  Recognized Character Count: {total_chars}")
    print("=" * 60)

    return {"evaluated_crops": evaluated_crops, "cer": cer, "wer": wer}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotations", default="data/gold_test_set/annotations.json")
    parser.add_argument("--images-dir", default="data/gold_test_set")
    args = parser.parse_args()

    evaluate_ocr(args.annotations, args.images_dir)
