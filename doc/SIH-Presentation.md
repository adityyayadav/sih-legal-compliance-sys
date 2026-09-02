# Legal Metrology Compliance Portal — SIH Presentation

**Duration:** 12–14 min talk + 2–3 min Q&A
**Format:** 15 slides (13 main + Title + Q&A), plus 4 backup slides
**Theme:** Government-of-India portal look (navy / saffron / green, Ashoka chakra, Noto Serif headings)

> Each slide below has: **what to put on the slide** (keep it sparse — 4–6 bullets max) and a **script** (what you actually say). Trim the script to hit the time budget in the header.

---

## Slide 1 — Title  ·  0:30

**On slide**
- Automated Legal Metrology Compliance Verification Portal
- Smart India Hackathon 2025
- Problem statement: *Automated checking of pre-packaged commodity labels for Legal Metrology compliance* — Department of Consumer Affairs / Legal Metrology
- Team name + members
- One tagline: *"From a photo of a label to an inspection-ready compliance report in seconds."*

**Script**
> Good morning. We're **[team]**, and we've built an automated compliance-verification portal for the Department of Legal Metrology. The one-line version: an enforcement officer takes a photo of a product label, and our system tells them — against the Packaged Commodities Rules — exactly what's declared, what's missing, and whether the print is large enough, and hands back a signed-style PDF report. Let me show you why that matters.

---

## Slide 2 — The Problem  ·  1:30

**On slide**
- ~**Every pre-packaged commodity sold in India** must carry mandatory declarations (Rule 6) at a minimum print size (Rule 7)
- Enforcement today is **manual** — an officer physically reads each pack against a checklist
- **Doesn't scale:** millions of SKUs, exploding e-commerce listings, limited inspectors
- **Inconsistent:** outcome depends on which officer, how tired, how much time
- **No audit trail:** hard to prove what was checked and why
- Consumers pay the price — missing MRP, no manufacturer address, undersized net-quantity text

**Script**
> Under the Legal Metrology (Packaged Commodities) Rules, 2011, every packaged good has to declare seven things — who made it, what it is, how much is inside, the MRP inclusive of taxes, the month of manufacture, a consumer-care contact, and for imports the country of origin. And Rule 7 says how *large* that text has to be printed.
>
> Right now, checking this is a person with a checklist and a ruler. That approach has three problems. It **doesn't scale** — there are millions of SKUs and e-commerce adds thousands of new listings a day. It's **inconsistent** — two officers, two verdicts. And there's **no record** — you can't easily audit what was inspected. The result is non-compliant packs on shelves, and consumers who can't find the MRP or a way to complain.

---

## Slide 3 — The Legal Framework  ·  1:00

**On slide**
- **Legal Metrology Act, 2009**  +  **LM (Packaged Commodities) Rules, 2011**
- **Rule 6 — Mandatory declarations:** manufacturer/packer/importer name & address · common name · net quantity · MRP ("incl. of all taxes") · month/year of manufacture · consumer-care details · country of origin (imports)
- **Rule 7 — Size of declarations:** minimum letter/numeral height by pack size (e.g. ≥ 4 mm for net quantity above 200 g/ml)
- Non-compliance → penalty under the Act
- Our rule matrix is a **configurable file**, not hard-coded — updates when the Rules change

**Script**
> This is the legal backbone. The Act and the 2011 Rules. Rule 6 is the *what* — the seven mandatory declarations. Rule 7 is the *how big* — there's a table of minimum text heights based on the net quantity of the pack.
>
> One design decision we want to highlight early: we didn't bake these rules into code. They live in a **configuration file** — rule codes, regex patterns, the font-size table, required phrases. When the Rules are amended, you edit that file, not the software.

---

## Slide 4 — Our Solution  ·  1:30

**On slide**
- A web portal for enforcement officers — nothing to install
- **Workflow:** ① register the product → ② photograph the principal display panel → ③ submit → ④ review the extracted declarations & rule results → ⑤ download the PDF report
- Processing is automatic: extract → measure → rule-check → report
- **Every declaration graded** PASS / WARNING / FAIL, with the extracted value and a confidence score
- **Dashboard:** compliance rate, top violations, scan volume — per officer or department-wide
- **Roles:** Inspectors see their own scans; Administrators see everything

**Script**
> Our answer is a portal — it runs in a browser, there's nothing for the department to install on every machine. The officer registers the product, uploads a photo of the front panel, and hits submit. Behind the scenes we extract the declarations, measure the print size, run the rule engine, and build a report.
>
> The officer gets a page showing each declaration — is it present, what did we read, how confident are we — and each rule graded PASS, WARNING or FAIL. They download a PDF for the case file. And there's a dashboard with the compliance rate, the most common violations, and scan volume — scoped to that officer, or department-wide for an administrator.

---

## Slide 5 — Live Demo  ·  3:30

**On slide** (minimal — this is a talking slide)
- **DEMO**
- Login → Dashboard → New Scan → Compliance Report → PDF → Roles

**Demo script (do this live — see the DEMO SCRIPT section at the bottom):**
1. Log in as **Administrator** → land on the **Dashboard**. Point at the donut (compliance breakdown), the "most frequent violations" bar chart, recent scans.
2. **Scans → New Scan.** Pick a product, upload a clean label photo, submit.
3. Land on the **Compliance Report** — walk through: verdict banner + rule-score meter, the Declarations table (present / value / confidence), the Rule Compliance Results table (PASS/WARN/FAIL with the rule reference and remarks).
4. **Download PDF** — open it, show the inspection-ready format.
5. Sign out, log in as **Inspector** — show the scan list now only shows *their* scans, and opening someone else's scan is blocked.

> **Fallback:** if the network/ML is slow, use pre-loaded seeded scans and one pre-run scan. Never debug live.

---

## Slide 6 — System Architecture  ·  2:00

**On slide** — a 3-box diagram

```
  ┌──────────────┐    REST + JWT     ┌──────────────────┐   multipart HTTP   ┌────────────────────┐
  │  React SPA   │ ───────────────▶ │  Spring Boot API │ ─────────────────▶ │  FastAPI ML Service │
  │  (browser)   │ ◀─────────────── │   (Java 21)      │ ◀───────────────── │   (Python)          │
  └──────────────┘                  └───────┬──────────┘                    └────────────────────┘
                                            │
                          ┌─────────────────┼──────────────────┐
                          ▼                                     ▼
                  PostgreSQL (Supabase)                Cloudinary  (image store)
```

- **Frontend** — React + TypeScript + Vite. Government-portal UI (GIGW styling), accessibility bar, role-aware nav.
- **Backend** — Spring Boot 4 / Java 21. Auth, product & scan management, orchestration, persistence, dashboard aggregates, PDF generation, RBAC. 20 automated integration tests.
- **ML service** — FastAPI. Stateless: image in → JSON report out. Never touches the database.
- **Clean separation** — each layer swappable; the ML team and the backend team agreed one JSON contract and worked independently.

**Script**
> Three tiers, three teams, one contract. The **React frontend** is what the officer sees — styled to the government web guidelines, with the accessibility bar and role-aware navigation.
>
> The **Spring Boot backend** is the coordinator. It handles login with JWT, stores products and scans in Postgres, orchestrates a scan, aggregates the dashboard numbers, and generates the PDF. It's the only component that talks to the database.
>
> The **ML service** is deliberately dumb and stateless — you give it an image, it gives you back a JSON report, and it forgets everything. That let our ML teammate and our backend teammate agree on one JSON schema on day one and then never block each other.

---

## Slide 7 — What Happens to One Scan  ·  1:30

**On slide** — a pipeline strip

```
 upload ─▶ store image ─▶ PENDING row ─▶ POST /analyze ─▶ map report ─▶ COMPLETED
                                              │
   preprocess ─▶ detect text ─▶ OCR ─▶ extract fields ─▶ font analysis ─▶ rule engine ─▶ build report
```

- Backend: upload → save `PENDING` → call ML → persist declarations + results → `COMPLETED` (or `FAILED`)
- The slow work (upload, ML call) runs **outside the DB transaction** — no held connections
- Image is **downscaled to 2000 px** before the ML call — keeps text legible, cuts OCR time
- Failure is graceful — scan ends `FAILED` with a reason, never hangs

**Script**
> When a scan comes in, the backend stores the image, writes a PENDING row so the officer can see it immediately, then calls the ML service. When the report comes back it writes the declarations and rule results and flips the scan to COMPLETED — or FAILED with a reason if the ML service is down.
>
> Two engineering details we're proud of: the upload and the ML call happen *outside* the database transaction, so we never hold a connection open for 30 seconds. And we downscale the photo to 2000 pixels before sending it — a 6-megapixel phone photo becomes 200 kilobytes, the text stays readable, and OCR time drops from a minute to about fifteen seconds.

---

## Slide 8 — Inside the ML Pipeline  ·  2:00

**On slide** — 7 numbered stages

1. **Preprocess** — perspective correction, deskew, denoise, contrast
2. **Text detection** — locate every text region (PaddleOCR detector, OpenCV fallback)
3. **OCR** — read each region (EasyOCR), clean the text (unit normalisation, `O`↔`0` fixes)
4. **Field extraction** — regex + keyword + light NER → map text to the 7 declaration types
5. **Font analysis** — detect the **barcode**, use its fixed module width as a **built-in ruler**, measure cap-height in **mm**, compare to the Rule 7 table
6. **Rule engine** — evaluate declarations + font analysis against the configurable rule matrix → violations with rule refs & severity
7. **Report builder** — assemble the JSON: declarations, font analysis, violations, overall status, confidence flags

**Script**
> Inside the ML service, seven stages. We straighten and clean the image. We find every block of text. We read it with EasyOCR and normalise it — "gm" becomes "g", common OCR confusions get fixed. We map each piece of text to one of the seven declaration types using regex and keyword rules.
>
> Stage five is the clever one. Rule 7 is in *millimetres*, but a photo is in *pixels* — and we don't know the scale. So we find the **barcode** on the pack. A barcode's bar width is a fixed physical size. That gives us a millimetre-per-pixel ratio — a ruler that's already in the photo. Now we can measure the net-quantity text in real millimetres and check it against the legal minimum.
>
> Then the rule engine applies the matrix and produces the violation list, and the report builder packages it all up.

---

## Slide 9 — Backend Engineering  ·  1:00

**On slide**
- **Auth** — JWT access + rotating refresh tokens; passwords BCrypt-hashed
- **RBAC** — `ADMIN` sees all scans & department stats; `INSPECTOR` sees only their own (enforced server-side)
- **Rule matrix** — externalised JSON, versioned with the Rules
- **Reports** — server-generated PDF (OpenPDF): meta, declarations table, results table, verdict
- **Quality** — 20 automated integration tests, run fully offline; consistent typed error responses (400 / 401 / 403 / 404 / 409 / 413 / 502)
- **Runs anywhere** — one profile flag switches between a full offline mock and the real services

**Script**
> On the backend: proper auth — short-lived JWTs, rotating refresh tokens, hashed passwords. Role-based access is enforced on the server, not just hidden in the UI — an inspector literally cannot fetch another inspector's scan.
>
> We have twenty automated integration tests that run without any external service, so the whole team can develop offline. And a single configuration flag flips the system between a fully mocked offline mode — useful for the frontend team and for demos — and the real Supabase-plus-ML deployment.

---

## Slide 10 — Tech Stack  ·  0:30

**On slide** — grouped list or logos

| Layer | Tech |
|---|---|
| Frontend | React 18 · TypeScript · Vite · TanStack Query |
| Backend | Java 21 · Spring Boot 4 · Spring Security · Hibernate/JPA |
| Database | PostgreSQL (Supabase) |
| ML service | Python · FastAPI · OpenCV · EasyOCR · scikit-image |
| Storage / Reports | Cloudinary · OpenPDF |
| Infra | No Docker required · runs natively · single-flag dev mode |

**Script**
> Nothing exotic. React and TypeScript on the front. Java 21 and Spring Boot on the back. Postgres for data. Python and FastAPI for the model service, with OpenCV and EasyOCR. All open-source, all standard, all deployable on existing government infrastructure — no proprietary cloud lock-in.

---

## Slide 11 — Status: What's Working  ·  1:00

**On slide**
- ✅ **End-to-end integrated** — frontend → backend → ML service, one real scan produces a real report
- ✅ Auth, products, scans, filters, pagination, dashboard, PDF export — all live
- ✅ 20 backend tests green · frontend builds clean
- ✅ Offline demo mode (rotating mock) for reliable presentations
- 🔧 **OCR accuracy is the active work item** — pretrained EasyOCR on CPU; extraction improves markedly with (a) clean captures and (b) fine-tuning on our annotated dataset
- 📊 Evaluation metrics: `ml-service/docs/EVALUATION_REPORT.md`

**Script**
> Where we are: the whole stack is integrated. A real photo goes in one end and a real compliance report comes out the other — we're not faking the connection.
>
> The honest gap is OCR accuracy. We're running a general-purpose OCR model on a CPU. On a clean, straight-on capture it does well; on an angled phone photo of a cluttered wrapper it misses some fields. That's a **training** problem, not an architecture problem — we have an annotated dataset ready to fine-tune on, and our evaluation report has the current numbers.

---

## Slide 12 — Impact & Feasibility  ·  1:30

**On slide**
- **Speed** — seconds per pack vs minutes of manual checking; one officer covers many times the SKUs
- **Consistency** — same rules, same verdict, every time; removes human variance
- **Auditability** — every scan stored with image, extracted values, confidence, verdict, timestamp, officer
- **E-commerce ready** — the same `/analyze` API can be pointed at marketplace listing images in bulk
- **Low cost to adopt** — browser-based, open-source, no per-seat license, runs on existing servers
- **Future-proof** — rule matrix is config; amend the Rules → edit a file

**Script**
> Why this matters in practice. **Speed** — a check that took minutes takes seconds, so an officer's reach multiplies. **Consistency** — the rule engine doesn't have a bad day. **Auditability** — every scan is on record with the image and the reasoning, which is exactly what you need for enforcement action or an appeal.
>
> And it extends. The same analysis API that reads a photo in the field can be pointed at e-commerce listing images at scale. It's browser-based and open-source, so adoption cost is basically zero. And because the rules are configuration, the department maintains it without a software release.

---

## Slide 13 — Roadmap  ·  1:00

**On slide**
- **Near term** — fine-tune the detector + recognizer on the annotated label dataset; add a mobile capture flow with on-screen capture guidance (barcode-in-frame)
- **Mid term** — batch mode for e-commerce catalogues; live rules table (Postgres) replacing the JSON file with an admin UI
- **Long term** — multilingual OCR (regional-language labels); integration hooks for the national enforcement / grievance systems; analytics for targeting inspections by brand/category risk

**Script**
> Next steps. Immediately: fine-tune the models on our labelled data, and build a phone capture screen that guides the officer to a good shot. Then a batch mode for marketplace catalogues, and moving the rule matrix into a database with an admin screen so non-developers can edit it. Longer term: regional-language OCR, and hooks into the department's existing enforcement and grievance systems so a failed scan can open a case directly.

---

## Slide 14 — Team  ·  0:30

**On slide**
- Names + roles: Frontend · Backend · ML · (Lead / Docs)
- Repo: `github.com/adityyayadav/sih-legal-compliance-sys`

**Script**
> Quick credits — [name] on the frontend, [name] on the backend, [name] on the ML pipeline. Code's on GitHub.

---

## Slide 15 — Thank You / Q&A  ·  remaining time

**On slide**
- Thank you
- "Automated Legal Metrology compliance — a photo to a verdict in seconds."
- Contact / repo QR

---

## Backup slides (only if asked)

**B1 — Data model** — `users`, `products`, `scans`, `declarations`, `compliance_results`, `refresh_tokens`; UUID PKs, `scan → declarations / results` one-to-many.

**B2 — ML API contract** — `POST /api/v1/analyze` (multipart `images[]` + `product_id`) → `{ declarations{}, font_analysis[], violations[], overall_compliance_status, confidence_flags }`. Plus `/health`, `/rules`.

**B3 — Rule matrix sample** — one rule entry: `rule_code`, `display_name`, `mandatory`, `format_regex`, `must_contain_phrase_any`, `font_size_table.tiers[]`, `severity`.

**B4 — Security specifics** — stateless sessions, CSRF disabled (token auth), CORS pinned to the frontend origin, `Content-Disposition` exposed for PDF download, role checks on every scan-scoped endpoint, public self-registration limited to `INSPECTOR`.

---

## Timing summary (target ≈ 13:00)

| # | Slide | min |
|---|---|---|
| 1 | Title | 0:30 |
| 2 | Problem | 1:30 |
| 3 | Legal framework | 1:00 |
| 4 | Solution | 1:30 |
| 5 | **Live demo** | 3:30 |
| 6 | Architecture | 2:00 |
| 7 | One scan's journey | 1:30 |
| 8 | ML pipeline | 2:00 |
| 9 | Backend engineering | 1:00 |
| 10 | Tech stack | 0:30 |
| 11 | Status | 1:00 |
| 12 | Impact & feasibility | 1:30 |
| 13 | Roadmap | 1:00 |
| 14 | Team | 0:30 |
| — | **Total** | **~13:00** + Q&A |

> If you're tight on time, cut **Slide 7** and shorten **Slide 8** to 1:00 — saves ~2:00.

---

## DEMO SCRIPT (rehearse this exactly)

**Setup before you present:**
- 3 terminals up: ML service (`uvicorn ... :7860`), backend (`mvn spring-boot:run "-Dspring-boot.run.profiles=dev"` — **use the mock, no `--app.ml.mock` flag**, it's reliable), frontend (`npm run dev`).
- Browser on `http://localhost:3000`, logged out.
- Have **one clean label photo** on the desktop, and know that seeded data already has 9 scans.
- Pre-run **one real scan** earlier so you can open its report instantly if the live one is slow.

**Run:**
1. **(20s)** "This is the officer's portal." → Login `admin@packsure.test` / `Admin@12345`.
2. **(45s)** Dashboard. "Department-wide view. Compliance breakdown — [X] compliant, [Y] non-compliant. Most frequent violation is [rule]. Recent scans here." Click into one completed scan.
3. **(60s)** Compliance Report. "Verdict at the top with a rule-score meter. Below: every declaration — present or not, what we extracted, our confidence. Then each rule — PASS, WARNING or FAIL, with the rule reference and a remark. Net-quantity print size measured at [n] mm against the [m] mm minimum."
4. **(30s)** Click **Download PDF**. Open it. "This is what goes in the case file."
5. **(40s)** Back → **Scans → New Scan**. Pick a product, choose the label photo, Submit. "Processing runs automatically." → land on the fresh report.
6. **(20s)** User menu → Sign out → login `inspector@packsure.test` / `Inspector@123`. Open **Scans**. "Same system, but this inspector only sees their own scans — and the server enforces that, it's not just hidden."
7. **(15s)** "That's the full loop — register, capture, analyse, report, done."

**Rules for the demo:**
- Never open dev tools or a terminal on screen.
- If something is slow, keep talking and switch to the pre-run scan.
- Don't type passwords slowly — use the demo credentials shown on the login screen.

---

## Likely questions + answers

**Q: How accurate is it?**
> On a clean, flat, well-lit capture the extraction is strong. On an angled photo of a busy wrapper it currently misses some fields — that's the pretrained OCR model on CPU. We have a labelled dataset ready to fine-tune on, and the evaluation report has current CER/field-F1 numbers. The architecture doesn't change when the model improves.

**Q: Why not just use a cloud OCR API?**
> We can — the OCR step is one swappable function behind a fixed interface. We chose a self-hosted open model so the department isn't sending enforcement evidence to a third party and isn't paying per-call at national scale.

**Q: What if the barcode isn't in the photo?**
> Font analysis needs the barcode as a scale reference, so the capture guidance tells the officer to keep it in frame. If it's missing, we fall back to a proportional estimate and flag the font check as low-confidence rather than asserting a pass or fail.

**Q: How does this handle multi-language labels?**
> Today it's English. EasyOCR supports many Indian scripts, and the extraction rules are per-field regex — adding a language is a config + model-pack change, on the roadmap.

**Q: Can it be gamed / what about adversarial packaging?**
> It's a decision-support tool for an officer, not an automated penalty system. Low confidence and any FAIL both flag "manual review recommended" — a human always makes the final call.

**Q: Is the data secure?**
> Stateless JWT auth, hashed passwords, role checks on every endpoint, images in a private store, every scan attributed to an officer with a timestamp. The ML service never touches the database.

**Q: Deployment?**
> Three processes — a JAR, a Python service, a static frontend bundle — plus a Postgres instance. No Docker required. Runs on a single mid-range server for a state office; scales horizontally for national volume.

**Q: What's genuinely done vs. planned?**
> Done: the entire portal — auth, products, scans, dashboard, filtering, PDF, roles, 20 passing tests — and the full ML pipeline wired end-to-end. Planned: model fine-tuning, mobile capture, batch mode, a rules admin UI.
