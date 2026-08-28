"""
train_detector.py
--------------------
OPTIONAL — per the project plan, this is "only if time permits." The
baseline detector in app/detection/text_detector.py (PaddleOCR out-of-box,
or the offline contour fallback) does NOT require this script to work.

What this script is for:
If PaddleOCR's generic pretrained detector under-performs on your specific
packaging photos (e.g. struggles with embossed/foil/curved-bottle text),
this is where you'd fine-tune a layout-aware detection model (LayoutLMv3 is
the model suggested in the project plan) against your own Phase 2 annotated
dataset (data/processed/train/, data/processed/val/).

This is intentionally left as a documented SKELETON, not a finished
training pipeline — actually training a layout model is a multi-day task on
its own (GPU access, hyperparameter tuning, correct label-alignment code for
LayoutLMv3's tokenizer+bbox format) and is explicitly the lowest-priority
item in Phase 4. Fill this in only after Phases 5-9 give you a working
end-to-end pipeline, if you have days left over.

Expected usage once implemented:
    python training/train_detector.py \\
        --train-dir data/processed/train \\
        --val-dir data/processed/val \\
        --output-dir app/models/detector \\
        --config training/configs/detector_config.yaml
"""

import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train-dir", default="data/processed/train")
    parser.add_argument("--val-dir", default="data/processed/val")
    parser.add_argument("--output-dir", default="app/models/detector")
    parser.add_argument("--config", default="training/configs/detector_config.yaml")
    parser.add_argument("--epochs", type=int, default=10)
    args = parser.parse_args()

    print("=" * 70)
    print("train_detector.py is a SKELETON — fine-tuning is not yet implemented.")
    print("=" * 70)
    print(f"""
This script is a placeholder for optional detector fine-tuning (Phase 4,
step 3 — 'only if time permits'). The baseline PaddleOCR/contour detector
in app/detection/text_detector.py works without this.

To actually implement fine-tuning here, you would:

  1. Load annotated data from {args.train_dir} / {args.val_dir}
     (these already exist and are validated — see Phase 2's
     app/dataset/annotation_loader.py to read them).

  2. Convert each ImageAnnotation's regions (bbox + category) into the
     input format LayoutLMv3 (or your chosen detector) expects — typically
     normalized bboxes + word tokens + labels per HuggingFace's
     `transformers` LayoutLMv3 processor conventions.

  3. Fine-tune using HuggingFace `Trainer` (or a custom training loop) for
     {args.epochs} epochs, validating against {args.val_dir}.

  4. Save the resulting weights to {args.output_dir}/ — this path is what
     text_detector.py should be updated to load from, behind a new
     backend="finetuned" option (following the same pattern as the
     existing "paddleocr" / "contour" backends).

  5. Re-run evaluation/evaluate_detection.py (Phase 10) to confirm the
     fine-tuned model actually beats the baseline before switching
     production traffic to it — don't assume fine-tuning helped without
     measuring it against the gold test set.

Not implemented in this hackathon timeline unless Phases 5-9 are already
complete and stable.
""")
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    print(f"(Created empty output directory at {args.output_dir}/ for when this is implemented.)")


if __name__ == "__main__":
    main()
