# Backend Progress Checklist — What's Done vs. What's Left

Audit date: **2026-09-01**. Compared against `Backend-Phasewise-Guide.md`, `Backend-Team-Context-Blueprint.md`, and `Legal-Metrology-Final-Implementation-Plan.md`.

Code lives at `backend/backend/` (double-nested), base package `com.packsure.backend`
(blueprint said `com.lmcompliance` — cosmetic, don't rewrite it, just stay consistent).

Legend: ✅ done · 🟡 partial / needs fixing · ❌ not started · ⏭️ ML teammate's job, skip

---

## Cross-cutting blockers (fix these first, they block everything else)

| # | Item | State | Notes |
|---|---|---|---|
| B1 | `JAVA_HOME` on this machine points to a missing JDK 11 | ✅ | Fixed via `setx JAVA_HOME "C:\Program Files\Eclipse Adoptium\jdk-21.0.12.101-hotspot"` (2026-09-01). Reopen terminals to pick it up. |
| B2 | No `.env` file → app cannot boot against Supabase | 🟡 | `.env.example` committed. **`dev` profile (H2 in-memory) added** so the app boots with zero external services — use it for all endpoint work. Real `.env` with Supabase + Cloudinary creds still needed for the production path / Cloudinary + real ML testing. |
| B3 | No env template committed | ✅ | `backend/backend/.env.example` + `backend/backend/README.md` added. (We keep `application.properties` committed with env-var indirection instead of the guide's committed-`.properties.example` approach — cleaner, same effect.) |
| B4 | `mvn` must be run from `backend/backend/`, not `backend/` | 🟡 | The phase guide says `cd backend/` — our layout is one level deeper. |

---

## Phase 0 — Environment Setup & Project Init

| Step | Item | State | Notes |
|---|---|---|---|
| 0.4 | Spring Boot project generated | ✅ | **Deviation:** Spring Boot **4.1.1** (guide said 3.3.x). Works, but blueprint code snippets may use older APIs. Also both `spring-boot-starter-webmvc` **and** `spring-boot-starter-webflux` are on the classpath — decide if WebFlux stays (see 2B-2). |
| 0.5 | `application.properties` with all config keys | ✅ | Present, uses `${ENV_VAR}` indirection + `spring.config.import` of `.env`. All required keys present (datasource, jpa, jwt, cloudinary, ml.service.base-url, multipart limits). |
| 0.5 | `.gitignore` excludes secrets | ✅ | `.env` and `application.properties`-style secrets handled via env indirection; `.env` is gitignored. |
| 0.5 | `application.properties.example` committed | ❌ | **B3.** |
| 0.6 | jjwt dependency | 🟡 | Present but **0.11.5** (old, uses deprecated `parserBuilder()` / `setSigningKey()`). Consider bumping to `0.12.6` and updating `JwtService`. Not urgent. |
| 0.6 | Cloudinary SDK (`cloudinary-http45`) | ✅ | v1.38.0. |
| 0.6 | OpenPDF | ✅ | v1.3.39 present but **unused** (no report code yet — Phase 2C). |
| 0.6 | actuator | ✅ | Added; `/actuator/health` is permit-all in security config. |
| 0.7 | Boots on :8080, tables auto-created | ✅ | Verified 2026-09-01 with the `dev` profile: `Started BackendApplication`, Hibernate created all 6 tables, `/actuator/health` = UP, register/login/product endpoints work, protected routes return 401 without a token. Supabase run still pending real creds. |

| 0.7 | `mvn clean package` / `mvn test` works offline | ✅ | `BackendApplicationTests` now uses `@ActiveProfiles("test")` + `src/test/resources/application-test.properties` (H2). Previously it needed a live DB and failed the build. |

### Bugs from the 2026-09-01 smoke test
- ~~Duplicate registration → HTTP 500 (want 409)~~ — **fixed in step 2** (now 409).
- ~~Wrong password on login → HTTP 500 (want 401)~~ — **fixed in step 2** (now 401).
- ~~`GET /api/users/me` → HTTP 500~~ — **fixed in step 2** (now 404; real endpoint still to build in step 3).
- `POST /api/products` response has `createdAt: null` (entity mapped to DTO before the tx flush sets `@CreationTimestamp`; correct on `GET`). Minor — still open.
- Startup warnings: `DaoAuthenticationProvider` + `UserDetailsService` bean redundancy warning; `spring.jpa.open-in-view` not set explicitly. Cosmetic.

---

## Phase 1 — Shared Foundation

| Step | Item | State | Notes |
|---|---|---|---|
| 1.1 | 4 enums (`Role`, `ScanStatus`, `ComplianceStatus`, `RuleStatus`) | ✅ | In `common/`. All values match spec. |
| 1.2 | 5 JPA entities | ✅ | `User`, `Product`, `Scan`, `Declaration`, `ComplianceResult` all present + a bonus `RefreshToken`. Relationships, `@GeneratedValue(UUID)`, `@CreationTimestamp`, `@Enumerated(STRING)` all correct. |
| 1.2 | `Scan` extra columns from Impl-Plan §4 | 🟡 | Impl-Plan §4 lists `ocr_raw_text` and `compliance_score` on `scans`. Entity has neither. Add `String ocrRawText` (TEXT) + `Double complianceScore` if we want to store them. |
| 1.2 | `rules` table / `Rule` entity (Impl-Plan §4) | ❌ | Optional. Rules currently live only in the ML service's `rules_db.py`. Only needed if we want a `GET /api/rules` passthrough or DB-backed rules later. Low priority for demo. |
| 1.3 | Schema auto-created in Supabase, verified | ❌ | Blocked by B2. |
| 1.4 | 5 repositories | ✅ | All present + `RefreshTokenRepository`. No custom query methods yet (needed in Phase 2C). |
| 1.5 | `GlobalExceptionHandler` | ✅ | Rewritten 2026-09-01. `ErrorResponse` body `{timestamp,status,error,message,fieldErrors?}`. Handlers: 404 (`ResourceNotFoundException` + unknown route), 409 (`DuplicateResourceException`), 400 (`MethodArgumentNotValidException` w/ field errors, `ConstraintViolationException`, type mismatch, `IllegalArgumentException`), 401 (`AuthenticationException`), 403 (`AccessDeniedException`), 413 (upload too large), 500 (generic — logged, safe message). Services throw the new typed exceptions. Verified with an 8-case smoke test. |

---

## Phase 2A — Auth & Products (Dev 1)

| Step | Item | State | Notes |
|---|---|---|---|
| 1 | JWT utility | ✅ | `auth/service/JwtService.java` — `generateToken`, `extractUsername`, `isTokenValid`, reads `jwt.secret` / `jwt.expiration-ms`. Also full refresh-token flow (persisted in DB). Deprecated jjwt API (see 0.6). |
| 2 | `JwtAuthFilter` (OncePerRequestFilter) | ✅ | Works. **Minor:** swallows exceptions with `System.out.println` — switch to `@Slf4j` / `log.debug` (Phase 4.5). |
| 3 | `SecurityConfig` | ✅ | CSRF off, STATELESS, `/api/auth/**` + `/actuator/health` permit-all, filter registered, CORS for `http://localhost:3000`. **Missing for later:** exposed header `Content-Disposition` (Phase 5.1, needed for PDF download), explicit method list. |
| 4 | Register endpoint | 🟡 | `POST /api/auth/register` works BUT **`RegisterRequest.role` is caller-controlled + endpoint is public → anyone can register themselves as `ADMIN`.** Force role to `INSPECTOR` on the public route (or lock the route to `ADMIN` per Phase 4.4). |
| 4 | Login endpoint | ✅ | `POST /api/auth/login` returns `{token, refreshToken, username, email, role}`. |
| 4 | `GET /api/users/me` | ❌ | **No `UserController`, no `UserService`, no `UserResponse` DTO.** This endpoint is in the contract and Phase 3.2 smoke test. Needs building. |
| 5 | Product service + controller | ✅ | `POST /api/products`, `GET /api/products`, `GET /api/products/{id}` all present, DTOs in place, `createdBy` wired from the JWT principal. |
| 6 | Postman verification of the 2A flow | ❌ | Pending (blocked by B2). |

---

## Phase 2B — Scan Engine & ML Integration (Dev 2)

| Step | Item | State | Notes |
|---|---|---|---|
| 1 | Cloudinary config + upload service | 🟡 | `config/CloudinaryConfig` + `scan/service/CloudinaryService` exist and work. Upload failure throws a raw `RuntimeException` — give it a dedicated exception + a `GlobalExceptionHandler` mapping (Phase 4.2: Cloudinary failure → scan not created). |
| 2 | ML client | 🟡 | `scan/service/MlServiceClient` exists but: (a) uses `new RestTemplate()` with **no connect/read timeout** → a hung ML call blocks the request thread forever; (b) blueprint/Impl-Plan wants **WebClient**; (c) it POSTs JSON `{imageUrl}` — **the agreed contract (Impl-Plan §5) is `multipart/form-data` with `images[]` + `scan_id` + `category`**; (d) no `MlWebClientConfig`. |
| 2 | ML response DTOs | 🟡 | `MlScanResponse` **does not match Impl-Plan §5.** Real shape: `scan_id`, `status`, `processed_at`, `declarations` is a **map keyed by type** (not a list), plus `font_analysis[]`, `violations[]`, `overall_compliance_status`, `confidence_flags`. Current DTO has `overallStatus` + `declarations[]` + `ruleResults[]`. Needs a rewrite: `MlAnalysisResponse`, `MlDeclarationDto`, `MlFontAnalysisDto`, `MlViolationDto`. **Coordinate the final contract with the ML teammate before rewriting** (their `/analyze` isn't built yet — `ml-service/app/main.py` is empty). |
| 3 | `ScanService` orchestrator | 🟡 | Exists and does upload → save → ML call → map → COMPLETED/FAILED. Gaps: no distinct `PENDING`-then-`PROCESSING` write; whole thing runs in **one `@Transactional`** so the DB connection is held across the Cloudinary upload + full ML call (pool exhaustion risk); `ComplianceStatus.valueOf(...)` / `RuleStatus.valueOf(...)` **throw on any unexpected/null string** from ML and fail the whole scan; mapping must be rewritten when the DTO changes (2B-2). |
| 3 | `getScanStatus(id)` | ❌ | Not implemented. |
| 4 | `POST /api/scans` | 🟡 | Implemented as **`POST /api/scans/analyze`** with param **`image`** (contract says path `POST /api/scans`, part name `file`). Align with the contract so the frontend/smoke test matches. |
| 4 | `GET /api/scans/{id}/status` | ❌ | Not implemented — the frontend polling endpoint. |
| 5 | Pipeline test (ML down → FAILED; ML up → COMPLETED) | ❌ | Pending. "ML down → FAILED" path should already mostly work once B2 is resolved. |

---

## Phase 2C — Dashboard & Reports (Dev 3) — **entirely not started**

| Step | Item | State | Notes |
|---|---|---|---|
| 1 | `GET /api/scans/{id}/detailed` (nested scan+product+declarations+results) | ❌ | No `report/` package. Need `DetailedScanResponse`, `DeclarationResponse`, `ComplianceResultResponse` DTOs. |
| 2 | `DashboardService` + `GET /api/dashboard/stats` | ❌ | No `dashboard/` package. Needs custom `@Query` methods on `ScanRepository` / `ComplianceResultRepository` (total, count-by-status, last 7/30 days, top-5 violations by `ruleCode`). |
| 2 | `GET /api/scans` (paginated list) | ❌ | Needs `Pageable` + a summary DTO (id, product name, status, date). |
| 3 | `PdfGeneratorService` + `GET /api/scans/{id}/report/pdf` | ❌ | OpenPDF dependency already present. Returns `application/pdf` + `Content-Disposition: attachment`. |
| 4 | Test with seeded rows | ❌ | Pending. |

---

## Phase 3 — Integration & Merge

| Item | State | Notes |
|---|---|---|
| Feature branches per dev | ❌ | Only `main` exists. All work so far is committed straight to `main`. |
| End-to-end smoke test (register → login → product → scan → poll → detailed → dashboard → PDF) | ❌ | Can't run until 2A `users/me`, 2B `status`, and 2C endpoints exist + B2 resolved. |
| snake_case (ML) vs camelCase (Spring) mapping | 🟡 | Will bite when the real ML DTO lands — plan for `@JsonProperty` / `@JsonNaming(SnakeCaseStrategy)` on the ML DTOs. |

---

## Phase 4 — Hardening & Polish

| Step | Item | State | Notes |
|---|---|---|---|
| 4.1 | `@Valid` on request DTOs | 🟡 | Present on auth + product DTOs. **Missing:** file type check (`image/jpeg`, `image/png`) on scan upload; `productId` existence check before scan (service does look it up — just needs a clean 400/404). Size limit (10MB) is set in `application.properties` ✅. |
| 4.2 | Error-handling edge cases | ❌ | ML timeout → `FAILED` not stuck (needs real timeout config, 2B-2); Cloudinary failure → rollback / no scan row; duplicate email → **409** (currently 500). |
| 4.3 | Pagination & filtering on `GET /api/scans` | ❌ | Endpoint doesn't exist yet (2C). Add `?status=`, `?productId=`, `?from=&to=` when built. |
| 4.4 | Role-based access | ❌ | `@EnableMethodSecurity` is on but **no `@PreAuthorize` anywhere**. Need: only `ADMIN` registers users; `ADMIN` sees all scans, `INSPECTOR` sees own. |
| 4.5 | Logging (`@Slf4j`) | ❌ | No logging in any service. Add scan-request / ML-duration / ML-error / verdict logs. |

---

## Phase 5 — Frontend Integration & Demo Prep

| Step | Item | State | Notes |
|---|---|---|---|
| 5.1 | CORS finalization | 🟡 | Origin `localhost:3000` ✅. **Missing:** `exposedHeaders("Content-Disposition")`, explicit methods `GET,POST,PUT,DELETE,OPTIONS`. |
| 5.2 | `backend/postman-collection.json` committed | ❌ | Not present. |
| 5.3 | ML contract alignment + 30s timeout | ❌ | Depends on ML teammate; DTO rewrite (2B-2) + WebClient timeout. |
| 5.4 | `DataSeeder` (dev profile: admin + inspector + sample products + sample scans) | ❌ | Not present. Big win for demo — dashboard needs data. |

---

## Recommended execution order (step by step)

1. **B1 + B2 + B3 + 0.7** — fix `JAVA_HOME`, get real Supabase + Cloudinary creds into `.env`, commit `application.properties.example`, confirm the app boots on :8080 and Hibernate creates all 6 tables in Supabase.
2. **1.5** — rewrite `GlobalExceptionHandler` (404 / 400 / 401 / 403 / 409 / 500, consistent JSON shape). Everything downstream depends on sane error responses.
3. **2A-4** — build `UserController` + `UserService` + `UserResponse` → `GET /api/users/me`; close the ADMIN self-registration hole.
4. **2B-4 + 2B-3** — rename to `POST /api/scans` (part `file`), add `GET /api/scans/{id}/status`, split the transaction (PENDING save → process outside tx → final update), make the enum mapping defensive.
5. **2B-2** — agree the `/analyze` contract with the ML teammate, then rewrite `MlServiceClient` (WebClient + 30s timeout + multipart) and the ML DTOs to match Impl-Plan §5.
6. **2C** — `GET /api/scans/{id}/detailed`, `GET /api/scans` (paginated), `GET /api/dashboard/stats` (+ repo `@Query` methods), `GET /api/scans/{id}/report/pdf` (OpenPDF).
7. **Phase 4** — validation (file type, productId), role-based access (`@PreAuthorize`), `@Slf4j` logging, Cloudinary-failure rollback.
8. **Phase 5** — CORS exposed headers, `DataSeeder` (dev profile), export `postman-collection.json`, end-to-end smoke test with a mock ML service.
9. **Phase 3** — adopt the per-dev branch workflow going forward (optional now that a lot is already on `main`).
