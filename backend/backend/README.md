# Backend — Legal Metrology Compliance

Spring Boot 4.1.1 · Java 21 · Maven · PostgreSQL (Supabase) · Cloudinary

## Prerequisites

- **JDK 21** on `JAVA_HOME`. On the current dev machine the variable points at a
  missing JDK 11 — fix it once (PowerShell, then reopen the terminal):

  ```powershell
  setx JAVA_HOME "C:\Program Files\Eclipse Adoptium\jdk-21.0.12.101-hotspot"
  ```

- Maven 3.9+ (`mvn -version`) or use the bundled `./mvnw`.

## Run — two options

### A) `dev` profile — no Supabase/Cloudinary needed (fastest)

In-memory H2 database, dummy external creds. Data is wiped on restart.
Cloudinary uploads and real ML calls fail at call time — fine for auth /
product / dashboard / report work.

```bash
mvn spring-boot:run "-Dspring-boot.run.profiles=dev"
```

On an empty DB the `dev` profile seeds demo data (users, products, scans):

| Login | Password | Role |
|---|---|---|
| `admin@packsure.test` | `Admin@12345` | ADMIN |
| `inspector@packsure.test` | `Inspector@123` | INSPECTOR |

### B) Real services (Supabase + Cloudinary)

Config keys in `src/main/resources/application.properties` resolve from env
vars loaded from a local `.env` via `spring.config.import`. `application.properties`
is **committed** (no secrets); `.env` is **gitignored**.

1. `copy .env.example .env`
2. Fill in real Supabase + Cloudinary values. `JWT_*` and `ML_SERVICE_URL`
   defaults work as-is.
3. Run from **this folder** so Spring finds `.env`:

```bash
mvn spring-boot:run
```

### Either way

- Starts on `http://localhost:8080`.
- Spring Security secures everything except `/api/auth/**` and
  `/actuator/health` — 401s elsewhere without a token are expected.
- On first boot Hibernate creates the tables: `users`, `products`, `scans`,
  `declarations`, `compliance_results`, `refresh_tokens`.

## Test

```bash
mvn test
```

Tests run against H2 (the `test` profile, `src/test/resources/application-test.properties`) —
no external services needed.

## Build

```bash
mvn clean package
```
