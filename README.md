# Legal Metrology Compliance Checker

Automated verification of mandatory declarations on pre-packaged commodity
labels, against the Legal Metrology (Packaged Commodities) Rules, 2011.
Smart India Hackathon prototype.

```
frontend/   React + Vite — government-portal style UI          (port 3000)
backend/    Spring Boot 4 — auth, products, scans, dashboard,  (port 8080)
            PDF reports, orchestration
ml-service/ FastAPI — preprocess → detect → OCR → extract →     (port 7860)
            font-analysis → rule engine → report
```

The browser talks only to the backend. The backend calls the ML service
(`POST /api/v1/analyze`) internally and stores everything.

---

## Quick start (demo — no external accounts)

Two terminals. The backend's **`dev` profile** uses an in-memory database, a
local image store, and a **mocked ML service**, so the whole scan flow works
offline.

```bash
# terminal 1 — backend
cd backend/backend
mvn spring-boot:run "-Dspring-boot.run.profiles=dev"

# terminal 2 — frontend
cd frontend
npm install        # first time only
npm run dev
```

Open **http://localhost:3000** and sign in:

| Login | Password | Role |
|---|---|---|
| `admin@packsure.test` | `Admin@12345` | Administrator (sees all scans) |
| `inspector@packsure.test` | `Inspector@123` | Inspector (sees own scans) |

---

## Full stack (real ML pipeline)

### 1. ML service

```bash
cd ml-service
python -m venv .venv && .venv\Scripts\activate     # Windows
pip install -r requirements.txt                     # heavy: paddleocr, paddlepaddle, easyocr
uvicorn app.main:app --host 0.0.0.0 --port 7860 --reload
```
First run downloads the OCR models (needs internet). Health check:
`GET http://localhost:7860/api/v1/health`.

### 2. Backend against real services

`backend/backend/.env` (copy from `.env.example`) — set real Supabase +
Cloudinary credentials and:
```
ML_SERVICE_URL=http://localhost:7860/api/v1
```
Then run **without** the dev profile:
```bash
cd backend/backend
mvn spring-boot:run
```
Now `MlServiceClient` sends the uploaded image as `multipart/form-data` to the
ML service and maps the returned report onto the scan.

### 3. Frontend
Same as above (`npm run dev`). It's backend-only aware — no ML config needed.

---

## Tests

```bash
cd backend/backend && mvn test        # 20 integration tests, offline
cd ml-service && pytest               # ML pipeline unit tests
cd frontend && npm run build          # type-check + build
```

## The ML `/analyze` contract

`POST /api/v1/analyze` · `multipart/form-data`: `images` (file[]) + `product_id` (form).
Returns `{ product_id, status, processed_at, declarations{}, font_analysis[],
violations[], overall_compliance_status, confidence_flags{} }`.
See `ml-service/app/api/schemas.py` and `backend/.../scan/dto/MlAnalyzeResponse.java`.
