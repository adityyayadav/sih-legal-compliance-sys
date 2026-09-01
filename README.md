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

## Real ML analysis — no Supabase / Cloudinary needed

Keep the `dev` profile (H2 + local image store) but point the backend at the
**real** ML service instead of the mock.

### 1. Start the ML service

```powershell
cd ml-service
python -m venv .venv
.venv\Scripts\activate
pip install fastapi "uvicorn[standard]" python-multipart opencv-python numpy pillow pydantic scikit-image
pip install easyocr          # for real OCR — large download; without it, OCR falls back to a stub
uvicorn app.main:app --host 127.0.0.1 --port 7860
```
Health check: `GET http://localhost:7860/api/v1/health` → `{"status":"ok",...}`
First scan with `easyocr` installed downloads the recognizer model (needs internet).

### 2. Start the backend with the real client

```powershell
cd backend\backend
mvn spring-boot:run "-Dspring-boot.run.profiles=dev" "-Dspring-boot.run.arguments=--app.ml.mock=false"
```
`app.ml.mock=false` swaps `MockMlAnalysisClient` for the real `MlServiceClient`,
which sends the uploaded image as `multipart/form-data` to `/api/v1/analyze` and
maps the returned report (declarations / violations / font analysis) onto the scan.

### 3. Frontend — unchanged
```powershell
cd frontend
npm run dev
```

## Production (persistent DB + cloud image store)

Fill `backend/backend/.env` (from `.env.example`) with real Supabase + Cloudinary
credentials, set `ML_SERVICE_URL=http://localhost:7860/api/v1`, and run the
backend with **no** profile flag (`mvn spring-boot:run`).

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
