<div align="center">

<img src="docs/assets/brand/edusync-lockup.png" alt="EduSynC" height="220" />

# Acadentrix

**The APAAR ID Student Data Management &amp; Verification Platform**

*A product of **EduSynC** · Smart India Hackathon · AICTE — Academic Performance Assessment and Accreditation Registry*

[Website &amp; landing page →](https://kumaribaishnabidas.github.io/EduSynC/) · [Source code](https://github.com/kumaribaishnabidas/EduSynC) · [App documentation](Acadentrix/README.md)

</div>

---

An offline-first Android application that turns the **APAAR** identifier into a verifiable,
tamper-evident academic credential for every student enrolled in an AICTE-approved programme.

> **APAAR** — the Academic Performance Assessment and Accreditation Registry is AICTE's student
> academic passport. Every enrolled student is issued a 12-digit APAAR ID that is supposed to travel
> with them across institutions, employers and degree-awarding bodies. In practice it is issued and
> reconciled by hand, which is where the fraud starts.

---

## Branding

| | |
| --- | --- |
| **Product / app / project name** | **Acadentrix** |
| **Brand name and logo** | **EduSynC** |
| **Package / application id** | `com.acadentrix.app` |
| **Gradle project name** | `Acadentrix` |

The EduSynC logo is the artwork the team supplied, shipped verbatim — as the launcher icon
(adaptive, with a themed-monochrome layer), in the app's header, on the degree certificate and
across the website. The brand palette is sampled directly from that artwork:
navy `#14246B` / `#0F2F73`, blue `#0F3A8A` / `#1558B8`, teal `#12B886`.

Source assets live in [`docs/assets/brand/`](docs/assets/brand/).

---

## What is in this repository

```
EduSynC/
├── README.md                 ← you are here
├── .gitignore
├── .gitattributes
├── .github/workflows/        ← CI: pytest on 3.11/3.12/3.13 + container build
├── docs/                     ← the website & landing page (GitHub Pages)
│   ├── index.html
│   └── assets/brand/         ← EduSynC logo artwork
├── edusync/                  ← the Python platform (FastAPI + portal + PWA)
│   ├── app/                  ← core, models, schemas, api, services, audit, web
│   ├── tests/                ← the pytest suite
│   ├── alembic/              ← database migrations
│   ├── Dockerfile
│   └── README.md             ← run instructions
└── Acadentrix/               ← the Android application
    ├── app/                  ← Kotlin + Jetpack Compose source, unit tests, Room schema
    ├── core/                 ← the shared Kotlin module (validator, anomaly engine, seal, QR)
    ├── gradle/               ← Gradle wrapper
    ├── build.gradle.kts
    ├── settings.gradle.kts
    ├── gradlew / gradlew.bat
    ├── build.ps1 / build.cmd ← convenience launcher (pins JDK 17, sanitises PATH)
    └── README.md             ← full technical documentation
```

There are **two implementations of the same rules**, and that is deliberate:

* **`Acadentrix/`** is the offline-first Android client (Kotlin, Compose, Room).
* **`edusync/`** is the server (FastAPI, SQLAlchemy, PostgreSQL) and the web
  portal / PWA.

The APAAR validator, the anomaly engine, the seal format and the QR payload
are specified identically in both, so the phone and the server can never
disagree about whether a record is valid.

---

## The two implementations

### 1. The Python platform (`edusync/`)

```bash
cd edusync
python -m venv .venv && .venv\Scripts\activate     # Windows
pip install -r requirements.txt
cp .env.example .env                                # then edit the secrets
alembic upgrade head
python -m app.scripts.seed                          # synthetic demo dataset
uvicorn app.main:app --reload
```

* Portal: <http://localhost:8000>
* OpenAPI: <http://localhost:8000/docs>
* Sign in with `aicte.admin@edusync.gov.in` / `EduSync@2024`

What it does: multi-role JWT authentication, RBAC on every endpoint, the
ten-layer anomaly engine, batch CSV ingestion with row-level validation and
seat-impact preview, consent-aware signed verification, APAAR QR badges,
PDF certificates carrying the APAAR ID, CSV/PDF regulatory reports, an
explainable per-institution risk score, and a hash-chained audit trail.

**161 pytest tests, all passing.** See [`edusync/README.md`](edusync/README.md)
and [`edusync/docs/architecture.md`](edusync/docs/architecture.md).

### 2. The Android client (`Acadentrix/`)

Requirements: **JDK 17+**, Android SDK with **compileSdk 36**.

```powershell
cd Acadentrix
.\gradlew.bat testDebugUnitTest assembleDebug
```

or with the convenience launcher (pins JDK 17, sanitises PATH):

```powershell
cd Acadentrix
.\build.cmd testDebugUnitTest assembleDebug
```

**Current status: 135 unit tests, 135 passing, 0 failing** — and the debug APK
builds clean.

| Suite | Tests |
| --- | --- |
| `AnomalyEngineTest` | 40 |
| `SignedSealTest` | 30 |
| `CsvExportTest` | 19 |
| `QrRoundTripTest` | 13 |
| `CsvIngestionTest` | 13 |
| `ConsentPolicyTest` | 10 |
| `AccessControlTest` | 9 |
| `AuditChainTest` | 8 |
| `ApaarIdValidatorTest` | 8 |
| `SealGeneratorTest` | 6 |
| `ApaarQrPayloadTest` | 6 |
| `CredentialsTest` | 6 |
| *(core module total)* | **135** |

The `:core` Kotlin module holds the shared logic — the APAAR validator, the
anomaly engine, the signed seal, the QR encoder/decoder and the CSV
ingestion — so the app and the server cannot drift apart.

---

## The problem, in one paragraph

APAAR is issued, stored and reconciled manually. That produces four recurring failure modes — garbage
identifiers, intakes filled beyond the sanctioned ceiling, supernumerary quota abuse, and the same
APAAR enrolled at two institutions or at a programme the institution was never approved to run.
Verifiers, employers and universities have **no offline way to check any of it**. The platform closes
all four loops with a four-layer anomaly engine, a tamper-evident cryptographic seal and a scannable
QR credential.

---

## Solution at a glance

| Role | What the platform gives them |
| --- | --- |
| **AICTE Central Directorate** | Pan-India dashboard, anomaly inspector, compliance matrix, audit trail |
| **AICTE-Approved Institution** | Student register, CSV bulk intake, intake tracking, manual admission |
| **Third-Party Verifier / Employer** | Single-APAAR lookup producing a signed verification dossier + QR card |
| **Student / Degree-Awarding Body** | Personal APAAR credential card, QR badge, degree certificate |

### Ten-layer anomaly engine

| Layer | Detects |
| --- | --- |
| 1. APAAR syntactic check | Length ≠ 12, non-triviality, placeholder rejection, Luhn checksum (advisory) |
| 2. Cross-institution duplicate | One APAAR active at two institutions |
| 3. Same-institution duplicate | The same APAAR imported twice, or admitted to two of the institute's own programmes |
| 4. Duplicate roll number | Two different students sharing one institute roll number |
| 5. Intake breach | Sanctioned intake exceeded for the programme |
| 6. Supernumerary ceiling | NRI ≤ 5 %, OCI+FN ≤ 15 %, TFW ≤ 5 %, PMSSS capped per course/institute |
| 7. Category consistency | Missing foreign-national documents; quota/nationality contradictions |
| 8. Impossible dates | Unparseable, future, or enrolment before birth |
| 9. Missing mandatory fields | Name, DOB, roll number, programme, year, enrolment date, nationality |
| 10. Unsanctioned programme | Enrolment in a course the institute is not approved to run |

### Tamper-evident verification

A digital seal is derived from the enrolment facts the APAAR was issued against:

```
HMAC-SHA256 or Ed25519 over
"APAAR|{apaarId}|{institutionId}|{programId}|{academicYear}|{enrollmentDate}|{name}|{dob}|{gender}|{quota}|{nationality}|{rollNo}|{version}"
```

Change any bound field and the seal changes with it — a scanned QR badge
proves the record behind it is the record that was sealed. The wire format is
`<ALG>.<keyId>.<signature>`, so a legacy unkeyed SHA-256 seal, an HMAC seal
and an offline-verifiable Ed25519 signature all coexist without breaking the
badges already in circulation. The Android client renders the QR matrix with a
**dependency-free ISO/IEC 18004 encoder and decoder** (Reed–Solomon error
correction included) on a Compose `Canvas`; the server uses the `qrcode`
library and `reportlab` for the printed certificates.

---

## Build & verify

### The Python platform

```bash
cd edusync
pip install -r requirements.txt
alembic upgrade head
python -m app.scripts.seed
uvicorn app.main:app --reload
pytest -q          # 161 tests
```

### The Android client

Requirements: **JDK 17+**, Android SDK with **compileSdk 36**.

```powershell
cd Acadentrix
.\gradlew.bat testDebugUnitTest assembleDebug
```

or with the convenience launcher (pins JDK 17, sanitises PATH):

```powershell
cd Acadentrix
.\build.cmd testDebugUnitTest assembleDebug
```

Artifacts land in `Acadentrix/app/build/outputs/apk/debug/app-debug.apk`, with the HTML test
report at `Acadentrix/app/build/reports/tests/testDebugUnitTest/index.html`.

---

## Tech stack

**Server** — Python 3.11+ · FastAPI · SQLAlchemy 2.0 (async) · Alembic · Pydantic v2 ·
PostgreSQL (SQLite for local development) · `cryptography` (HMAC-SHA256, Ed25519) ·
`qrcode` · `reportlab` · Jinja2 · pytest.

**Client** — Kotlin 2.2.21 · Jetpack Compose (BOM 2025.09.01) · Material 3 · Room 2.8.5 (KSP) ·
Coroutines + Flow · Navigation Compose · AGP 8.13.2 / Gradle 8.14.6 · minSdk 24, targetSdk 36.

The Android app ships with a deterministic seeded dataset — 12 institutions,
30 programmes and 2,219 students including crafted anomalies — so it is fully
demonstrable offline. The server seeds the same shape of synthetic dataset
(12 institutions, 60 programme seats, ~1,900 students and 26 live anomalies)
so the portal is demonstrable on a laptop.

---

## Team

**EduSynC** — Smart India Hackathon.
