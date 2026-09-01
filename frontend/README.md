# Legal Metrology Compliance Portal — Frontend

React + TypeScript + Vite. Government-of-India portal styling (GIGW-inspired).
Consumes the Spring Boot backend in `../backend/backend`.

## Run

```bash
npm install
npm run dev            # http://localhost:3000
```

The dev server proxies `/api` and `/actuator` to `http://localhost:8080`, so run
the backend too:

```bash
cd ../backend/backend
mvn spring-boot:run "-Dspring-boot.run.profiles=dev"
```

The `dev` profile seeds demo logins:

| Login | Password | Role |
|---|---|---|
| `admin@packsure.test` | `Admin@12345` | Administrator |
| `inspector@packsure.test` | `Inspector@123` | Inspector |

## Build

```bash
npm run build          # tsc + vite build -> dist/
npm run preview
```

## Configuration

`VITE_API_BASE_URL` (in `.env`) — set only if the backend is not reachable via
the dev proxy (e.g. a deployed backend). Leave blank for local dev.

## Structure

```
src/
  lib/         api client (axios + token refresh), auth context, react-query hooks, types
  components/  layout (gov top bar / masthead / nav / footer), shared UI, RequireAuth
  pages/       Home, About, Login, Register, Dashboard, Products, Scans, NewScan,
               ScanDetail, Profile, NotFound
  styles/      global.css — the government portal design system
```

## Notes

- Auth: JWT in `localStorage`; a 401 triggers one silent refresh, else redirect to `/login`.
- Role: `ADMIN` sees all scans + department stats; `INSPECTOR` sees only their own
  (enforced by the backend; the UI just reflects it).
- Scan submission is synchronous in the prototype; the report page still polls
  while a scan is `PENDING`/`PROCESSING`.
- PDF report is fetched as a blob (needs the auth header) and saved client-side.
- This is a Smart India Hackathon prototype — not an official Government of India portal.
