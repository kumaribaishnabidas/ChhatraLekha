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
                      +---------------------------+
                      |        EduSynC web        |
                      |  portal / PWA / verifier  |
                      +-------------+-------------+
                                    |  fetch() / JSON
                      +-------------v-------------+
                      |       FastAPI (app)       |
                      |  routers -> services      |
                      +------+---------------+----+
                             |               |
              +--------------v--+         +--v----------------+
              |  SQLAlchemy 2.0 |         |  cryptography     |
              |  async ORM      |         |  HMAC / Ed25519   |
              +------+----------+         +--+----------------+
                     |                       |
         +-----------v-----------+   +-------v--------+
         | PostgreSQL / SQLite   |   |   qrcode       |
         | institutions          |   |   reportlab    |
         | program_intakes       |   +----------------+
         | students              |
         | anomalies             |
         | consents              |
         | audit_logs (chained)  |
         | users / api_keys      |
         | revoked_credentials   |
         +-----------------------+
```

### Layers

| Layer | Package | Responsibility |
|---|---|---|
| Configuration | `app.core.config` | Environment-driven settings; refuses to boot with dev secrets in production |
| Persistence | `app.core.database` | Async engine, session factory, declarative base |
| Security | `app.core.security` | bcrypt password hashing, PBKDF2 PIN hashing, JWT issuing, API keys |
| Access control | `app.core.rbac` | The role-to-permission matrix, shared by every router |
| Domain | `app.models` | SQLAlchemy tables and the enums the whole platform agrees on |
| Rules | `app.services` | The APAAR validator, the anomaly engine, the seal signer, the CSV reader/writer, the consent policy, the audit chain, the risk scorer, the PDF renderer |
| API | `app.api` | Routers; each one is thin and delegates to the services |
| Audit | `app.audit.writer` | Chained, hash-linked audit entries |
| Presentation | `app.web` | Jinja2 portal, CSS, JS, PWA manifest and service worker |

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
OCI + foreign national 15%, TFW 5%, and a per-course PMSSS cap.

The quota/nationality rules are deliberately domain-correct:

* `FN` (foreign national) must **not** be an Indian citizen - CRITICAL.
* `NRI` and `OCI` are, by definition, Indian nationals - an NRI seat held by a
  foreign national is a mis-bucketed foreign national, so it is **HIGH**, not
  CRITICAL.
* `NRI` held by an Indian national is **correct** and is never flagged.
* `TFW` and `PMSSS` are Government of India entitlements reserved for Indian
  students.

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

## 5. The tamper-evident audit trail

```
hash(n) = SHA-256( hash(n-1) | timestamp | actor | action | subject | details | category )
```

Each entry stores its predecessor's hash. Deleting, reordering or editing a
row invalidates every hash after it, and `app.services.audit_chain.first_break`
names the first broken link. The chain needs no server and no key, so an
auditor can re-verify it offline from an exported CSV.

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

The verification endpoint always issues its verdict; it withholds the
personal fields when consent is missing or withdrawn.

## 7. Access control

| Role | May |
|---|---|
| `aicte_admin` | national dashboard, anomaly review, compliance matrix, audit trail, reports |
| `institution_admin` | own students, CSV upload, consent, certificates, reports, own audit trail |
| `verifier` | credential verification, audit trail |
| `student` | own record, own certificates, own consent |

The matrix lives in `app.core.rbac` and is the only place a role-to-capability
mapping is written down. Every router declares the permission it needs with
`require_permission(...)`, and institution-scoped routers additionally call
`principal.require_scope(...)`.

## 8. Data flow of a batch upload

```
CSV file
  -> CsvParser                       (RFC 4180 reader, BOM tolerant)
  -> CsvIngestionValidator           (row-level issues: CRITICAL / WARNING)
  -> CsvValidationContext            (live registry: existing IDs, seat counts)
  -> preview  (nothing is written)   or   commit
  -> Student rows                    (the committable rows only)
  -> AnomalyEngine.evaluate          (all ten layers)
  -> Anomaly rows + verification status refresh
  -> AuditLog entry                  (chained)
```

A row with a CRITICAL issue is never committed, and an APAAR ID that appears
twice inside one batch blocks **every** copy of it: there is no way to tell
which one is the authoritative admission.

## 9. Testing

`pytest` with `pytest-asyncio`. The suite runs against a throwaway SQLite
database and covers:

* the APAAR validator (structure, placeholders, the Luhn advisory, masking),
* all ten anomaly layers, individually and in combination,
* the seal generations, including the Ed25519 round trip,
* the QR payload round trip and rendering,
* the CSV reader, the CSV validator and the CSV writers (including a
  write-then-read round trip),
* the consent policy, the audit chain and the RBAC matrix,
* the HTTP API end to end: authentication, RBAC enforcement, CRUD, bulk
  upload, dashboards, verification, consent, reports and the portal pages.

## 10. Deployment

* `Dockerfile` - a two-stage build: dependencies in one stage, a slim runtime
  image that runs as a non-root user.
* `alembic` - the schema is migrated, never auto-created, in production.
* `GitHub Actions` - the suite runs on Python 3.11, 3.12 and 3.13, followed by
  a container build and a health-check smoke test.
* `SECRET_KEY`, `SEAL_HMAC_KEY` and the database URL come from the
  environment; nothing sensitive is committed.
