# EduSynC - the Python backend

The server of the **EduSynC** platform. It holds
the registry, runs the validation and the anomaly rules, and issues the
credentials that the web frontend and the Android client consume.

| Layer | Package |
|---|---|
| Configuration | `app.core.config` |
| Persistence | `app.core.database` (Motor, async MongoDB) |
| Security | `app.core.security` (bcrypt, PBKDF2, JWT, API keys) |
| Access control | `app.core.rbac` |
| Documents | `app.models.documents` |
| Rules | `app.services` |
| API | `app.api` |
| Audit | `app.audit.writer` |

> **Verification is against this prototype's database. It is not official APAAR
> or AICTE verification.**

---

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
FRONTEND_ORIGIN=http://localhost:5173
```

> **No MongoDB server?** Leave `MONGODB_URL` empty **and** set
> `ALLOW_IN_MEMORY_DB=true`. The application then uses a throwaway in-memory
> database, logs a loud warning, shows a "demo data, not persisted" notice in
> `/health` and in the UI, and refuses to start in production. A missing or
> unreachable `MONGODB_URL` is otherwise a **clear error**, never a silent
> downgrade.

### 2. Seed the demo data

```bash
python -m app.scripts.seed
```

The dataset is **entirely synthetic** - no real student, institution or APAAR
identifier is used. It contains one instance of every anomaly the engine can
detect, plus the four walk-through scenarios of the change impact detector.

The demo accounts are:

| E-mail | Role |
|---|---|
| `aicte.admin@edusync.gov.in` | AICTE Directorate |
| `principal@vidyavikas.edu.in` | Institution admin (INST-0421) |
| `principal@bhartiya.edu.in` | Institution admin (INST-0422) |
| `verifier@acme-corp.com` | Verifier |
| `student@vidyavikas.edu.in` | Student |

Their password comes from `DEMO_PASSWORD`. When that is empty, the seed script
generates one and **prints it once** - it is never stored in the repository and
never written to a log.

### 3. Run it

```bash
uvicorn app.main:app --reload
```

* Portal: <http://localhost:8000>
* OpenAPI: <http://localhost:8000/docs>
* Health: <http://localhost:8000/health>

---

## The headline feature: the change impact detector

A correction to a student record can make other records inconsistent. The
detector answers that question **before** anything is written.

```
POST /api/students/{record_id}/correction-preview   ->  nothing is written
POST /api/students/{record_id}/corrections          ->  the correction, with a checklist
GET  /api/impacts                                     ->  the assessments
GET  /api/review-tasks                                ->  the checklist
PATCH /api/review-tasks/{task_id}                     ->  the reviewer's decision
GET  /api/students/{record_id}/versions               ->  the version timeline
```

The rules are deterministic. No model decides whether a record is valid.

| Rule | Fires when |
|---|---|
| `CIA-A` | The APAAR identifier changes - validity, duplicates, stale findings, revocations |
| `CIA-B` | The institution or programme changes - sanction, seat recalculation, roll-number clash |
| `CIA-C` | The academic year or enrolment date changes - both years recalculated, date sanity |
| `CIA-D` | The quota bucket or nationality changes - the supernumerary ceilings, category consistency |
| `CIA-E` | A seat count moves - enrolment against the sanctioned intake, per programme, year and category |
| `CIA-F` | A sealed field changes - the issued tokens and credentials are out of date |

Two invariants hold throughout:

* **A linked record is never modified.** A dependent fix is a separate
  authorised action that writes its own audit entry.
* **A half-applied correction is never left silently.** The operation is
  recorded in `operation_status` before it starts, so a crash leaves a visible,
  recoverable state.

The preview requires `expected_version` when it is applied. If the record moved
in the meantime, the correction is refused with **409** rather than
overwriting a change the reviewer did not see.

---

## Opaque verification tokens

A public check must not put the APAAR ID in a URL. A token is a
high-entropy, expiring, revocable handle:

```
POST /api/verification-tokens            ->  the plaintext, shown exactly once
GET  /api/verify/token/{token}           ->  public, allowlist only
POST /api/verification-tokens/{id}/revoke
```

Only the SHA-256 hash of the token is stored, so a dump of the collection
cannot be replayed. The public answer contains the record status, the
institution, the programme, the academic year, the issue date and the
verdict - **never** the APAAR ID, the date of birth, contact details or the
underlying document.

The QR badges and the PDF certificates carry

```
{FRONTEND_ORIGIN}/verify/t/{token}
```

- the opaque token, on **this deployment's own origin**, never the raw APAAR
ID and never an official government service. The portal resolves it at
`/verify/t/:token` through the public endpoint above.

The older `GET /api/verify/{apaar_id}` route still exists, but it requires the
`verify_credential` permission and every call is audited.

## Google sign-in

The portal can sign a user in with their Google account, using the standard
OAuth 2.0 **authorization code** flow:

```
browser  ->  /api/auth/google          ->  accounts.google.com
          ->  /api/auth/google/callback ->  exchanges the code, reads the
                                               profile, issues the JWT pair
          ->  {FRONTEND_ORIGIN}/auth/callback#access_token=...
```

The tokens travel in the URL **fragment**, which is never sent to a server
and never lands in a log. A random `state` is kept in a short-lived, HttpOnly
cookie and compared on the way back, so a third party cannot feed the
callback a code of their own.

**To switch it on**

1. In the [Google Cloud console](https://console.cloud.google.com/), create a
   project and enable the **Google Identity Services** API.
2. Create an **OAuth client ID** of the type *Web application*.
3. Add the authorised redirect URI, which must match exactly:
   * local: `http://localhost:8000/api/auth/google/callback`
   * deployed: `https://<your-render-service>.onrender.com/api/auth/google/callback`
4. Set the credentials:

   ```env
   GOOGLE_CLIENT_ID=xxxx.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=xxxx
   # Optional, when the backend sits behind a proxy that rewrites the host.
   GOOGLE_REDIRECT_URI=https://<your-render-service>.onrender.com/api/auth/google/callback
   # The role given to a first-time Google sign-in.
   GOOGLE_DEFAULT_ROLE=verifier
   ```

   When the id and the secret are both present, the portal shows the
   **Sign in with Google** button; when they are not, the button is hidden and
   the endpoint answers `503` with an explanation.

**How an account is resolved**

| Situation | What happens |
|---|---|
| The Google identity is already known | That account is signed in. |
| The e-mail already has a local account | The Google identity is **linked** to it - no second account, and the existing role and institution are kept. |
| Neither | A new account is created with `GOOGLE_DEFAULT_ROLE` (the restricted `verifier` role by default) and no usable password. |

A Google-only account can never be signed into with a password: its stored
`password_hash` is not a valid bcrypt hash, so no password can match it.

---

## The rules

| Layer | Module |
|---|---|
| APAAR identifier validation | `app/services/apaar_validator.py` |
| The ten-layer anomaly engine | `app/services/anomaly_engine.py` |
| The change impact engine | `app/services/impact_engine.py` |
| The versioned seat policy | `app/services/policy.py` |
| Signed seals (legacy / HMAC / Ed25519) | `app/services/seal.py` |
| Batch CSV ingestion and validation | `app/services/csv_ingestion.py` |
| CSV and PDF reports | `app/services/csv_export.py`, `app/services/pdf.py` |
| Purpose-wise, revocable consent | `app/services/consent_policy.py` |
| The hash-chained audit trail | `app/services/audit_chain.py` |
| The explainable institution risk score | `app/services/risk_scoring.py` |

These modules are storage-agnostic: they work on plain objects, so the same
code runs against MongoDB, against the seed script and against the Android
client's Kotlin twin.

The supernumerary ceilings are **policy, not code**. The active document in
the `policy_rules` collection describes one version of the rules; the built-in
fallback is used when no document is published, and a category the policy does
not define is reported as `review_only` rather than guessed at.

---

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
| `GET` | `/api/students/{apaar_id}/qr` | The APAAR QR badge (carries a token) |
| `GET` | `/api/students/{apaar_id}/certificate.pdf` | A certificate carrying the APAAR ID |
| `GET` | `/api/anomalies` | The findings available to the caller |
| `GET` | `/api/dashboard/national` | The pan-India headline numbers |
| `GET` | `/api/dashboard/intake` | Live intake utilisation |
| `GET` | `/api/dashboard/compliance` | The institution compliance matrix |
| `POST` | `/api/students/{id}/correction-preview` | Assess a correction without writing |
| `POST` | `/api/students/{id}/corrections` | Apply a reviewed correction |
| `GET` | `/api/review-tasks` | The review checklist |
| `GET` | `/api/verification-tokens` | The tokens issued for a record |
| `GET` | `/api/verify/token/{token}` | The public, allowlist-only verification |
| `GET` | `/api/reports/students.csv` | Export an authorised student report |

Every protected endpoint enforces its permission **on the server** - hiding a
button in React is not a security control.

---

## Environment variables

| Variable | Purpose |
|---|---|
| `MONGODB_URL` | The MongoDB connection string. **Required** outside the demo mode. |
| `MONGODB_DATABASE` | The database name. Default `edusync`. |
| `ALLOW_IN_MEMORY_DB` | `true` to run the throwaway demo database. Never in production. |
| `SECRET_KEY` | The JWT signing key. At least 32 characters. |
| `SEAL_HMAC_KEY` | The HMAC sealing key. |
| `MATCH_KEY` | Optional separate key for the keyed APAAR match token. |
| `FRONTEND_ORIGIN` | The public origin of the web frontend. Used for CORS and for badge links. |
| `CORS_ORIGINS` | Extra allowed origins. A wildcard is never allowed. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | The access-token lifetime. Default 60. |
| `REFRESH_TOKEN_EXPIRE_DAYS` | The refresh-token lifetime. Default 7. |
| `VERIFICATION_TOKEN_MINUTES` | The verification-token lifetime. Default 60. |
| `RATE_LIMIT_PER_MINUTE` | The request budget per client. Default 60. |
| `UPLOAD_MAX_SIZE_MB` | The largest accepted CSV. Default 10. |
| `BCRYPT_ROUNDS` | The password hashing cost. Default 12. |
| `DEMO_PASSWORD` | The password of the seeded demo accounts. |
| `ENVIRONMENT` | `dev`, `test` or `production`. |

---

## Tests

```bash
cd edusync && pytest -q     # 258 tests
```

The suite runs against the in-memory MongoDB, so it needs no server and no
fixtures on disk. It covers the APAAR validator, all ten anomaly layers, the
six impact rules, the correction workflow (including the no-mutation
assertion, the 409 on a stale version and the review-task lifecycle), the
verification tokens (including the allowlist-only public answer), the consent
policy, the audit chain, the RBAC matrix, the Google sign-in (the
authorisation URL, the code exchange, the account linking and the CSRF state)
and the HTTP API end to end.

---

## Deployment

### Render (the backend)

`render.yaml` at the repository root describes the service. The steps are:

1. Create a **MongoDB Atlas** cluster and a database user.
2. In Render, create a **Web Service** from the repository - the file is
   picked up automatically. The build is `pip install -r requirements.txt`
   and the start command is
   `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
3. Add the environment variables: `MONGODB_URL` (the Atlas string),
   `SECRET_KEY`, `SEAL_HMAC_KEY` and `FRONTEND_ORIGIN`.
4. The health check is `/health`.

> **Atlas and transactions.** MongoDB Atlas clusters are replica sets, so
> multi-document transactions are available. A standalone development server
> is not a replica set, and the correction workflow falls back to the explicit
> `operation_status` recovery there.

### Vercel (the frontend)

1. Import the repository into Vercel with **the `frontend` directory as the
   root**.
2. The build is `npm run build` and the output directory is `dist`.
   `frontend/vercel.json` adds the SPA rewrite, so `/verify/t/<token>` and
   `/impact` resolve as deep links.
3. **Set `VITE_API_URL` to the Render URL of the backend** (no trailing
   slash) **before the first build**. The Vercel rewrite sends every path -
   `/api` included - to `index.html`, so a build with the variable unset
   would receive HTML instead of JSON. Changing it later needs a redeploy.

> The deployment configuration is provided and documented, but **it was not
> exercised against a live Atlas, Render or Vercel account** in this
> repository - only the local Docker Compose path was run.

### Locally

```bash
docker compose up --build     # MongoDB + the API + the React frontend
```

See [`docs/architecture.md`](docs/architecture.md) for the full design.
