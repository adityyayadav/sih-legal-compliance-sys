# Backend Phase-wise Construction Guide — Zero to Deployment

Every step, in order. No code — just the blueprint. Refer to `Backend-Team-Context-Blueprint.md` for who owns what.

---

## Phase 0: Environment Setup & Project Init (Day 1 — All 3 Devs)

### 0.1 — Prerequisites (Everyone installs individually)
- **PostgreSQL client (psql):** For manual DB inspection — not a local server (Supabase hosts the DB).
- **Git:** Ensure all 3 have Git configured with their GitHub accounts.
- **IDE:** IntelliJ IDEA (recommended) or VS Code with Java Extension Pack.
- **Postman / Insomnia:** For manually testing APIs during development.

### 0.2 — Supabase Setup (One person does this, shares creds)
1. Go to [supabase.com](https://supabase.com), create a new project.
2. Note down the **Postgres connection string** from Project Settings → Database → Connection String (JDBC format).
   - It will look like: `jdbc:postgresql://db.xxxx.supabase.co:5432/postgres?user=postgres&password=YOUR_PASSWORD`
3. Share the connection URL and password with the team securely (don't commit it).

### 0.3 — Cloudinary Setup (One person does this, shares creds)
1. Create a free account at [cloudinary.com](https://cloudinary.com).
2. Note down: `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`.
3. Share with Team.

### 0.4 — Spring Boot Project Generation (One person — Dev 1 recommended)
1. Go to [start.spring.io](https://start.spring.io).
2. Configure:
   - **Project:** Maven
   - **Language:** Java
   - **Spring Boot:** 3.3.x (latest stable)
   - **Group:** `com.lmcompliance`
   - **Artifact:** `backend`
   - **Name:** `backend`
   - **Packaging:** Jar
   - **Java:** 21
3. Add these **Dependencies** (select all on the website):
   - Spring Web
   - Spring Data JPA
   - Spring Security
   - PostgreSQL Driver
   - Lombok
   - Spring Boot DevTools
   - Validation (Bean Validation / Hibernate Validator)
   - Spring WebFlux (for WebClient — used to call the ML service)
4. Click **Generate**, download the zip.
5. Extract inside the project repo as the `backend/` folder.

### 0.5 — application.properties Setup
Create `backend/src/main/resources/application.properties` with the following config keys (values from Supabase/Cloudinary):
- `spring.datasource.url` → Supabase JDBC URL
- `spring.datasource.username` → `postgres`
- `spring.datasource.password` → Supabase DB password
- `spring.jpa.hibernate.ddl-auto` → `update` (auto-creates tables from entities)
- `spring.jpa.show-sql` → `true` (for debugging)
- `spring.jpa.properties.hibernate.dialect` → `org.hibernate.dialect.PostgreSQLDialect`
- `server.port` → `8080`
- `jwt.secret` → a random 256-bit secret string
- `jwt.expiration-ms` → `86400000` (24 hours)
- `cloudinary.cloud-name` → from Cloudinary dashboard
- `cloudinary.api-key` → from Cloudinary dashboard
- `cloudinary.api-secret` → from Cloudinary dashboard
- `ml.service.base-url` → `http://localhost:7860/api/v1`

> **IMPORTANT:** Add `application.properties` to `.gitignore`. Commit an `application.properties.example` with placeholder values instead.

### 0.6 — Additional Maven Dependencies (pom.xml)
Beyond what Spring Initializr provides, these need to be added manually to `pom.xml`:
- **jjwt (io.jsonwebtoken):** `jjwt-api`, `jjwt-impl`, `jjwt-jackson` — for JWT token creation/parsing.
- **Cloudinary SDK:** `com.cloudinary:cloudinary-http45` — for image uploads.
- **OpenPDF:** `com.github.librepdf:openpdf` — for generating PDF compliance reports.

### 0.7 — First Run & Verify
1. Run `mvn spring-boot:run` from the `backend/` directory.
2. Expect it to start on port 8080 — Spring Security will auto-secure all endpoints (expect 401s everywhere, that's fine).
3. Check Supabase dashboard — tables should NOT exist yet (no entities defined yet).
4. If it boots without errors, commit and push as the initial backend skeleton.
5. **All 3 devs clone and verify they can boot the project locally.**

---

## Phase 1: Shared Foundation (Day 2 — Dev 1 leads, others observe)

### 1.1 — Create the Enums (shared across all modules)
Create a `common/` or `enums/` package with:
- `Role` enum: `ADMIN`, `INSPECTOR`
- `ScanStatus` enum: `PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`
- `ComplianceStatus` enum: `COMPLIANT`, `NON_COMPLIANT`, `PARTIAL`
- `RuleStatus` enum: `PASS`, `FAIL`, `WARNING`, `NOT_APPLICABLE`

### 1.2 — Create All 5 JPA Entities (Dev 1 writes, team reviews)
Even though Dev 2 "owns" the Scan entities, it is most efficient for **one person** to write all 5 entities in one go to ensure the `@ManyToOne` / `@OneToMany` relationships are consistent and bidirectional:
- `User.java` — mapped to `users` table
- `Product.java` — mapped to `products` table
- `Scan.java` — mapped to `scans` table
- `Declaration.java` — mapped to `declarations` table
- `ComplianceResult.java` — mapped to `compliance_results` table

Each entity must have:
- `@Id @GeneratedValue(strategy = GenerationType.UUID)` on the `id` field.
- `@CreationTimestamp` on `createdAt` fields.
- Proper `@ManyToOne` / `@OneToMany(mappedBy = ...)` annotations linking them.
- `@Enumerated(EnumType.STRING)` on all enum fields.
- Lombok `@Data`, `@NoArgsConstructor`, `@AllArgsConstructor`, `@Builder` to reduce boilerplate.

### 1.3 — Boot and Verify Schema Creation
1. Run the app again.
2. Check Supabase SQL editor / Table Editor — all 5 tables should now exist with correct columns and foreign keys.
3. If schema looks correct, commit and push. **All devs pull this commit — it's the shared foundation.**

### 1.4 — Create All 5 Repositories (One per entity)
Simple Spring Data JPA interfaces:
- `UserRepository extends JpaRepository<User, UUID>`
- `ProductRepository extends JpaRepository<Product, UUID>`
- `ScanRepository extends JpaRepository<Scan, UUID>`
- `DeclarationRepository extends JpaRepository<Declaration, UUID>`
- `ComplianceResultRepository extends JpaRepository<ComplianceResult, UUID>`

Place each in its owning dev's package. Commit, push, pull.

### 1.5 — Global Exception Handler
Dev 1 creates `GlobalExceptionHandler.java` in the `exception/` package:
- Catches `EntityNotFoundException` → returns `404`.
- Catches validation errors → returns `400` with field-level messages.
- Catches `AccessDeniedException` → returns `403`.
- Catches generic `Exception` → returns `500` with a safe error message.
- Returns a consistent JSON error shape: `{ "status": 4xx, "error": "...", "message": "..." }`.

**After Phase 1, the codebase has: entities, repos, enums, exception handling. All 3 devs now branch off and work in parallel.**

---

## Phase 2: Parallel Development (Days 3–7)

From this point, all 3 devs work on their own Git branches simultaneously.

---

### Phase 2A: Auth & Products (Dev 1)

#### Step 1 — JWT Utility Class
- Create `JwtUtil.java` in the `security/` package.
- It must have methods to:
  - `generateToken(username, role)` → returns a signed JWT string.
  - `extractUsername(token)` → parses the JWT claims.
  - `isTokenValid(token)` → checks expiry and signature.
- Read `jwt.secret` and `jwt.expiration-ms` from `application.properties` using `@Value`.

#### Step 2 — JWT Authentication Filter
- Create `JwtAuthFilter.java` — a `OncePerRequestFilter`.
- On every incoming request:
  1. Extract the `Authorization: Bearer <token>` header.
  2. Validate the token using `JwtUtil`.
  3. If valid, set the `SecurityContext` with the authenticated user.
  4. If invalid/missing, let the request proceed unauthenticated (Spring Security will block it if the endpoint requires auth).

#### Step 3 — Security Configuration
- Create `SecurityConfig.java`:
  - Disable CSRF (since this is a stateless REST API).
  - Set session management to `STATELESS`.
  - Permit `/api/auth/**` endpoints without authentication.
  - Require authentication for everything else.
  - Register the `JwtAuthFilter` before Spring's `UsernamePasswordAuthenticationFilter`.
  - Configure CORS to allow requests from `http://localhost:3000` (React frontend).

#### Step 4 — User Service & Controller
- `UserService.java`:
  - `register(username, email, password, role)` → hash password with BCrypt, save to DB, return the user.
  - `login(username, password)` → verify credentials, generate JWT, return token.
  - `getCurrentUser(authentication)` → return the logged-in user's profile.
- `UserController.java`:
  - `POST /api/auth/register` → calls `register()`.
  - `POST /api/auth/login` → calls `login()`, returns `{ "token": "..." }`.
  - `GET /api/users/me` → returns the current user's profile.
- Create DTOs: `RegisterRequest`, `LoginRequest`, `LoginResponse`, `UserResponse`.

#### Step 5 — Product Service & Controller
- `ProductService.java`:
  - `createProduct(name, category, brand, userId)` → save and return.
  - `getAllProducts()` → return list.
  - `getProductById(id)` → return or throw 404.
- `ProductController.java`:
  - `POST /api/products` → create product (requires auth).
  - `GET /api/products` → list products (requires auth).
  - `GET /api/products/{id}` → get single product.
- Create DTOs: `ProductRequest`, `ProductResponse`.

#### Step 6 — Test with Postman
1. Register a user → should get 201.
2. Login → should get a JWT back.
3. Use that JWT as `Bearer` token to hit `GET /api/users/me` → should get your profile.
4. Create a product → should get 201.
5. List products → should return the created product.

---

### Phase 2B: Scan Engine & ML Integration (Dev 2)

#### Step 1 — Cloudinary Configuration
- Create `CloudinaryConfig.java` in `storage/` — reads the 3 cloudinary properties from `application.properties`, creates a `Cloudinary` bean.
- Create `StorageService.java`:
  - `uploadImage(MultipartFile file)` → uploads to Cloudinary, returns the public URL string.
  - Handle upload failures gracefully (throw a custom exception).

#### Step 2 — ML Service Client
- Create `MlWebClientConfig.java` in `mlclient/` — configures a `WebClient` bean pointing at `${ml.service.base-url}`.
- Create `MlServiceApiClient.java`:
  - `analyzeImage(byte[] imageBytes, String scanId, String category)` → sends a `multipart/form-data POST` to the ML service's `/analyze` endpoint.
  - Deserializes the JSON response into a Java DTO (`MlAnalysisResponse`).
  - Handles timeouts and errors (ML service down → mark scan as `FAILED`).
- Create full DTO hierarchy in `mlclient/dto/`:
  - `MlAnalysisResponse` — top-level response.
  - `MlDeclarationDto` — one declaration entry (present, value, confidence, bbox).
  - `MlFontAnalysisDto` — one font measurement entry.
  - `MlViolationDto` — one violation entry.

#### Step 3 — Scan Service (The Core Orchestrator)
- Create `ScanService.java`:
  - `createAndProcessScan(MultipartFile image, UUID productId, UUID userId)`:
    1. Upload image to Cloudinary via `StorageService` → get `imageUrl`.
    2. Create a `Scan` entity with status `PENDING`, save to DB.
    3. Update status to `PROCESSING`.
    4. Call `MlServiceApiClient.analyzeImage(...)`.
    5. On success:
       - Parse each entry in `response.declarations` → create `Declaration` entities, save.
       - Parse each entry in `response.violations` → create `ComplianceResult` entities, save.
       - Set `scan.overallStatus` from `response.overall_compliance_status`.
       - Set `scan.status = COMPLETED`, set `processedAt`.
    6. On failure:
       - Set `scan.status = FAILED`, set `scan.errorMessage`.
    7. Save and return the scan.
  - `getScanStatus(UUID scanId)` → return `{ id, status, overallStatus }`.

#### Step 4 — Scan Controller
- `ScanController.java`:
  - `POST /api/scans` — accepts `multipart/form-data` with `file` and `productId`. Calls `ScanService.createAndProcessScan(...)`.
  - `GET /api/scans/{id}/status` — returns the current status of a scan (for frontend polling).

#### Step 5 — Test the Pipeline
1. **Without the ML service running:** Submit a scan → it should go `PENDING` → `PROCESSING` → `FAILED` with an error message like "ML service unreachable". Verify this in the DB.
2. **With the ML service running (or a mock):** Submit a scan → it should go all the way to `COMPLETED`. Check the Supabase tables — `scans`, `declarations`, and `compliance_results` should all have rows.

---

### Phase 2C: Dashboard & Reports (Dev 3)

#### Step 1 — Detailed Scan View
- Create `ReportController.java`:
  - `GET /api/scans/{id}/detailed` → Returns a rich, nested JSON:
    ```
    {
      scan: { id, status, imageUrl, processedAt, ... },
      product: { name, category, brand },
      declarations: [ { type, present, value, confidence, bbox }, ... ],
      complianceResults: [ { ruleCode, description, status, remarks }, ... ]
    }
    ```
  - This is the main endpoint the React "Scan Results" page will consume.
- Create DTOs: `DetailedScanResponse`, `DeclarationResponse`, `ComplianceResultResponse`.

#### Step 2 — Dashboard Aggregation APIs
- Create `DashboardService.java`:
  - `getOverviewStats(UUID userId)` → run aggregate queries:
    - Total scans count.
    - Count by `overallStatus` (compliant vs. non-compliant vs. partial).
    - Count of scans in last 7 days / 30 days.
    - Top 5 most frequent violations (group by `ruleCode`, order by count desc).
  - These require custom `@Query` methods in `ScanRepository` and `ComplianceResultRepository`. Dev 3 adds query methods to these Repos (coordinate with Dev 2 to avoid conflicts — or Dev 3 can create a separate read-only repository interface).
- Create `DashboardController.java`:
  - `GET /api/dashboard/stats` → returns `{ totalScans, compliant, nonCompliant, partial, recentScans, topViolations }`.
  - `GET /api/scans` → paginated list of recent scans (with basic info: id, product name, status, date). Use Spring Data's `Pageable`.

#### Step 3 — PDF Report Generation
- Create `PdfGeneratorService.java`:
  - `generateReport(UUID scanId)` → Fetches the scan + declarations + compliance results from DB, builds a PDF document using OpenPDF:
    - **Page 1:** Header with "Legal Metrology Compliance Report", scan date, product details.
    - **Table 1:** Declarations found — columns: Declaration Type | Present | Extracted Value | Confidence.
    - **Table 2:** Compliance Results — columns: Rule Code | Description | Status (PASS/FAIL/WARNING) | Remarks.
    - **Footer:** Overall compliance status.
  - Returns the PDF as a `byte[]`.
- Add to `ReportController.java`:
  - `GET /api/scans/{id}/report/pdf` → Calls `PdfGeneratorService`, returns the PDF with `Content-Type: application/pdf` and `Content-Disposition: attachment`.

#### Step 4 — Test
1. Manually insert some fake scan + declaration + compliance_result rows into Supabase.
2. Hit `GET /api/scans/{id}/detailed` → verify the nested JSON is correct.
3. Hit `GET /api/dashboard/stats` → verify aggregates.
4. Hit `GET /api/scans/{id}/report/pdf` → download and open the PDF, verify it renders correctly.

---

## Phase 3: Integration & Merge (Days 8–9)

### 3.1 — Merge All Branches
1. Dev 1 merges their branch into `main` first (Auth + Products — the foundation others depend on).
2. Dev 2 merges next (Scan Engine — may need minor adjustments if Entity fields changed).
3. Dev 3 merges last (Dashboard/Reports — purely reads data, least likely to conflict).

### 3.2 — End-to-End Smoke Test (All 3 Devs)
Run the full flow manually using Postman or the React frontend:
1. **Register** → `POST /api/auth/register`
2. **Login** → `POST /api/auth/login` → copy JWT.
3. **Create Product** → `POST /api/products` (with JWT).
4. **Submit Scan** → `POST /api/scans` (upload a real product label image, with productId).
5. **Poll Status** → `GET /api/scans/{id}/status` until `COMPLETED`.
6. **View Results** → `GET /api/scans/{id}/detailed` → verify declarations and compliance.
7. **Dashboard** → `GET /api/dashboard/stats` → verify counters incremented.
8. **Download PDF** → `GET /api/scans/{id}/report/pdf` → open, verify content.

### 3.3 — Fix Integration Bugs
Expect minor issues:
- JSON field naming mismatches (snake_case from ML vs camelCase from Spring).
- CORS issues when React frontend connects.
- Null pointer exceptions on optional fields.
Fix them together, commit.

---

## Phase 4: Hardening & Polish (Days 10–12)

### 4.1 — Input Validation
- Add `@Valid` annotations on all request DTOs.
- Validate file types (only allow `image/jpeg`, `image/png`) and file size (max 10MB) on the scan upload endpoint.
- Validate that `productId` exists before creating a scan.

### 4.2 — Error Handling Edge Cases
- ML service timeout → scan should be `FAILED` not stuck in `PROCESSING`.
- Cloudinary upload failure → scan should not be created at all (rollback).
- Duplicate email on registration → proper 409 Conflict response.

### 4.3 — Pagination & Filtering
- Add pagination to `GET /api/scans` (page, size, sort).
- Add optional filters:  `?status=COMPLETED`, `?productId=xxx`, `?from=2026-08-01&to=2026-08-27`.

### 4.4 — Role-Based Access
- Ensure `ADMIN` can see all scans, while `INSPECTOR` can only see their own.
- Ensure only `ADMIN` can register new users.

### 4.5 — Logging
- Add `@Slf4j` (Lombok) to all service classes.
- Log: incoming scan requests, ML service call duration, ML service errors, compliance verdicts.

---

## Phase 5: Frontend Integration & Demo Prep (Days 13–14)

### 5.1 — CORS Finalization
- Ensure `SecurityConfig` allows:
  - Origins: `http://localhost:3000`
  - Methods: `GET, POST, PUT, DELETE, OPTIONS`
  - Headers: `Authorization, Content-Type`
  - Exposed Headers: `Content-Disposition` (for PDF download).

### 5.2 — Coordinate with Frontend Dev
- Share the Postman collection (export and commit it as `backend/postman-collection.json`).
- Ensure the React dev knows: every request after login must include `Authorization: Bearer <token>` header.
- Agree on the JSON field naming convention (use `@JsonProperty` if needed to match what frontend expects).

### 5.3 — Coordinate with ML Dev
- Verify the ML service's `/analyze` response matches the DTOs Dev 2 built exactly.
- Test with 5–10 real product images end-to-end.
- Ensure timeout is generous enough (set `WebClient` timeout to ~30 seconds for complex images).

### 5.4 — Demo Data Seeding
- Create a `DataSeeder.java` that runs on startup (only in dev profile) and inserts:
  - 1 Admin user, 1 Inspector user.
  - 5–10 sample products across different categories.
  - Optionally a few pre-completed scans with declarations and compliance results (so dashboard has data to show).

---

## Summary Timeline

| Day | Milestone |
| :--- | :--- |
| Day 1 | Environment setup, Spring Boot project generated, DB connected, all devs can boot |
| Day 2 | Entities, Repos, Enums, Exception Handler committed — shared foundation locked |
| Days 3–5 | Parallel development: Auth + Products / Scan Engine / Dashboard & Reports |
| Days 6–7 | Individual testing within each module using Postman |
| Days 8–9 | Merge all branches, full end-to-end smoke test, fix integration bugs |
| Days 10–12 | Validation, error handling, pagination, role-based access, logging |
| Days 13–14 | CORS finalization, frontend/ML integration, demo data seeding, final testing |
