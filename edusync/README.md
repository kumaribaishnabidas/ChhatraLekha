# EduSynC - APAAR ID Student Data Management & Verification Platform

EduSynC is a student data management and verification platform for AICTE-approved
institutions. It validates every enrolment as it is uploaded, detects regulatory
breaches before they reach the national registry, and issues credentials that any
employer can verify offline.

## Components

| Component | Directory | Stack |
|---|---|---|
| Web frontend | `../frontend/` | React 19, Vite 6, Tailwind CSS 4, Recharts 3, React Router 7, Vitest |
| Python backend | `app/` | FastAPI, Motor (async MongoDB), Pydantic v2, `cryptography`, `qrcode`, ReportLab |
| Android client | `../Acadentrix/` | Kotlin 2.2, Jetpack Compose, Material 3, Room |

## Quick start

### 1. The backend

```bash
cd edusync
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
# source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set the secrets:

```env
MONGODB_URL=mongodb://localhost:27017
SECRET_KEY=<at least 32 random characters>
SEAL_HMAC_KEY=<a random key>
```

> **No MongoDB server?** Leave `MONGODB_URL=` empty. The application then uses a
> built-in **in-memory MongoDB**, which is seeded automatically on start-up, so
> the whole platform is demonstrable with a single command and no external
> service.

### 2. Run it

```bash
uvicorn app.main:app --reload
```

* Portal: <http://localhost:8000>
* OpenAPI: <http://localhost:8000/docs>
* Health: <http://localhost:8000/api/health>

Sign in with `aicte.admin@edusync.gov.in` / `EduSync@2024` (development only).

### 3. The frontend

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173, proxies /api to the backend
npm run build    # production bundle in dist/, served by the backend
```

The backend serves `frontend/dist` from the same origin, so a production
deployment is a single container.

### 4. Everything at once

```bash
docker compose up --build
```

## Seeding the demo dataset

```bash
python -m app.scripts.seed --students 2219
```

The dataset is **entirely synthetic** - no real student, institution or APAAR
identifier is used. It deliberately contains one instance of every anomaly the
engine can detect, so the dashboards show a live breach rather than an empty
state.

## Tests

```bash
cd edusync && pytest -q      # 159 backend tests
cd frontend && npm test      # 25 frontend tests
```

The backend suite runs against the in-memory MongoDB, so it needs no server and
no fixtures on disk.

## The rules

| Layer | Module |
|---|---|
| APAAR identifier validation | `app/services/apaar_validator.py` |
| The ten-layer anomaly engine | `app/services/anomaly_engine.py` |
| Signed seals (legacy / HMAC / Ed25519) | `app/services/seal.py` |
| Batch CSV ingestion and validation | `app/services/csv_ingestion.py` |
| CSV and PDF reports | `app/services/csv_export.py`, `app/services/pdf.py` |
| Purpose-wise, revocable consent | `app/services/consent_policy.py` |
| The hash-chained audit trail | `app/services/audit_chain.py` |
| The explainable institution risk score | `app/services/risk_scoring.py` |

These modules are storage-agnostic: they work on plain objects, so the same
code runs against MongoDB, against the seed script and against the Android
client's Kotlin twin.

## API highlights

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/auth/login` | Authenticate and receive a JWT pair |
| `GET` | `/api/institutions` | List institutions permitted to the caller |
| `GET` | `/api/institutions/{id}/programmes` | The sanctioned capacity of a programme |
| `POST` | `/api/students` | Create an enrolment record |
| `GET` | `/api/students` | Search the authorised student register |
| `POST` | `/api/students/bulk/preview` | Validate a batch CSV without writing |
| `POST` | `/api/students/bulk/commit` | Commit the accepted rows of a batch |
| `GET` | `/api/students/{apaar_id}/qr` | The APAAR QR badge |
| `GET` | `/api/students/{apaar_id}/certificate.pdf` | A certificate carrying the APAAR ID |
| `GET` | `/api/anomalies` | The findings available to the caller |
| `GET` | `/api/dashboard/national` | The pan-India headline numbers |
| `GET` | `/api/dashboard/intake` | Live intake utilisation |
| `GET` | `/api/dashboard/compliance` | The institution compliance matrix |
| `GET` | `/api/dashboard/risk` | The explainable risk scores |
| `GET` | `/api/verify/{apaar_id}` | Verify a credential |
| `POST` | `/api/verify/scan` | Verify a credential from a scanned QR payload |
| `POST` | `/api/consent` | Grant or revoke a consent |
| `GET` | `/api/reports/students.csv` | Export an authorised student report |
| `GET` | `/api/reports/anomalies.pdf` | Export the anomaly register as PDF |

Every endpoint is documented at `/docs`, and every protected endpoint enforces
its permission **on the server** - hiding a button in React is not a security
control.

## Security

- Passwords are hashed with bcrypt; PINs use PBKDF2-HMAC-SHA256.
- JWT access and refresh tokens with role claims; API keys for machine-to-machine
  integrations.
- The APAAR ID is never used as a lookup key: equality lookups use a keyed
  HMAC token, so an index dump does not disclose the identifiers.
- The audit trail is hash-chained, and audit entries store a masked APAAR ID.
- Rate limiting on every request; a sliding window per client.
- Secrets come from the environment; production start-up refuses development
  secrets and refuses the in-memory database.
- The data model never imposes a global unique index on the APAAR ID, because
  that would prevent the registry from holding - and therefore detecting - a
  cross-institution duplicate.

See [`docs/architecture.md`](docs/architecture.md) for the full design.
