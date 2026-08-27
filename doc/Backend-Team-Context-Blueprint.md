# Spring Boot Backend — Team Context & Blueprint

This document acts as the single source of truth for the 3 backend developers. 
By strictly adhering to these package boundaries and entity definitions, the team can develop in parallel with **zero merge conflicts**.

---

## 1. Work Distribution (3 Developers)

| Developer | Role             | Owned Packages | Responsibilities |
| :--- | :--- | :--- | :--- |
| **Dev 1** | **Auth & Core Domain** | `.security`, `.user`, `.product` | Spring Security config, JWT filters, User login/register (`Users` table), Product catalog CRUD (`Products` table). |
| **Dev 2** | **Scan Engine & ML** | `.scan`, `.storage`, `.mlclient` | Cloudinary integration, triggering the ML FastAPI via `WebClient`, executing scans, parsing huge ML JSON, saving `Declarations` & `ComplianceResults`. |
| **Dev 3** | **Analytics & Reports**| `.dashboard`, `.report` | Returning nested json for completed scans, Dashboard aggregate stats (Pass/Fail ratios), Generating PDF reports using OpenPDF. |

---

## 2. Project Structure

Everyone must stick to their assigned packages. Cross-importing entities is fine, but **do not edit someone else's Controller, Service, or Repository without coordinating.**

```java
backend/src/main/java/com/lmcompliance/
├── LmComplianceApplication.java
├── security/                // Dev 1
│   ├── SecurityConfig.java
│   ├── JwtUtil.java
│   └── JwtAuthFilter.java
├── exception/               // Dev 1 (Global Error Handling)
│   └── GlobalExceptionHandler.java
├── user/                    // Dev 1
│   ├── UserController.java
│   ├── UserService.java
│   ├── UserRepository.java
│   └── User.java
├── product/                 // Dev 1
│   ├── ProductController.java
│   ├── ProductService.java
│   ├── ProductRepository.java
│   └── Product.java
├── scan/                    // Dev 2
│   ├── ScanController.java
│   ├── ScanService.java
│   ├── ScanRepository.java
│   ├── Scan.java
│   ├── Declaration.java
│   └── ComplianceResult.java
├── storage/                 // Dev 2
│   ├── CloudinaryConfig.java
│   └── StorageService.java
├── mlclient/                // Dev 2
│   ├── MlWebClientConfig.java
│   ├── MlServiceApiClient.java
│   └── dto/                 // DTOs for the FastAPI response
├── dashboard/               // Dev 3
│   ├── DashboardController.java
│   └── DashboardService.java
└── report/                  // Dev 3
    ├── ReportController.java
    └── PdfGeneratorService.java
```

---

## 3. Full Database Schema (Entities)

*Use Spring Data JPA `@Entity` to map these exactly.*

### `User` (Dev 1)
- `UUID id` (PK)
- `String username`
- `String email`
- `String password` (BCrypt)
- `Role role` (Enum: `ADMIN`, `INSPECTOR`)
- `LocalDateTime createdAt`
- **Relationships:** `@OneToMany` to `Product`, `@OneToMany` to `Scan`

### `Product` (Dev 1)
- `UUID id` (PK)
- `String name` 
- `String category`
- `String brand`
- `LocalDateTime createdAt`
- **Relationships:** `@ManyToOne` to `User` (createdBy), `@OneToMany` to `Scan`

### `Scan` (Dev 2)
- `UUID id` (PK)
- `String imageUrl` (Cloudinary URL)
- `ScanStatus status` (Enum: `PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`)
- `ComplianceStatus overallStatus` (Enum: `COMPLIANT`, `NON_COMPLIANT`, `PARTIAL`)
- `String errorMessage`
- `LocalDateTime createdAt`
- `LocalDateTime processedAt`
- **Relationships:** `@ManyToOne` to `Product`, `@ManyToOne` to `User` (scannedBy), `@OneToMany` to `Declaration`, `@OneToMany` to `ComplianceResult`

### `Declaration` (Dev 2)
- `UUID id` (PK)
- `String declarationType` (e.g., `NET_QUANTITY`, `MRP`)
- `boolean isPresent`
- `String extractedValue`
- `Double confidenceScore`
- `String boundingBox` (Storing JSON as string or using Postgres JSONB)
- **Relationships:** `@ManyToOne` to `Scan`

### `ComplianceResult` (Dev 2)
- `UUID id` (PK)
- `String ruleCode` (e.g., `RULE_6_7_NET_QUANTITY`)
- `String ruleDescription`
- `RuleStatus status` (Enum: `PASS`, `FAIL`, `WARNING`)
- `String remarks` (e.g., "Font height 3.8mm is below required 4.0mm")
- **Relationships:** `@ManyToOne` to `Scan`

---

## 4. API Endpoints Contract

### Dev 1 (Auth & Products)
- `POST /api/auth/register` - Create new user
- `POST /api/auth/login` - Authenticate, returns `{ "token": "jwt-string" }`
- `GET /api/users/me` - Get current logged-in user profile
- `POST /api/products` - Register a new product
- `GET /api/products` - List available products for dropdowns

### Dev 2 (Scan Pipeline)
- `POST /api/scans` 
  - **Type:** `multipart/form-data`
  - **Inputs:** `file`, `productId`
  - **Flow:** Uploads to Cloudinary → creates PENDING scan in DB → calls FastAPI asynchronously (or synchronously for PoC) → updates DB on return. Returns scan ID instantly to frontend.
- `GET /api/scans/{id}/status` - Polling endpoint for frontend to check if processing is done (returns state: `PROCESSING`, `COMPLETED`).

### Dev 3 (Analytics & Output)
- `GET /api/scans` - List recent scans (paginated) for the dashboard.
- `GET /api/scans/{id}/detailed` - Returns the massive nested graph of a scan: The Scan info, the embedded Product, inner arrays for `Declarations` and `ComplianceResults`. The React frontend needs this for the Results UI.
- `GET /api/dashboard/stats` - Returns aggregates: `{ totalScans: 152, passes: 90, fails: 62, topViolations: [...] }`
- `GET /api/scans/{id}/report/pdf` - Generates and downloads a compiled PDF report.

---

## 5. Avoiding Merge Conflicts (Critical Rules)
1. **The `pom.xml` Coordinator:** Whenever a new dependency is needed (jjwt, openpdf, webflux), Dev 1 adds it and warns everyone to pull. Do not edit `pom.xml` individually in parallel.
2. **DTO Layering:** Have a `dto/` package inside your respective modules for request/response payloads (e.g. `LoginRequest`, `ScanResponse`). Do not expose Entities directly in controllers!
3. **Database Initialization:** Ensure `spring.jpa.hibernate.ddl-auto=update` is set in local `application.properties` so schema changes sync cleanly into Supabase during early dev.
