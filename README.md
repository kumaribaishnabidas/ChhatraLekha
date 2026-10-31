<div align="center">

<img src="docs/assets/brand/chhatralekha-logo.png" alt="ChhatraLekha" height="220" />

# ChhatraLekha — Unified Student Academic Identity & Campus Platform for Schools and Colleges Across India

**The Unified Student Academic Identity &amp; Campus Platform for Schools and Colleges Across India**

[Website &amp; landing page →](https://kumaribaishnabidas.github.io/ChhatraLekha/) · [Source code](https://github.com/kumaribaishnabidas/ChhatraLekha) · [Backend documentation](chhatralekha/README.md) · [App documentation](android/README.md) · [iOS Architecture](docs/IOS_ARCHITECTURE_AND_ROADMAP.md)

</div>

---

> **APAAR** — the **Automated Permanent Academic Account Registry**, issued under the
> Ministry of Education's *One Nation, One Student ID* initiative. It is the student's
> lifelong academic passport across schools, higher education colleges, polytechnics,
> and universities.
>
> ChhatraLekha is an independent educational prototype. Nothing in this prototype is an official
> APAAR, AICTE, CBSE, or government registry verification.

---

## What this repository is

A unified multi-tenant platform for schools and colleges across India, connecting
academic operations, student credentials, attendance, examinations, and families:

| Part | Directory | Stack |
|---|---|---|
| Web frontend | `frontend/` | React 19, Vite 6, Tailwind CSS 4, Recharts 3, React Router 7 |
| Python backend | `chhatralekha/` | FastAPI, Motor (async MongoDB), Pydantic v2, `cryptography` |
| Android client | `android/` | Kotlin 2.2, Jetpack Compose, Material 3, Room |
| iOS client roadmap | [`docs/IOS_ARCHITECTURE_AND_ROADMAP.md`](docs/IOS_ARCHITECTURE_AND_ROADMAP.md) | Swift 6, SwiftUI, GRDB.swift, CryptoKit |

The **Connected Campus Core** unites school and college academic operations with
**Academic Record Change Impact Detection**: preview corrections, verify credentials
tamper-evidently, take attendance, publish examinations, and connect parents securely.

---

## Branding

| | |
| --- | --- |
| **Product / project name** | **ChhatraLekha** |
| **Brand name and logo** | **ChhatraLekha** |
| **Package / application id** | `com.chhatralekha.app` |
| **Gradle project name** | `chhatralekha-android` |
| **Backend package** | `chhatralekha/` |

The ChhatraLekha logo is the project's own artwork, used unmodified — as the launcher icon
(adaptive, with a themed-monochrome layer), in the app's header, on the degree certificate and
across the website. The brand palette is sampled directly from that artwork:
navy `#2F57D6` / `#16257A`, blue `#1F3FBF` / `#4169E1`, teal `#FF8A00`.

Source assets live in [`docs/assets/brand/`](docs/assets/brand/).

---

## What is in this repository

```
ChhatraLekha/
├── README.md                 ← you are here
├── .gitignore
├── .gitattributes
├── .github/workflows/        ← CI: pytest + vitest + container build
├── docker-compose.yml        ← MongoDB + the API in one command
├── render.yaml               ← the Render deployment of the backend
├── docs/                     ← the website & landing page (GitHub Pages)
│   ├── index.html
│   └── assets/brand/         ← ChhatraLekha logo artwork
├── chhatralekha/                  ← the Python backend (FastAPI + MongoDB)
│   ├── app/                  ← core, models, schemas, api, repositories, services, audit
│   ├── tests/                ← the pytest suite
│   ├── Dockerfile
│   └── docs/architecture.md  ← the full design
├── frontend/                 ← the React web application
│   ├── src/                  ← pages, components, hooks, services, utils
│   ├── public/brand/         ← ChhatraLekha logo artwork
│   ├── vercel.json           ← the Vercel deployment of the frontend
│   └── vite.config.js
└── android/                  ← the Android application
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

* **`android/`** is the offline-first Android client (Kotlin, Compose, Room).
* **`chhatralekha/`** is the server (FastAPI, MongoDB) and the web portal.

The APAAR validator, the anomaly engine, the seal format and the QR payload
are specified identically in both, so the phone and the server can never
disagree about whether a record is valid.

---

## The three components

### 1. The web frontend (`frontend/`)

React 19 + Vite + Tailwind CSS 4 + Recharts, served as a PWA.

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173, proxies /api to the backend
npm run build    # production bundle, served by the backend from the same origin
```

Dedicated pages: the AICTE Directorate dashboard, the **Institution Principal Dashboard** with review queue, the **Student Academic Wallet** with digital ID card and consent switches, institutions and their sanctioned capacity, the student register, the CSV batch uploader, **pluggable OCR document verification**, the anomaly inspector with a review workflow, the **change impact** page, the token credential verifier, the report centre, and an **interactive persona-guided tour**.

### 2. The Python backend (`chhatralekha/`)

```bash
cd chhatralekha
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp .env.example .env                              # then edit the secrets
python -m app.scripts.seed                        # synthetic demo dataset
uvicorn app.main:app --reload
```

* Portal: <http://localhost:8000>
* OpenAPI: <http://localhost:8000/docs>
* Health: <http://localhost:8000/health>

MongoDB is the store. Point `MONGODB_URL` at a real server; the demo
alternative (`ALLOW_IN_MEMORY_DB=true` with an empty URL) has to be asked for
explicitly, is never used in production, and says so in `/health` and in the
UI. The demo accounts are created by the seed script, and their password comes
from `DEMO_PASSWORD` or is generated and printed once.

What it does: multi-role JWT authentication with optional **Google sign-in**,
RBAC on every endpoint, the
ten-layer anomaly engine, the **academic record change impact detector**,
batch CSV ingestion with row-level validation and seat-impact preview,
**inter-institutional student transfer workflows** with relieving institution authorization,
**student lifecycle state management** with transition reason audit logs,
**case reviewer assignment, internal case notes, and structured dismissal reasons**,
**versioned cryptographic key rotation and JWKS endpoint** for offline verification,
consent-aware verification, **opaque expiring revocable verification tokens**,
APAAR QR badges, PDF certificates carrying the APAAR ID, CSV/PDF regulatory
reports, an explainable per-institution risk score, versioned seat policy, and
a hash-chained audit trail.

**293 pytest tests, all passing.** See [`chhatralekha/README.md`](chhatralekha/README.md)
and [`chhatralekha/docs/architecture.md`](chhatralekha/docs/architecture.md).

#### Google sign-in

The login page can also offer **Sign in with Google**, using the OAuth 2.0
authorization-code flow. The browser is sent to
`/api/auth/google`, which redirects to Google's consent screen with a random
`state` kept in a short-lived, HttpOnly cookie; the callback exchanges the
code, reads the profile, and returns the browser to
`/auth/callback#access_token=...` — the URL *fragment*, which is never sent
to a server and never lands in a log.

An account is **linked, not duplicated**: a Google identity that is already
known signs in as that account, an e-mail that already has a local account
attaches the Google identity to it, and only a genuinely new person gets a
new account with the restricted `verifier` role.

It is off until you give the backend a client of your own — see
[`chhatralekha/README.md`](chhatralekha/README.md#google-sign-in).

### 3. The Android client (`android/`)

Requirements: **JDK 17+**, Android SDK with **compileSdk 36**.

```powershell
cd android
.\gradlew.bat :core:test assembleDebug
```

or with the convenience launcher (pins JDK 17, sanitises PATH):

```powershell
cd android
.\build.cmd :core:test assembleDebug
```

**Current status: 204 unit tests, 204 passing, 0 failing** — and the debug APK
builds clean (`app-debug.apk`).

| Suite | Tests |
| --- | --- |
| `AnomalyEngineTest` | 39 |
| `SignedSealTest` | 28 |
| `CsvIngestionTest` | 21 |
| `ApaarIdValidatorTest` | 15 |
| `QrRoundTripTest` | 14 |
| `CsvExportTest` | 13 |
| `SealGeneratorTest` | 11 |
| `ConsentPolicyTest` | 10 |
| `CredentialsTest` | 10 |
| `ApaarQrPayloadTest` | 10 |
| `ChhatraLekhaApiClientTest` | 9 |
| `AuditChainTest` | 9 |
| `AccessControlTest` | 8 |
| `VoiceIntentMatcherTest` | 5 |
| `PrivacyMaskTest` | 2 |
| *(core module total)* | **204** |

The `:core` Kotlin module holds the shared logic — the APAAR validator, the
anomaly engine, the signed seal, the QR encoder/decoder and the CSV
ingestion — so the app and the server cannot drift apart.

### Running everything

```bash
docker compose up --build     # MongoDB + the API + the React frontend
```

---

## Deployment

### Architecture

| Part | Platform | Notes |
|---|---|---|
| Frontend (React 19 + Vite + Tailwind 4) | **Vercel** | Root directory `frontend/`, output `dist` |
| Backend (FastAPI + Motor) | **Render** (web service) | `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, health check `/health` |
| Database (MongoDB) | **MongoDB Atlas** | An Atlas cluster is a replica set, so multi-document transactions are available |
| Android client (`android/`) | Direct APK / Play Internal Testing | Offline-capable with Room database, pure Java runtime HTTP client (`ChhatraLekhaApiClient`), two-way sync (`SyncManager`), and optimistic concurrency (HTTP 409 conflict handling) |

The configuration files are [`render.yaml`](render.yaml) and
[`frontend/vercel.json`](frontend/vercel.json).

### 1. MongoDB Atlas

1. Create an Atlas project and a cluster. **M0 (free) is enough for the demo** —
   check the current free-tier limits on the Atlas site, because the storage
   cap and the connection limit are both low.
2. Create a **dedicated database user** with read/write on the app database
   only. Do **not** use an admin user.
3. **Network Access.** Render's free tier has no fixed outbound IP, so the
   allowlist will probably have to be `0.0.0.0/0`. That is a real trade-off:
   anybody who learns the connection string and the password can reach the
   cluster. Compensate with a long random password, a least-privilege user,
   and TLS (the `mongodb+srv://` scheme enforces it). If you move to a paid
   Render plan with static outbound IPs, restrict the allowlist to those
   instead.
4. Copy the `mongodb+srv://...` connection string. **URL-encode any special
   characters in the password** (`@` becomes `%40`, and so on) — this is the
   single most common reason a connection string fails.
5. No manual index step: the application creates every index at start-up, and
   the creation is idempotent, so it is safe on every deploy.

### 2. Render (the backend)

1. Push the repository to GitHub and create a **Web Service** from it. Render
   reads [`render.yaml`](render.yaml) automatically; the build is
   `pip install -r requirements.txt` and the start command is
   `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
2. Set the environment variables in the Render dashboard (the secrets are
   declared with `sync: false`, so they are never in the file).
3. The health check is `/health`.

### 3. Vercel (the frontend)

1. Import the repository into Vercel with **the `frontend` directory as the
   root directory**.
2. Framework **Vite**, build command `npm run build`, output directory
   `dist`. [`frontend/vercel.json`](frontend/vercel.json) adds the SPA
   rewrite, so a deep link such as `/impact` or `/verify/t/<token>` resolves
   instead of 404ing.
3. **Set `VITE_API_URL` to the Render URL of the backend** (no trailing
   slash), and build. The Vercel rewrite sends *every* path — `/api`
   included — to `index.html`, so a build with `VITE_API_URL` unset would
   receive HTML instead of JSON.

> **`VITE_*` variables are baked in at build time.** Set `VITE_API_URL`
> **before the first build**; changing it later needs a **redeploy**, not
> just a restart.

### 4. Set `FRONTEND_ORIGIN` and redeploy the backend

`FRONTEND_ORIGIN` is the Vercel URL of the frontend, e.g.
`https://chhatralekha.vercel.app`. It is what the API uses for CORS, and it is
the origin printed on a QR badge. Set it on Render and **redeploy the
backend** — the CORS list is read at start-up.

### 5. Seed the demo data (an explicit, manual step)

Seeding **never** runs on start-up against a real database. Run it from a
machine that can reach Atlas:

```bash
cd chhatralekha
MONGODB_URL='mongodb+srv://...' \
MONGODB_DATABASE=chhatralekha \
ENVIRONMENT=production \
ALLOW_PRODUCTION_SEED=true \
DEMO_PASSWORD='choose-a-demo-password' \
python -m app.scripts.seed
```

`ALLOW_PRODUCTION_SEED=true` is required when `ENVIRONMENT=production`, so a
stray call cannot wipe the live registry. **Switch it off again afterwards** —
remove the variable from the environment and from Render.

When `DEMO_PASSWORD` is empty, a password is generated and printed **once**.

### Environment variables

**Backend** (set on Render, or in `chhatralekha/.env` locally):

| Name | Required | Placeholder | Where |
|---|---|---|---|
| `MONGODB_URL` | yes | `mongodb+srv://user:pass@cluster.mongodb.net` | Render (secret) |
| `MONGODB_DATABASE` | no | `chhatralekha` | Render |
| `SECRET_KEY` | yes | `python -c "import secrets; print(secrets.token_urlsafe(48))"` | Render (secret) |
| `SEAL_HMAC_KEY` | yes | `python -c "import secrets; print(secrets.token_urlsafe(32))"` | Render (secret) |
| `MATCH_KEY` | no | falls back to `SEAL_HMAC_KEY` | Render |
| `FRONTEND_ORIGIN` | yes | `https://chhatralekha.vercel.app` | Render |
| `CORS_ORIGINS` | no | extra origins, comma separated | Render |
| `ENVIRONMENT` | yes | `production` | Render (`ENV` also works) |
| `ALLOW_IN_MEMORY_DB` | no | `false` — never `true` in production | Render |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | no | `60` | Render |
| `REFRESH_TOKEN_EXPIRE_DAYS` | no | `7` | Render |
| `VERIFICATION_TOKEN_MINUTES` | no | `60` | Render |
| `RATE_LIMIT_PER_MINUTE` | no | `120` | Render |
| `UPLOAD_MAX_SIZE_MB` | no | `10` | Render |
| `BCRYPT_ROUNDS` | no | `12` | Render |
| `DEMO_PASSWORD` | no | the seeded demo accounts' password | Render (secret) |
| `GOOGLE_CLIENT_ID` | no | `xxxx.apps.googleusercontent.com` | Render (secret) |
| `GOOGLE_CLIENT_SECRET` | no | `xxxx` | Render (secret) |
| `GOOGLE_REDIRECT_URI` | no | `https://<service>.onrender.com/api/auth/google/callback` | Render |
| `GOOGLE_DEFAULT_ROLE` | no | `verifier` | Render |
| `ALLOW_PRODUCTION_SEED` | no | `false` — only for a deliberate seed | local only |

**Frontend** (set on Vercel, or in `frontend/.env.local` locally):

| Name | Required | Placeholder | Where |
|---|---|---|---|
| `VITE_API_URL` | no | `https://chhatralekha-api.onrender.com` | Vercel (build time) |

### Smoke test checklist

```bash
# 1. The backend is up and the database is connected.
curl -s https://<service>.onrender.com/health
# expect: {"status":"ok", ..., "database":"up", "in_memory_demo_data":false, "notice":""}
```

2. Open the Vercel URL and sign in with a seeded account.
3. Go to **Change Impact**, pick a student, change a field and press
   **Preview the impact**.
4. Confirm the banner **"Preview only: nothing has been saved"** appears,
   with the findings listed underneath.
5. Press **Apply the correction**, then open **Review checklist** and resolve
   a task.
6. Issue a verification token for a student and open its QR link in a
   **private window** (so no session is carried over). Only the allowlisted
   fields may appear — the APAAR ID, the date of birth and the contact
   details must not.
7. Open the anomaly inspector — the change should not have created a
   duplicate.

### Free-tier caveats

* **Render free web services spin down** after a period of inactivity, and the
  first request afterwards can take roughly a minute while the service starts.
  Check Render's current policy. For a demo week, either use a paid
  instance, or put an uptime pinger on `/health`, and open the site a few
  minutes before you present.
* **Atlas M0** has a small storage cap and a low connection limit. It is
  ample for the synthetic demo dataset, but check the current numbers on the
  Atlas site before you rely on it.
* **Vercel Hobby** is fine for a static SPA.

### Security notes

* Rotate `SECRET_KEY` and the database password **if they are ever exposed**.
  Rotating `SECRET_KEY` invalidates every issued token.
* Never reuse the demo credentials in a real deployment, and never put a
  real password in `render.yaml`, `.env.example` or a commit.
* The in-memory database is **refused in production** — the service refuses
  to start with `ENVIRONMENT=production` and an empty `MONGODB_URL`.
* A missing or unreachable `MONGODB_URL` is a **clear startup error**; there
  is no silent fallback to an in-memory database.
* The connection string is never written to a log: it is redacted to
  `user:***@host` before it appears in an error message.
* Verification in this prototype is **against this prototype's database, not
  official APAAR or AICTE verification**.

### The Android client

The client is **offline-first with bidirectional network synchronisation capability**:
it features an in-built `ChhatraLekhaApiClient` and `SyncManager` (`com.chhatralekha.core.network`),
using standard Java runtime networking (zero external dependencies). It connects to
the FastAPI backend (`http://10.0.2.2:8000/api` for emulator, or configurable remote URL).

* **Local persistence**: Room remains the authoritative local cache, seeded with
  12 institutions and 2,219 synthetic student records so the application is 100%
  operational without network connectivity.
* **Network & offline resilience**: All API operations wrap in `NetworkResult`
  (`Success`, `OfflineFallback`, `Error`). If the backend is unreachable or drops,
  the app falls back gracefully without crashing.
* **Synchronisation & Conflict Handling**: Two-way sync pushes local admissions
  and pulls central updates. Duplicate submissions (409 Conflict) and cross-institution
  clashes are caught safely, flagged as anomalies, and never silently overwritten.
* **QR & Token Contract**: Android `ApaarQrPayload` supports both the deep-link
  token contract (`https://chhatralekha.vercel.app/verify/t/{token}`) and the canonical
  seal verification query (`/verify?apaar=...&seal=...`). Online token lookups resolve
  through `GET /api/verify/token/{token}` with public allowlisted fields only.

* *Demo* — a signed release APK shared by link or QR code.
* *Wider testing* — Firebase App Distribution, or Google Play Internal
  Testing (Play needs a one-time developer registration fee; check the
  current amount on the Play Console).

### Not yet verified

The following could **not** be tested from this repository, because they need
accounts and credentials that are deliberately not committed:

* a live Render deployment;
* a live MongoDB Atlas connection, and therefore the transaction path of the
  correction workflow against a real replica set;
* a live Vercel deployment, and therefore the built bundle behind the Vercel
  rewrite.

What **was** run: the whole pytest suite (262 tests passed), the whole Vitest suite
(61 tests passed), the frontend production build and link check, the Android core
unit and HTTP integration test suite (204 tests passed), the Android debug APK build,
and the production-safety start-up refusals.


---

## The problem, in one paragraph

APAAR is issued, stored and reconciled manually. That produces four recurring failure modes — garbage
identifiers, intakes filled beyond the sanctioned ceiling, supernumerary quota abuse, and the same
APAAR enrolled at two institutions or at a programme the institution was never approved to run.
Verifiers, employers and universities have **no offline way to check any of it**. The platform closes
all four loops with a ten-layer anomaly engine, a tamper-evident cryptographic seal and a scannable
QR credential.

---

## Solution at a glance

| Role | What the platform gives them |
| --- | --- |
| **AICTE Central Directorate** | Pan-India dashboard, anomaly inspector, compliance matrix, audit trail |
| **AICTE-Approved Institution** | Student register, CSV bulk intake, intake tracking, manual admission |
| **Third-Party Verifier / Employer** | An opaque verification token producing a signed, expiring verdict |
| **Student / Degree-Awarding Body** | Personal APAAR credential card, QR badge, degree certificate |

### The Academic Record Change Impact Detector

The headline feature. A correction to a record can leave another institution's
copy inconsistent. The detector answers that **before** anything is written:

| Rule | Fires when |
| --- | --- |
| `CIA-A` | The APAAR identifier changes — validity, duplicates, stale findings, revocations |
| `CIA-B` | The institution or programme changes — sanction, seat recalculation, roll-number clash |
| `CIA-C` | The academic year or enrolment date changes — both years recalculated, date sanity |
| `CIA-D` | The quota bucket or nationality changes — the supernumerary ceilings, category consistency |
| `CIA-E` | A seat count moves — enrolment against the sanctioned intake, per programme, year and category |
| `CIA-F` | A sealed field changes — the issued tokens and credentials are out of date |

A cross-institution identifier collision is reported as a **potential conflict
for review** — never as a conclusion, and never as "fraud". A linked record is
never modified: the dependent work becomes a checklist for an authorised
reviewer, and the previous version of the record is always preserved.

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

The ceilings are **versioned policy configuration**, stored in the
`policy_rules` collection, not hard-coded in the engine.

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
**dependency-free ISO/IEC 18004 encoder and decoder** (Reed-Solomon error
correction included) on a Compose `Canvas`; the server uses the `qrcode`
library and `reportlab` for the printed certificates.

### Opaque verification tokens

A public check must not put the APAAR ID in a URL, so a badge carries a
**token**: high-entropy, expiring, revocable, and stored only as a SHA-256
hash. The public answer is an allowlist — the record status, the institution,
the programme, the academic year, the issue date and the verdict. It never
contains the APAAR ID, the date of birth, contact details or the underlying
document.

---

## Build & verify

### The Python platform

```bash
cd chhatralekha
pip install -r requirements.txt
cp .env.example .env            # then edit the secrets
python -m app.scripts.seed
python -m app.scripts.check_prod_settings # verify 12/12 production safety checks
uvicorn app.main:app --reload
pytest -q                       # 305 passed across 33 test suites
```

### The web frontend

```bash
cd frontend
npm install
npm test                        # 68 passed (including 7 design system lint tests and 7 student portal component tests)
npm run i18n:check              # 13 locales, 423 keys each
npm run check:links             # verified 25 internal routes (34 configured application routes)
npm run build                   # route-level code splitting
```

### The Android client

Requirements: **JDK 17+**, Android SDK with **compileSdk 36**.

```powershell
cd android
.\gradlew.bat :core:test assembleDebug
```

or with the convenience launcher (pins JDK 17, sanitises PATH):

```powershell
cd android
.\build.cmd :core:test assembleDebug   # 204 passed unit & integration tests, builds app-debug.apk
```


Artifacts land in `android/app/build/outputs/apk/debug/app-debug.apk`, with the HTML test
report at `android/core/build/reports/tests/test/index.html`.

---

## Themes, languages and voice

### Appearance

The web portal supports **Light**, **Dark** and **System** appearance. The
choice is kept locally, follows operating-system changes in System mode, and
is applied before React loads to prevent a flash of the wrong palette. Android
has the same three choices in **Settings**, persisted with Jetpack DataStore.

### Languages

The web registry contains English (`en`), Hindi (`hi`), Bengali (`bn`), Tamil
(`ta`), Telugu (`te`), Marathi (`mr`) and Urdu (`ur`, RTL), with Tier 2
registry entries for Gujarati, Kannada, Malayalam, Punjabi, Odia and Assamese.
Indic fonts are self-hosted and loaded on demand; no external font request is
made. Android supplies values folders for the Tier 1 languages plus Urdu and
uses Android's per-app language setting on Android 13+ (and AppCompat on older
versions).

**Every non-English locale is Beta and draft, needs native-speaker review.**
The current structural coverage and review checklist are in
[`docs/TRANSLATIONS.md`](docs/TRANSLATIONS.md). Add a language by adding its
locale JSON and one registry entry, then run:

```powershell
cd frontend
npm run i18n:check
```

The check fails for missing/extra translation keys or mismatched
`{{placeholders}}`.

### Voice (optional)

Voice is a deterministic convenience feature, **not a chatbot**. In browsers
that expose the Web Speech API it can recognize a fixed catalogue of navigation,
statistics, review-task and theme commands, and read fixed templates based on
structured API data. It cannot apply corrections, dismiss tasks, revoke
tokens, or perform any other state-changing action. APAAR IDs are masked before
display or read-aloud, and audio is never recorded, stored or sent to the
ChhatraLekha backend.

Voice input is opt-in. A translated privacy notice explains that some browsers
process microphone audio through the browser vendor's cloud speech service.
Browser recognition support varies (Chromium browsers commonly support it;
Firefox commonly does not); unsupported browsers keep all typed workflows and
show a clear fallback notice. Android uses the device `SpeechRecognizer` and
TTS language data when available, but requires device testing for the selected
vendor/language.

## Tech stack

**Web frontend** — React 19 · Vite 6 · Tailwind CSS 4 · Recharts 3 · React Router 7 ·
Axios · Vitest + React Testing Library.

**Server** — Python 3.11+ · FastAPI · Motor (async MongoDB driver) · Pydantic v2 ·
`cryptography` (HMAC-SHA256, Ed25519) · `qrcode` · ReportLab · pytest.

**Client** — Kotlin 2.2.21 · Jetpack Compose (BOM 2025.09.01) · Material 3 · Room 2.8.5 (KSP) ·
Coroutines + Flow · Navigation Compose · AGP 8.13.2 / Gradle 8.14.6 · minSdk 24, targetSdk 36.

The Android app ships with a deterministic seeded dataset — 12 institutions,
30 programmes and 2,219 students including crafted anomalies — so it is fully
demonstrable offline. The server seeds the same shape of synthetic dataset
(12 institutions, 60 programme seats, ~1,900 students and 24 live anomalies)
so the portal is demonstrable on a laptop.

---

## Project

ChhatraLekha is an open academic-identity prototype. Questions and feedback are welcome through the contact page.
