  # Legal Metrology Compliance Checker — Final Implementation Plan

Single source of truth. Follow this exactly — no alternate paths left in.

---

## 1. Architecture

```
┌─────────────────────────┐
│ FRONTEND (React) │ <-- local, port 3000
└────────────┬─────────────┘
             │ REST/JSON (JWT)
             ▼
┌─────────────────────────┐
│ SPRING BOOT BACKEND │ <-- Teammate A, port 8080
│ - Auth (JWT) │
│ - Product/Rules CRUD │
│ - Scan orchestration │
│ - Compliance persistence│
│ - Reports + Dashboard │
└────────────┬─────────────┘
             │ REST/JSON (no auth — internal call)
             ▼
┌─────────────────────────┐
│ ML SERVICE (FastAPI) │ <-- Teammate B (you), port 7860
│ STATELESS — never │
│ touches the DB │
│ Preprocess → Detect │
│ → OCR → Extract → │
│ Font-Analyze → Rules │
└────────────┬─────────────┘
             │
   ┌─────────▼─────────┐
   │ Supabase Postgres │ (Spring Boot only)
   └───────────────────┘
   Image files → Cloudinary
```

- **No Docker.** Everyone runs natively: `npm run dev`, `mvn spring-boot:run`, `uvicorn ... --reload`.
- **ML service is stateless.** It receives image(s), returns JSON, forgets everything. Spring Boot owns all persistence.
- **No auth on the Spring Boot → ML service call.** It's an internal call on the local network; skip the API key header entirely.

---

## 2. Repository Structure

```
legal-metrology-compliance/
├── frontend/                        # React + Vite
│   ├── src/
│   ├── package.json
│   └── .env
│
├── backend/                         # Spring Boot (Teammate A)
│   ├── src/main/java/com/lmcompliance/
│   │   ├── LmComplianceApplication.java
│   │   ├── config/
│   │   │   ├── SecurityConfig.java
│   │   │   └── WebClientConfig.java
│   │   ├── auth/
│   │   ├── user/
│   │   ├── product/
│   │   ├── scan/
│   │   │   ├── ScanService.java
│   │   │   ├── ScanController.java
│   │   │   └── MlServiceClient.java
│   │   ├── declaration/
│   │   ├── compliance/
│   │   ├── report/
│   │   ├── dashboard/
│   │   ├── storage/
│   │   └── common/
│   ├── src/main/resources/application.properties
│   └── pom.xml
│
├── ml-service/                      # FastAPI — YOUR MODULE
│   ├── app/
│   │   ├── main.py                  # FastAPI entrypoint
│   │   ├── api/
│   │   │   ├── routes.py            # /analyze, /health, /rules
│   │   │   └── schemas.py           # Pydantic request/response models
│   │   │
│   │   ├── preprocessing/
│   │   │   ├── deskew.py
│   │   │   ├── perspective_correction.py
│   │   │   ├── denoise_enhance.py
│   │   │   └── pipeline.py
│   │   │
│   │   ├── detection/
│   │   │   ├── text_detector.py     # PaddleOCR/CRAFT wrapper
│   │   │   └── region_classifier.py # classify regions into declaration types
│   │   │
│   │   ├── ocr/
│   │   │   ├── ocr_engine.py        # PaddleOCR/EasyOCR wrapper
│   │   │   └── postprocess_text.py  # cleanup, unit normalization, OCR confusions
│   │   │
│   │   ├── extraction/
│   │   │   ├── regex_patterns.py
│   │   │   ├── field_extractor.py   # structures OCR text into typed fields
│   │   │   └── ner_model.py         # optional, stretch goal
│   │   │
│   │   ├── font_analysis/
│   │   │   ├── calibration.py       # px→mm via barcode-as-ruler
│   │   │   ├── font_measure.py      # cap-height in mm vs. rule table
│   │   │   └── readability.py       # contrast/readability checks
│   │   │
│   │   ├── compliance/
│   │   │   ├── rules_db.py          # ██ THE RULE MATRIX ██ (Python dict)
│   │   │   ├── rule_engine.py       # applies rules_db to extracted data
│   │   │   └── report_builder.py    # assembles final JSON response
│   │   │
│   │   ├── models/                  # trained/fine-tuned weights (gitignored)
│   │   │   ├── detector/
│   │   │   ├── ocr_recognizer/
│   │   │   └── ner/
│   │   │
│   │   └── utils/
│   │       ├── image_io.py
│   │       ├── logger.py
│   │       └── config.py
│   │
│   ├── data/
│   │   ├── raw_images/
│   │   ├── annotations/
│   │   ├── processed/
│   │   └── gold_test_set/           # 30–50 manually verified images
│   │
│   ├── training/
│   │   ├── train_detector.py
│   │   ├── train_ocr_recognizer.py
│   │   ├── train_ner.py
│   │   └── configs/
│   │       ├── detector_config.yaml
│   │       └── ocr_config.yaml
│   │
│   ├── evaluation/
│   │   ├── evaluate_detection.py    # Precision/Recall/F1
│   │   ├── evaluate_ocr.py          # CER/WER
│   │   ├── evaluate_e2e.py          # full pipeline accuracy vs. gold set
│   │   └── results/
│   │
│   ├── tests/
│   │   ├── test_preprocessing.py
│   │   ├── test_ocr.py
│   │   ├── test_extraction.py
│   │   ├── test_font_analysis.py
│   │   ├── test_compliance_engine.py
│   │   └── test_api.py
│   │
│   ├── scripts/
│   │   ├── download_models.sh
│   │   ├── setup_env.sh
│   │   └── run_local.sh
│   │
│   ├── notebooks/
│   │   └── exploration.ipynb
│   │
│   ├── docs/
│   │   ├── API_CONTRACT.md
│   │   ├── ARCHITECTURE.md
│   │   └── EVALUATION_REPORT.md
│   │
│   ├── requirements.txt
│   ├── .env.example
│   ├── .gitignore
│   └── README.md
│
└── README.md
```

---

## 3. Tech Stack

| Layer | Choice |
|---|---|
| Frontend | React + Vite |
| Backend framework | Spring Boot 3.3+ (Java 21) |
| Backend DB access | Spring Data JPA + Hibernate |
| Backend config | `application.properties` |
| Auth (frontend↔backend) | Spring Security + JWT (jjwt) |
| Database | PostgreSQL via Supabase |
| Image/file storage | Cloudinary free tier |
| ML microservice | FastAPI (Python 3.11+) |
| OCR engine | **PaddleOCR** (primary) / EasyOCR (fallback wrapper option) |
| Image preprocessing | OpenCV + Pillow |
| Rule engine | Python dict (`rules_db.py`) — swappable later for a live Postgres `rules` table |
| Font/size analysis | Barcode-based px→mm calibration, cap-height measured in mm against rule table |
| PDF report | Spring Boot side, OpenPDF |
| Containerization | None |

`ml-service/requirements.txt`:
```
fastapi
uvicorn[standard]
python-multipart
opencv-python
numpy
pillow
paddleocr
paddlepaddle
easyocr
pydantic
pyyaml
scikit-image
pytest
```

`ml-service/.env.example`:
```
MODEL_VERSION=v1.0
LOG_LEVEL=INFO
MAX_IMAGE_SIZE_MB=10
CONFIDENCE_THRESHOLD=0.5
```

---

## 4. Database Schema (Spring Boot / Supabase Postgres)

**`rules`**
| Column | Type | Notes |
|---|---|---|
| id | UUID | PK |
| rule_code | varchar | e.g. `RULE_6_1_A` |
| description | text | |
| check_type | varchar | e.g. `presence`, `font_ratio` |
| severity | varchar | `FAIL`, `WARNING` |

**`users`**: `id` (UUID PK), `username`, `email`, `password_hash` (BCrypt), `role` (`ADMIN`/`INSPECTOR`), `created_at`

**`products`**: `id` (UUID PK), `name`, `category`, `brand` (nullable), `created_by` (FK → users.id), `created_at`

**`scans`**: `id`, `product_id` (FK, nullable), `image_url`, `status` (`PENDING`/`PROCESSING`/`COMPLETED`/`FAILED`), `ocr_raw_text`, `overall_compliance` (`COMPLIANT`/`NON_COMPLIANT`/`PARTIAL`), `compliance_score`, `created_by`, `created_at`, `processed_at`, `error_message`

**`declarations`**: `id`, `scan_id` (FK), `declaration_type`, `present` (bool), `extracted_value`, `confidence_score`, `bounding_box` (jsonb)

**`compliance_results`**: `id`, `scan_id` (FK), `rule_code`, `rule_description`, `status` (`PASS`/`FAIL`/`WARNING`/`NOT_APPLICABLE`), `remarks`, `created_at`

Spring Boot maps the ML service's response (Section 6) into `declarations` and `compliance_results` rows keyed by `scan_id`.

---

## 5. API Contract — Spring Boot → ML Service

### `POST /api/v1/analyze`
No auth header. Internal call, same trusted network.

Request (`multipart/form-data`):
| Field | Type | Notes |
|---|---|---|
| images | file[] | 1 or more images of the same product (front/back/side) |
| scan_id | string | Spring Boot's scan UUID — echoed back in the response |
| category | string | optional |

Response `200 OK`:
```json
{
  "scan_id": "uuid-echoed-back",
  "status": "SUCCESS",
  "processed_at": "2026-08-27T10:00:00Z",
  "declarations": {
    "manufacturer_name_address": {
      "present": true, "value": "ABC Foods Pvt Ltd, Pune, MH",
      "confidence": 0.92, "bbox": [120, 340, 480, 60], "source_image_index": 0
    },
    "commodity_name": {
      "present": true, "value": "Refined Sunflower Oil",
      "confidence": 0.89, "bbox": [100, 300, 300, 40], "source_image_index": 0
    },
    "net_quantity": {
      "present": true, "value": "500 g", "confidence": 0.88,
      "bbox": [200, 410, 150, 40], "source_image_index": 0
    },
    "mrp": {
      "present": true, "value": "₹120.00 (incl. of all taxes)",
      "confidence": 0.95, "bbox": [200, 460, 220, 40], "source_image_index": 0
    },
    "mfg_date": { "present": true, "value": "07/2026", "confidence": 0.81, "bbox": [180, 500, 100, 30], "source_image_index": 0 },
    "consumer_care": { "present": false, "value": null, "confidence": 0.0, "bbox": null, "source_image_index": null },
    "country_of_origin": { "present": false, "value": null, "confidence": 0.0, "bbox": null, "source_image_index": null },
    "unit_sale_price": { "present": false, "value": null, "confidence": 0.0, "bbox": null, "source_image_index": null },
    "dimensions": { "present": false, "value": null, "confidence": 0.0, "bbox": null, "source_image_index": null }
  },
  "font_analysis": [
    {
      "field": "net_quantity",
      "measured_height_mm": 3.8,
      "required_min_mm": 4.0,
      "compliant": false
    }
  ],
  "violations": [
    { "rule_ref": "Rule 6(1)(f)", "field": "consumer_care", "issue": "Mandatory declaration missing" },
    { "rule_ref": "Rule 7", "field": "net_quantity", "issue": "Font height 3.8mm is below required 4.0mm" }
  ],
  "overall_compliance_status": "NON_COMPLIANT",
  "confidence_flags": {
    "needs_manual_review": true,
    "low_confidence_fields": ["mfg_date"]
  }
}
```

Response `4xx/5xx`:
```json
{ "status": "ERROR", "error_code": "INVALID_IMAGE", "message": "Uploaded file is not a readable image" }
```

Other endpoints:
- `GET /api/v1/health` → `{ "status": "ok", "model_version": "v1.2" }`
- `GET /api/v1/rules` → returns current `rules_db.py` contents as JSON

Agree this contract with your backend teammate on day 1, then neither of you touches the other's code again.

---

## 6. Fixed List of Declaration Types

```
MANUFACTURER_NAME_ADDRESS
COMMODITY_NAME
NET_QUANTITY
MRP
MFG_DATE
CONSUMER_CARE_DETAILS
COUNTRY_OF_ORIGIN
DIMENSIONS
UNIT_SALE_PRICE
```

---

## 7. Rule Matrix — `app/compliance/rules_db.py`

Python dict, not JSON. Same content shape as the original rule tables (regex, font-size table, required phrases) — just expressed in code so `rule_engine.py` never touches a file-parsing step. This is what a future live Postgres `rules` table replaces without touching `rule_engine.py`.

```python
RULES_DB = {
    "RULE_6_1_A_MANUFACTURER_NAME": {
        "description": "Package must declare name and address of manufacturer/packer/importer",
        "declaration_type": "MANUFACTURER_NAME_ADDRESS",
        "mandatory": True,
        "check_type": "presence",
        "severity": "FAIL",
    },
    "RULE_6_1_B_COMMODITY_NAME": {
        "description": "Package must declare the common/generic name of the commodity",
        "declaration_type": "COMMODITY_NAME",
        "mandatory": True,
        "check_type": "presence",
        "severity": "FAIL",
    },
    "RULE_6_7_NET_QUANTITY": {
        "description": "Package must declare net quantity in standard units",
        "declaration_type": "NET_QUANTITY",
        "mandatory": True,
        "check_type": "presence_and_format",
        "severity": "FAIL",
        "format_regex": r"\d+(\.\d+)?\s?(g|kg|ml|l|gm|GM|ML)",
        "font_size_table": [
            {"max_net_qty_grams_or_ml": 200, "min_font_mm": 2},
            {"max_net_qty_grams_or_ml": 1000, "min_font_mm": 4},
            {"max_net_qty_grams_or_ml": None, "min_font_mm": 6},
        ],
    },
    "RULE_6_1_E_MRP": {
        "description": "Package must declare Maximum Retail Price",
        "declaration_type": "MRP",
        "mandatory": True,
        "check_type": "presence_and_format",
        "severity": "FAIL",
        "format_regex": r"(₹|Rs\.?|INR)\s?\d+(\.\d{2})?",
        "must_contain_phrase": ["incl. of all taxes", "inclusive of all taxes"],
    },
    "RULE_6_1_D_MFG_DATE": {
        "description": "Package must declare month and year of manufacture/import",
        "declaration_type": "MFG_DATE",
        "mandatory": True,
        "check_type": "presence_and_format",
        "severity": "FAIL",
        "format_regex": r"(0[1-9]|1[0-2])/\d{4}",
    },
    "RULE_6_1_F_CONSUMER_CARE": {
        "description": "Package must declare consumer care/complaint contact details",
        "declaration_type": "CONSUMER_CARE_DETAILS",
        "mandatory": True,
        "check_type": "presence",
        "severity": "FAIL",
    },
    "RULE_6_1_C_COUNTRY_OF_ORIGIN": {
        "description": "Imported packages must declare country of origin",
        "declaration_type": "COUNTRY_OF_ORIGIN",
        "mandatory": False,   # only mandatory for imported goods
        "check_type": "presence",
        "severity": "WARNING",
    },
    "RULE_18_DIMENSIONS": {
        "description": "Certain commodities must declare number/dimensions",
        "declaration_type": "DIMENSIONS",
        "mandatory": False,   # category-dependent
        "check_type": "presence",
        "severity": "WARNING",
    },
    "RULE_6_UNIT_SALE_PRICE": {
        "description": "Multi-piece packages must declare unit sale price",
        "declaration_type": "UNIT_SALE_PRICE",
        "mandatory": False,   # only for multi-packs
        "check_type": "presence",
        "severity": "WARNING",
    },
}
```

`rule_engine.py` reads `mandatory`/`severity` to decide whether a missing field is a `FAIL` violation or just a flag, and reads `format_regex`/`font_size_table`/`must_contain_phrase` to validate the value once the field is present.

---

## 8. ML Pipeline — What Happens Inside `/analyze`

```python
# app/api/routes.py
@router.post("/analyze")
async def analyze(images: list[UploadFile], scan_id: str, category: str | None = None):
    processed = [preprocess(load(img)) for img in images]
    regions = [detect_text_regions(img) for img in processed]
    ocr_results = [run_ocr(r) for region_set in regions for r in region_set]
    declarations = extract_fields(ocr_results, RULES_DB)
    font_analysis = analyze_fonts(regions, RULES_DB)
    violations = check_compliance(declarations, font_analysis, RULES_DB)
    return build_report(scan_id, declarations, font_analysis, violations)
```

1. **Preprocess** (`preprocessing/pipeline.py`): perspective correction → deskew → denoise/enhance.
2. **Detect text regions** (`detection/text_detector.py`): PaddleOCR's built-in detector, returns `[{"bbox": [...], "crop": ...}]`.
3. **Classify regions** (`detection/region_classifier.py`): keyword/regex match against `rules_db.py` to guess declaration type per region.
4. **OCR** (`ocr/ocr_engine.py`): `run_ocr(region_crop) -> {"text": ..., "confidence": ...}` via PaddleOCR (EasyOCR as swappable fallback behind the same function signature).
5. **Postprocess text** (`ocr/postprocess_text.py`): strip noise, normalize units (`gm`→`g`), fix `O`↔`0` type confusions.
6. **Extract fields** (`extraction/field_extractor.py`): regex-match cleaned OCR text against `rules_db.py` patterns, produce the `declarations` object.
7. **Font analysis** (`font_analysis/`):
   - `calibration.py`: detect the product barcode in-frame, use its fixed real-world module width as a built-in ruler for px→mm conversion. (Communicate this to frontend as a hard requirement for the capture flow — barcode must be in frame.)
   - `font_measure.py`: measure cap-height of each detected text region in px, convert to mm, compare against the field's `font_size_table`.
   - `readability.py`: text/background contrast ratio (luminance difference) check.
8. **Rule engine** (`compliance/rule_engine.py`): evaluate declarations + font analysis against `RULES_DB`, build `violations[]`.
9. **Report builder** (`compliance/report_builder.py`): assemble the final response matching Section 5.

---

## 9. Roadmap (4–5 week build)

| Week | Focus |
|---|---|
| 1 | Rule matrix (`rules_db.py`) + dataset collection starts (500–1500+ label images, annotate in Label Studio/CVAT, COCO export) + preprocessing pipeline |
| 2 | Text detection + OCR wrapper — get a rough end-to-end pipeline working, even at low accuracy. **Checkpoint: run preprocess→detect→OCR→extract→compliance manually end-to-end at least once by end of week 2**, so backend has a real API to build against immediately |
| 3 | Field extraction + font analysis (calibration) + rule engine — full pipeline logically complete |
| 4 | FastAPI wrapper finished, hand `/analyze` off to backend teammate; they integrate while you keep improving accuracy |
| 5 | Evaluation (gold test set, CER/WER, F1, end-to-end accuracy vs. manual audit) + fine-tuning weak components + docs polish + demo prep |

Backend (Spring Boot) and frontend (React) tracks run in parallel starting Week 1, using the API contract in Section 5 as their fixed target — they build against it before your pipeline is fully accurate.

---

## 10. Local Development (native, no Docker)

```
# Terminal 1 — frontend
cd frontend && npm run dev

# Terminal 2 — backend
cd backend && mvn spring-boot:run

# Terminal 3 — ml-service
cd ml-service && uvicorn app.main:app --host 0.0.0.0 --port 7860 --reload
```

Set up once: GitHub repo → Supabase project (copy Postgres connection string) → Cloudinary account (copy `CLOUDINARY_URL`).

---

## 11. Technical Documentation Deliverable

- `ml-service/docs/ARCHITECTURE.md` — Section 1 diagram + Section 8 pipeline breakdown.
- `ml-service/docs/API_CONTRACT.md` — Section 5.
- `ml-service/docs/EVALUATION_REPORT.md` — Week 5 evaluation metrics.

Hand these three to whoever compiles the final project documentation.

---

## 12. Checklist Before Calling It Done

- [ ] `rules_db.py` covers every mandatory declaration in Rules 6–18.
- [ ] `/api/v1/analyze` returns valid JSON matching Section 5 for a real image, in under ~5 seconds.
- [ ] Barcode-based font calibration strategy agreed with whoever owns the capture flow (frontend).
- [ ] Gold test set (30–50 images) evaluated, metrics written into `EVALUATION_REPORT.md`.
- [ ] Backend teammate has successfully called `/analyze` from Spring Boot at least once before the demo.
- [ ] `ml-service/README.md` explains how to run it standalone in under 5 commands.
