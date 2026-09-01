"""
evaluate_e2e.py
---------------
Phase 10 — Full end-to-end pipeline benchmark on test/gold set:
- Runs: Preprocess -> Detect -> OCR -> Extract -> Font Analysis -> Compliance -> Report
- Measures per-stage latency and total inference time (target < ~5 seconds)
- Evaluates extracted declarations and detected violations
- Generates summary report
"""

import argparse
import json
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.dataset.annotation_loader import load_annotation_dataset
from app.utils.image_io import load_image_sync
from app.preprocessing.pipeline import preprocess
from app.detection.text_detector import detect_text_regions
from app.ocr.ocr_engine import run_ocr
from app.extraction.field_extractor import extract_fields
from app.font_analysis.font_measure import analyze_fonts
from app.compliance.rule_engine import check_compliance
from app.compliance.report_builder import build_report


def load_rules(path: str = "app/compliance/rules_config.json") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_e2e(annotations_path: str, images_dir: str, rules_path: str = "app/compliance/rules_config.json"):
    dataset = load_annotation_dataset(annotations_path)
    rules_config = load_rules(rules_path)

    total_images = len(dataset.images)
    latencies = []
    reports = []
    compliant_count = 0
    non_compliant_count = 0

    print(f"\nRunning End-to-End Evaluation on {total_images} images from {annotations_path}...")
    print("=" * 70)

    for idx, img_ann in enumerate(dataset.images, 1):
        img_path = Path(images_dir) / img_ann.image_filename
        if not img_path.exists():
            print(f"[{idx}/{total_images}] Skipping missing image {img_ann.image_filename}")
            continue

        start_t = time.perf_counter()

        # 1. Load & Preprocess
        raw_img = load_image_sync(img_path)
        processed = preprocess(raw_img)

        # 2. Text Region Detection
        regions = detect_text_regions(processed)

        # 3. OCR Recognition
        ocr_results = [run_ocr(r) for r in regions]

        # 4. Field Extraction
        declarations = extract_fields(ocr_results, rules_config)

        # 5. Font Analysis
        font_analysis = analyze_fonts([regions], rules_config)

        # 6. Compliance Evaluation
        violations = check_compliance(declarations, font_analysis, rules_config)

        # 7. Final Report Construction
        report = build_report(
            product_id=f"e2e-eval-{idx}",
            declarations=declarations,
            font_analysis=font_analysis,
            violations=violations
        )

        elapsed = time.perf_counter() - start_t
        latencies.append(elapsed)
        reports.append(report)

        status = report.get("overall_compliance_status")
        if status == "COMPLIANT":
            compliant_count += 1
        else:
            non_compliant_count += 1

        fields_found = [k for k, v in declarations.items() if v.get("present")]
        print(f"[{idx}/{total_images}] {img_ann.image_filename} | Time: {elapsed:.2f}s | Status: {status} | Fields: {len(fields_found)} found | Violations: {len(violations)}")

    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    print("=" * 70)
    print("END-TO-END BENCHMARK SUMMARY:")
    print(f"  Processed Images:        {len(latencies)} / {total_images}")
    print(f"  Average Inference Time:  {avg_latency:.2f}s (Target: < 5.0s)")
    print(f"  Compliant Labels:        {compliant_count}")
    print(f"  Non-Compliant Labels:    {non_compliant_count}")
    print("=" * 70)

    return {
        "processed": len(latencies),
        "avg_latency_seconds": round(avg_latency, 2),
        "compliant_count": compliant_count,
        "non_compliant_count": non_compliant_count,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotations", default="data/gold_test_set/annotations.json")
    parser.add_argument("--images-dir", default="data/gold_test_set")
    args = parser.parse_args()

    evaluate_e2e(args.annotations, args.images_dir)
