# EduSynC - Architecture

## 1. The problem in one paragraph

AICTE-approved institutions each hold their own student registers. The national
picture of *sanctioned intake against actual enrolment* only exists after the
data is collected, and by the time it is collected it is already wrong: a
student is admitted twice, a foreign-national seat is filled by an Indian
citizen, a supernumerary ceiling is quietly exceeded. EduSynC moves the
validation to the moment the data arrives, and makes the resulting record
verifiable by anyone who holds the APAAR ID.

## 2. Component map

```
   AICTE Administrator | Institution Administrator | Verifier | Student
                                  |
                                  v
                  +-------------------------------+
                  |  React 19 + Vite + Tailwind 4   |
                  |  Recharts, React Router, PWA   |
                  +---------------+-------------------+
                                  |  fetch() / JSON
                  +---------------v-------------------+
                  |         Python FastAPI           |
                  |  routers -> services -> repos     |
                  +-------+-------------------+-------+
                          |                   |
          +---------------v------+   +--------v-----------------+
          |   Motor (async)     |   |  cryptography           |
          |   MongoDB driver    |   |  HMAC / Ed25519         |
          +----------+-----------+   |  qrcode / reportlab     |
                     |               +--------------------------+
        +------------v---------------------------------------+
        |  institutions  programmes  students  anomalies      |
        |  consents  audit_events  users  api_keys           |
        |  revoked_credentials  submissions  policy_rules   |
        +-----------------------------------------------------+

                  +-------------------------------+
                  |  Android client (Kotlin)      |
                  |  Compose + Room, offline-first|
                  +-------------------------------+
```

### Layers

| Layer | Package | Responsibility |
|---|---|---|
| Configuration | `app.core.config` | Environment-driven settings; refuses to boot with dev secrets in production |
| Persistence | `app.core.database` | The async MongoDB client, the collection registry and the index strategy |
| Documents | `app.models.documents` | The attribute-style document wrapper, the keyed match token and the redaction helpers |
| Repositories | `app.repositories` | Every MongoDB read and write lives here; the routers never touch a collection |
| Security | `app.core.security` | bcrypt password hashing, PBKDF2 PIN hashing, JWT issuing, API keys |
| Access control | `app.core.rbac` | The role-to-permission matrix, shared by the server and the React frontend |
| Rules | `app.services` | The APAAR validator, the anomaly engine, the seal signer, the CSV reader and writer, the consent policy, the audit chain, the risk scorer, the PDF renderer |
| API | `app.api` | Routers; each one is thin and delegates to the services |
| Audit | `app.audit.writer` | Chained, hash-linked audit entries |
| Frontend | `../frontend` | The React application: pages, components, hooks and the Axios client |

## 3. The anomaly engine

Ten independent layers run over a `RegistrySnapshot` of the whole registry.
Each layer is a pure function, so the same data always produces the same
verdicts - which is what makes the engine testable and the platform auditable.

| # | Layer | Anomaly type | Severity |
|---|---|---|---|
| 1 | APAAR syntax | `INVALID_APAAR_FORMAT` | CRITICAL |
| 2 | Cross-institution duplicate | `DUPLICATE_CROSS_COLLEGE` | CRITICAL / HIGH |
| 3 | Same-institution duplicate | `DUPLICATE_SAME_INSTITUTION` | CRITICAL / HIGH |
| 4 | Duplicate roll number | `DUPLICATE_ROLL_NUMBER` | HIGH |
| 5 | Regular intake breach | `EXCESS_APPROVED_INTAKE` | CRITICAL |
| 6 | Supernumerary ceilings | `SUPERNUMERARY_BREACH` | CRITICAL / WARNING |
| 7 | Documentary consistency | `INCONSISTENT_CATEGORY` | WARNING / HIGH / CRITICAL |
| 8 | Impossible dates | `IMPOSSIBLE_DATE` | CRITICAL / HIGH |
| 9 | Missing mandatory fields | `MISSING_REQUIRED_FIELD` | HIGH |
| 10 | Unsanctioned programme | `UNSANCTIONED_PROGRAM` | CRITICAL |

Supernumerary ceilings follow the AICTE Approval Process Handbook: NRI 5%,
OCI + foreign national 15%, TFW 5%, and a per-course PMSSS cap. The policy
version is stored on every programme document, so a rule change is a data
change rather than a code change.

The quota/nationality rules are deliberately domain-correct:

* `FN` (foreign national) must **not** be an Indian citizen - CRITICAL.
* `NRI` and `OCI` are, by definition, Indian nationals - an NRI seat held by a
  foreign national is a mis-bucketed foreign national, so it is **HIGH**, not
  CRITICAL.
* `NRI` held by an Indian national is **correct** and is never flagged.
* `TFW` and `PMSSS` are Government of India entitlements reserved for Indian
  students.

Every finding is stored with a rule code, a severity, an explanation **and a
recommended next step**, so the review queue is actionable rather than a list
of raw complaints.

## 4. The credential seal

Three generations of seal coexist so that nothing already printed stops
verifying:

| Generation | Wire format | Verifiable by | Verdict |
|---|---|---|---|
| Legacy | 32 hex characters | anybody (it is unkeyed) | `LEGACY_UNVERIFIED` |
| HMAC-SHA256 | `HMAC-SHA256.<keyId>.<b64url>` | the holder of the server secret | `VALID` |
| Ed25519 | `ED25519.<keyId>.<b64url>` | anyone with the published public key | `VALID` |

The committed payload is the APAAR ID, the institution, the programme, the
academic year, the enrolment date, the student name, the date of birth, the
gender, the quota bucket, the nationality, the institute roll number and the
payload version. The moment the badge was printed (`issued_at`) is
deliberately **not** committed to, because a verifier does not know it and
committing to it would make every badge unverifiable.

The private key never leaves the server. The Android client holds no signing
material at all.

## 5. The tamper-evident audit trail

```
hash(n) = SHA-256( hash(n-1) | timestamp | actor | action | subject | details | category )
```

Each entry stores its predecessor's hash. Deleting, reordering or editing a
row invalidates every hash after it, and `app.services.audit_chain.first_break`
names the first broken link. The chain needs no server and no key, so an
auditor can re-verify it offline from an exported CSV.

Audit entries store a **masked** APAAR ID, never the raw one.

## 6. Consent

Consent is modelled per purpose, not as a single flag, because the Digital
Personal Data Protection Act requires purpose-wise, revocable and evidenced
consent. `app.services.consent_policy` resolves the ledger down to one
decision per purpose:

* a purpose that requires explicit consent is blocked until a `GRANTED`
  record exists;
* a revocation always beats an earlier grant, whatever the order of the
  records;
* the most recent record for a purpose is the one that counts.

The verification endpoint always issues its verdict; it withholds the personal
fields when consent is missing or withdrawn.

## 7. Access control

| Role | May |
|---|---|
| `aicte_admin` | national dashboard, anomaly review, compliance matrix, audit trail, reports |
| `institution_admin` | own students, CSV upload, consent, certificates, reports, own audit trail |
| `verifier` | credential verification, audit trail |
| `student` | own record, own certificates, own consent |

The matrix lives in `app.core.rbac` and is mirrored in
`frontend/src/utils/permissions.js`. The **server** is the enforcement point;
the React copy only decides what to show. Every router declares the permission
it needs with `require_permission(...)`, and institution-scoped routers
additionally call `principal.require_scope(...)`.

## 8. Privacy: the keyed match token

The raw APAAR ID is never used as a lookup key. Each student document also
stores `apaar_id_hmac`, a keyed HMAC-SHA256 of the normalised identifier, and
the equality lookups use that token. An index dump therefore discloses no
identifiers, while the duplicate detection still works exactly as before.

## 9. MongoDB data model

| Collection | Key fields | Indexes |
|---|---|---|
| `institutions` | `institution_id`, name, type, state, city, university, grade | `institution_id` |
| `programmes` | `institution_id`, `program_id`, `academic_year`, `approved_intake`, the four supernumerary caps, `policy_version`, `total_sanctioned` | `(institution_id, program_id, academic_year)`, `(program_id, academic_year)` |
| `students` | `apaar_id`, `apaar_id_hmac`, the enrolment facts, `record_status`, `submission_source` | `apaar_id`, `apaar_id_hmac`, `(institution_id, program_id)`, `(institution_id, student_institute_roll_no)`, `(record_status, academic_year)` |
| `anomalies` | `student_apaar_id`, `anomaly_type`, `severity`, `details`, `recommended_action`, `review_status` | `(severity, review_status)`, `student_apaar_id`, `institution_id` |
| `consents` | `student_apaar_id`, `purpose`, `status`, `channel`, `policy_version`, `recorded_at`, `revoked_at` | `student_apaar_id`, `(purpose, status)` |
| `audit_events` | `timestamp`, `actor`, `action`, `subject`, `details`, `prev_hash`, `hash` | `timestamp`, `actor` |
| `users` | `user_id`, `email`, `role`, `institution_id`, `password_hash` | `email` |
| `api_keys` | `key_id`, `key_hash`, `role`, `scopes` | `key_id` |
| `revoked_credentials` | `apaar_id`, `reason`, `revoked_by` | `apaar_id` |
| `submissions` | `institution_id`, `submitted_by`, the accepted/quarantined counts | `(created_at, status)` |

**There is deliberately no unique index on the APAAR ID.** A unique index would
make the cross-institution duplicate physically impossible to store, and
therefore impossible to detect - which is precisely the anomaly the platform
exists to find.

## 10. Data flow of a batch upload

```
CSV file
  -> CsvParser                       (RFC 4180 reader, BOM tolerant)
  -> CsvIngestionValidator           (row-level issues: CRITICAL / WARNING)
  -> CsvValidationContext            (live registry: existing IDs, seat counts)
  -> preview  (nothing is written)   or   commit
  -> Student documents               (the committable rows only)
  -> AnomalyEngine.evaluate          (all ten layers)
  -> Anomaly documents + verification status refresh
  -> Submission document             (the provenance of the batch)
  -> AuditLog entry                  (chained)
```

A row with a CRITICAL issue is never committed, and an APAAR ID that appears
twice inside one batch blocks **every** copy of it: there is no way to tell
which one is the authoritative admission.

## 11. The React frontend

| Path | What it does |
|---|---|
| `src/services/api.js` | The single Axios client: bearer token, automatic refresh, 401 handling |
| `src/hooks/useAuth.jsx` | The authentication context and the permission helpers |
| `src/hooks/useApi.js` | A small data-fetching hook with loading, error and reload state |
| `src/utils/permissions.js` | The mirror of the server's permission matrix |
| `src/utils/format.js` | Number, date, APAAR, quota and severity formatting |
| `src/components/layout` | The app shell (top bar, navigation) and the page header |
| `src/components/common` | Cards, KPI tiles, badges, spinner, empty and error states, pagination |
| `src/pages` | Login, Dashboard, Institutions, Students, Upload, Anomalies, Verification, Reports |

Every page handles the loading, empty, success and error states. Every table
has a search, a filter and a pagination control. The permission matrix decides
what is rendered, and the server decides what is allowed.

## 12. Testing

**Backend** - pytest with pytest-asyncio, 159 tests, running against the
in-memory MongoDB:

* the APAAR validator (structure, placeholders, the Luhn advisory, masking);
* all ten anomaly layers, individually and in combination;
* the seal generations, including the Ed25519 round trip;
* the QR payload round trip and rendering;
* the CSV reader, the CSV validator and the CSV writers (including a
  write-then-read round trip);
* the consent policy, the audit chain and the RBAC matrix;
* the HTTP API end to end: authentication, RBAC enforcement, CRUD, bulk
  upload, dashboards, verification, consent, reports and the OpenAPI document.

**Frontend** - Vitest and React Testing Library, 25 tests: the sign-in flow,
the error handling, the API client, the formatting helpers and the permission
matrix.

**Android** - JUnit, 185 tests in the shared `:core` module.

## 13. Deployment

* `render.yaml` - the Render web service: `rootDir: edusync`,
  `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, health check `/health`.
  The secrets are declared with `sync: false`, so they are set in the Render
  dashboard and never in the file.
* `frontend/vercel.json` - the SPA rewrite and the safe security headers.
* `edusync/Dockerfile` - a three-stage build: the React bundle, the Python
  dependencies, and a slim runtime image that runs as a non-root user.
* `docker-compose.yml` - MongoDB 7 plus the API, with a health check.
* `.github/workflows/edusync.yml` - the backend suite on Python 3.11, 3.12 and
  3.13, the frontend suite on Node 20 and 22, then a container build and a
  health-check smoke test.
* `SECRET_KEY`, `SEAL_HMAC_KEY` and the database URL come from the
  environment; nothing sensitive is committed.

### The transaction mode

A correction writes to six collections. On a replica set - and a MongoDB
Atlas cluster always is - the whole correction runs inside one
**multi-document transaction**, so a failure half way through leaves nothing
behind. On a standalone server there are no transactions, so the operation is
recorded in `operation_status` first, and an interrupted correction stays
visible and recoverable rather than silently half-applied. The mode is
detected at start-up and logged once.

### The in-memory database

`MONGODB_URL` empty would silently fall back to an in-memory database. It
does not any more: the fallback has to be asked for with
`ALLOW_IN_MEMORY_DB=true`, it is refused outright in production, it logs a
loud warning, and it shows a "demo data, not persisted" notice in `/health`
and in the UI. A missing or unreachable `MONGODB_URL` is a **clear startup
error**, and the connection string is redacted (`user:***@host`) before it
appears in any message.
