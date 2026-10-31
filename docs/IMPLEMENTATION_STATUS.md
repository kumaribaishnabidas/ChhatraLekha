# ChhatraLekha — Implementation Status & Baseline Audit

**Date**: 2026-10-24
**Repository**: [ChhatraLekha](https://github.com/kumaribaishnabidas/ChhatraLekha.git)
**Branch**: `main`
**Commit**: Latest HEAD

This document records the factual, tested state of the ChhatraLekha codebase across all tiers: Web Frontend (React / Vite), API Backend (Python / FastAPI / MongoDB), Android Client (Kotlin / Jetpack Compose / Room), and CI / Tooling.

---

## 1. Verified Baseline Test & Build Results

Every command below has been executed on the local workspace and confirmed passing:

| Component | Test / Build Command | Result | Duration / Scope |
| :--- | :--- | :--- | :--- |
| **API Backend** | `pytest --tb=no` (in `edusync/`) | **262 passed**, 0 failures, 1 warning | ~10.2s across 26 test suites |
| **Frontend Unit Tests** | `npm.cmd test -- --run` (in `frontend/`) | **61 passed**, 0 failures | 8 test files, 19.88s |
| **Frontend Route Links** | `npm.cmd run check:links` (in `frontend/`) | **Passed** | 19 declared router paths verified |
| **Frontend Translations** | `npm.cmd run i18n:check` (in `frontend/`) | **Passed** | 13 languages, 257 translation keys |
| **Frontend Production Build** | `npm.cmd run build` (in `frontend/`) | **Passed** | `dist/` bundle created in 11.07s |
| **Android Core Unit Tests** | `.\gradlew.bat :core:test` (in `Acadentrix/`) | **204 passed**, 0 failures | 15 test XML suites in 29s |
| **Android Debug APK Build** | `.\gradlew.bat assembleDebug` (in `Acadentrix/`) | **Passed** | `app-debug.apk` built (22.5 MB) |
| **Anomaly Evaluation** | `python -m app.scripts.eval_anomalies` | **100% Precision, 100% Recall** | 23 synthetic records, 10 layers |
| **Performance Benchmark** | `python -m app.scripts.benchmark` | **All Passed (0 errors)** | CSV parse, Ed25519, HMAC, Token |

---

## 2. Core Workflows Implementation Checklist

| # | Workflow | Status | Description & Code Verification |
| :--- | :--- | :--- | :--- |
| **1** | **Login & Authorization** | **IMPLEMENTED** | JWT authentication in `edusync/app/api/auth.py` (`/api/auth/login`, `/me`, `/refresh`). Fine-grained RBAC in `edusync/app/core/rbac.py` enforcing 4 distinct roles: `aicte_admin`, `institution_admin`, `verifier`, `student`. Tenant scoping prevents cross-institution data access (`test_tenant_isolation_institution_scoping`). |
| **2** | **Create / Read / Update Academic Record** | **IMPLEMENTED** | Full CRUD in `edusync/app/api/records.py`. Version incrementing (`version += 1`), change-tracking, and input validation via Pydantic schemas in `edusync/app/schemas/student.py`. Tenant scoping enforced on all mutations. |
| **3** | **CSV Upload & Batch Validation** | **IMPLEMENTED** | Implemented in `edusync/app/api/records.py` (`/upload-csv`) and `edusync/app/services/csv_ingestion.py`. Validates headers, MIME type, max size (5 MB), and row-level schema constraints. Returns row-by-row errors with line numbers and field names without leaking raw PII. |
| **4** | **Anomaly Detection & Reviewer Outcome** | **IMPLEMENTED** | 10-layer regulatory rule engine in `edusync/app/services/anomaly_engine.py` (Python) and `Acadentrix/core/.../AnomalyEngine.kt` (Kotlin). Detects APAAR syntax, cross/same institution duplicates, roll collisions, intake breaches, supernumerary caps, quota conflicts, date anomalies, missing fields, and unapproved programs. Tested by `eval_anomalies.py` with 100% precision & recall. |
| **5** | **Change-Impact Analysis** | **IMPLEMENTED** | Implemented in `edusync/app/services/impact_engine.py` and exposed via `/api/impact/preview` and `/api/impact/apply`. Compares existing vs proposed record, flagging cascade capacity impacts and marking credentials for reissue. Interactive 3-step review UI in `frontend/src/pages/ImpactPage.jsx`. |
| **6** | **QR Credential Issuance & Verification** | **IMPLEMENTED** | Issuance produces opaque verification tokens (`edusync/app/api/tokens.py`) or signed URLs (`edusync/app/services/qr.py`). Verification: Public opaque token route `GET /api/verify/token/{token}` returns an allowlist (institution, programme, academic year, valid verdict) with zero PII. Authenticated verifiers can query `/api/verify/{apaar_id}`. Public key endpoint `GET /api/verify/public-key` allows offline Ed25519 verification. |
| **7** | **Credential Expiry & Revocation** | **IMPLEMENTED** | Fails closed immediately on verification. `GET /api/verify/token/{token}` verifies `expires_at < now` -> `EXPIRED`, `document.revoked` -> `REVOKED`, and `document.needs_reissue` -> `NEEDS_REFRESH`. Tested in backend test suites. |
| **8** | **Android Local Persistence & API Sync** | **IMPLEMENTED** | Room database in `Acadentrix/app` caches students (`StudentRecordDao`), pending operations (`PendingSyncDao`), and audit events (`AuditEntryDao`). Pure Java HTTP client `EduSyncApiClient.kt` communicates with backend REST API. `SyncManager.kt` provides two-way sync, optimistic concurrency (record versions), HTTP 409 conflict detection, and safe offline fallbacks. |
| **9** | **Audit Event Creation & Retrieval** | **IMPLEMENTED** | Append-only audit log in `edusync/app/audit/writer.py` and `AuditRepository`. Backward-linked hash chaining in `edusync/app/services/audit_chain.py` (`prev_hash || timestamp || actor || action || subject || details || category`). Endpoint `GET /api/audit/verify-chain` verifies cryptographic continuity. |

---

## 3. Architecture & Mismatch Analysis

### 3.1 Android Offline-Only Claims vs. Real Sync Integration
- **Previous Claim**: The Android app README previously claimed purely offline isolated operation while another document claimed full cloud synchronization.
- **Reality & Resolution**: The Android codebase (`Acadentrix/core` and `Acadentrix/app`) implements a robust offline-capable client:
  - Local persistence: Room database (`ApaarDatabase`) caches records and queues offline changes in `pending_sync`.
  - Network client: `EduSyncApiClient.kt` uses standard `java.net.HttpURLConnection` (zero third-party networking library dependencies) with configurable base URLs (`http://10.0.2.2:8000/api` for emulator, or custom server).
  - Sync orchestration: `SyncManager.kt` pushes pending queue operations with idempotency keys and pulls latest records from `/api/sync/pull`. In the event of a concurrent server edit, HTTP 409 Conflict is surfaced to the user.
  - Offline QR Verification: The app clearly flags offline verification as *limited* (cannot confirm real-time revocation status without server connectivity).

### 3.2 SHA-256 "Seals" vs. Cryptographic Signatures
- **Previous Claim**: Early design documents referred to SHA-256 hashes as "tamper-proof cryptographic seals".
- **Reality & Resolution**: A bare SHA-256 hash is an unkeyed digest; anyone can modify a record and recompute the hash.
  - ChhatraLekha implements three distinct generations in `seal.py` and `SealVerification`:
    1. `LEGACY` (unkeyed SHA-256): Explicitly marked as `LEGACY_UNVERIFIED`. It is never accepted as an authentic signature.
    2. `HMAC` (`HMAC-SHA256`): Keyed with a server-held secret. Authenticates that the issuing server produced the seal.
    3. `ED25519` (Asymmetric Digital Signature): Signed with an Ed25519 private key kept server-side. Third parties can verify credentials independently using the public key published at `GET /api/verify/public-key`.

### 3.3 Test Totals Alignment
- **Discrepancy**: Prior notes in various drafts claimed conflicting test numbers (ranging from 160 to 250).
- **Verified Ground Truth**:
  - Backend pytest: **262 tests passed** (0 failures).
  - Frontend vitest: **61 tests passed** (0 failures).
  - Android core unit tests: **204 tests passed** across 15 XML test suites (0 failures).
  - Total automated unit/integration tests across the entire repository: **527 tests passed**.

### 3.4 CI Pipeline Status
- **Prior State**: `.github/workflows/edusync.yml` tested only backend and frontend, omitting the Android app entirely and missing `Acadentrix/**` in triggers.
- **Current State**: Extended `.github/workflows/edusync.yml` to trigger on `Acadentrix/**`, install JDK 17, execute `./gradlew :core:test`, and compile the debug APK via `./gradlew assembleDebug`.

---

## 4. Benchmark Performance Evidence

Captured from `python -m app.scripts.benchmark` on Windows 11 / Python 3.14 (AMD64):

1. **Batch CSV Ingestion & Validation Throughput**:
   - 50 rows: Median **4.287 ms** (p95: 4.990 ms) → **11,663 rows/s** (0 errors)
   - 100 rows: Median **9.186 ms** (p95: 12.848 ms) → **10,886 rows/s** (0 errors)
   - 250 rows: Median **22.537 ms** (p95: 35.718 ms) → **11,093 rows/s** (0 errors)

2. **Cryptographic Seal Generation & Verification**:
   - HMAC-SHA256 Sign: Median **0.0099 ms** | Verify: Median **0.0126 ms** (0 errors)
   - Ed25519 Digital Sign: Median **0.0758 ms** | Verify: Median **0.2233 ms** (0 errors)

3. **Public Token Hash Lookup & Chain Verification**:
   - Opaque Token Hash Check: Median **0.0021 ms** (476,187 ops/sec, 0 errors)
   - Audit Chain (500 entries): Median **3.223 ms** (155,154 entries/sec, 0 errors)

---

## 5. Security & Privacy Guarantees

- **No Secrets in Repo**: Private keys and JWT secrets are injected via environment variables (`.env`). `.env.example` contains only benign placeholders.
- **Zero Raw PII in Public Verification**: Opaque token verification endpoint `GET /api/verify/token/{token}` returns strictly an allowlist of non-sensitive academic attributes (institution, programme, academic year, valid verdict) and never exposes the APAAR ID, student name, date of birth, or contact information.
- **Append-Only Tamper-Evident Audit Trail**: Audit entries are hash-chained backwards to genesis hash `0`*64. Any retroactive modification or deletion breaks downstream hashes.
- **Defense-in-Depth HTTP Headers**: Every response carries `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy`, and unique correlation tracing header `X-Request-ID`.
