"""
ocr_engine.py
-------------
Runs OCR on cropped text regions produced by Phase 4.

BACKENDS:
  1. "easyocr" (default for real execution) — pretrained CRNN/ResNet recognizer.
  2. "stub"    — deterministic non-ML fallback for testing.
  3. "auto"    — tries EasyOCR, falls back to stub.

Usage:
    from app.ocr.ocr_engine import run_ocr
    result = run_ocr(crop)                 # crop: np.ndarray (BGR or grayscale)
    # result: {"text": "...", "confidence": 0.0-1.0}
"""

import logging
from typing import Dict, Union, Any
import numpy as np
from app.ocr.postprocess_text import postprocess

logger = logging.getLogger(__name__)

_easyocr_reader = None
_easyocr_available = None


def _try_load_easyocr() -> bool:
    global _easyocr_reader, _easyocr_available
    if _easyocr_available is not None:
        return _easyocr_available

    try:
        import easyocr
        _easyocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        _easyocr_available = True
        logger.info("EasyOCR reader loaded successfully.")
    except Exception as e:
        logger.warning(f"EasyOCR not available ({e}); falling back to stub OCR.")
        _easyocr_available = False

    return _easyocr_available


def _run_with_easyocr(region_crop: np.ndarray) -> Dict[str, Any]:
    results = _easyocr_reader.readtext(region_crop)
    if not results:
        return {"text": "", "confidence": 0.0}

    results_sorted = sorted(results, key=lambda r: r[0][0][0])
    raw_text = " ".join(r[1] for r in results_sorted).strip()
    avg_confidence = sum(r[2] for r in results_sorted) / len(results_sorted)
    
    clean_text = postprocess(raw_text)

    return {"text": clean_text, "confidence": round(float(avg_confidence), 4)}


def _run_with_stub(region_crop: np.ndarray) -> Dict[str, Any]:
    if region_crop.size == 0:
        return {"text": "", "confidence": 0.0}

    import cv2
    gray = cv2.cvtColor(region_crop, cv2.COLOR_BGR2GRAY) if region_crop.ndim == 3 else region_crop
    ink_ratio = float((gray < 128).mean())

    if ink_ratio < 0.01:
        return {"text": "", "confidence": 0.0}

    return {"text": "[STUB_OCR_TEXT]", "confidence": 0.5}


def run_ocr(region_crop: Union[np.ndarray, Dict[str, Any]], backend: str = "auto") -> Dict[str, Any]:
    """
    Recognizes text in a single cropped image region or region dict.
    """
    meta = {}
    if isinstance(region_crop, dict):
        meta = {k: v for k, v in region_crop.items() if k != "crop"}
        crop_array = region_crop.get("crop")
    else:
        crop_array = region_crop

    if crop_array is None or not isinstance(crop_array, np.ndarray) or crop_array.size == 0:
        raise ValueError("run_ocr received an empty image crop")

    if backend == "stub":
        res = _run_with_stub(crop_array)
    elif backend == "easyocr":
        if not _try_load_easyocr():
            raise RuntimeError(
                "EasyOCR backend was explicitly requested but is not available. "
                "Install with: pip install easyocr"
            )
        res = _run_with_easyocr(crop_array)
    else:  # backend == "auto"
        if _try_load_easyocr():
            try:
                res = _run_with_easyocr(crop_array)
            except Exception as e:
                logger.warning(f"EasyOCR recognition failed at runtime ({e}); falling back to stub.")
                res = _run_with_stub(crop_array)
        else:
            res = _run_with_stub(crop_array)

    return {**meta, **res}
