# EduSynC – APAAR ID-based Student Data Management & Verification Platform

EduSynC is a Python/FastAPI implementation of the AICTE APAAR ID platform for managing, validating, verifying, and reporting student enrolments across AICTE-approved institutions.

## Features

- **Multi-role portal**: AICTE Directorate Admin, Institution Admin, Verifier, Student
- **APAAR ID validation**: 12-digit structural checks, placeholder/trivial rejection, advisory Luhn checksum
- **Automated anomaly detection**: intake breach, supernumerary caps (NRI ≤ 5%, OCI+FN ≤ 15%, TFW ≤ 5%, PMSSS), cross-institution duplicates, same-institution duplicates, roll duplicates, missing fields, invalid dates, category/nationality inconsistencies, unsanctioned programmes
- **Tamper-evident seals**: HMAC/Ed25519-ready signed seals + QR codes
- **Secure verification**: `/verify/{apaar_id}` with role checks, consent enforcement, immutable audit logging
- **Consent management**: DPDP-aligned purpose-wise, revocable consent
- **CSV ingestion**: batch upload with row-level validation and anomaly reporting
- **Reports & certificates**: CSV/PDF exports, certificate PDFs with APAAR ID and QR
- **PWA**: Installable web app with QR scanning
- **RBAC & audit**: JWT auth, fine-grained permissions, tamper-evident audit chain

## Quick Start

### 1) Create environment
```bash
cd edusync
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
# source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Configure
Copy `.env.example` to `.env` and set:
```env
DATABASE_URL=sqlite+aiosqlite:///./edusync.db
SECRET_KEY=change-me
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
SEAL_HMAC_KEY=change-me
```

### 3) Migrate & seed
```bash
alembic upgrade head
python -m app.scripts.seed
```

### 4) Run
```bash
uvicorn app.main:app --reload
```
Open http://localhost:8000/docs for OpenAPI, http://localhost:8000 for portal.

## Tests
```bash
pytest -v
```

## API Highlights
- `POST /api/auth/login` – JWT login
- `POST /api/students/bulk` – CSV bulk upload with validation
- `GET /api/verify/{apaar_id}` – verification (consent-aware)
- `GET /api/reports/students.csv` / `GET /api/reports/anomalies.pdf`
- `POST /api/consent/grant|revoke`

## Security
- Passwords hashed with bcrypt; PINs use PBKDF2-HMAC-SHA256
- JWT access/refresh tokens with role claims
- Immutable audit log with hash chaining
- API keys/OAuth2 client credentials supported for system integrations
- No secrets in repo; use env vars

## Architecture
See `docs/architecture.md` for diagrams and component details.
