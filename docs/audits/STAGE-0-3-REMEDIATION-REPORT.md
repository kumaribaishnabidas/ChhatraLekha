# Stage 0.3 Remediation Report — Critical Security Remediation and Backend CI Recovery

**Project:** ChhatraLekha  
**Branch:** `security/stage-0-3-remediation`  
**Execution Date:** 2026-11-06  
**Auditor / Engineer:** Antigravity (Advanced Agentic Coding)  
**Status:** PASS (All P0, P1, and P2 Findings Remediated and Verified)

---

## 1. Executive Summary

This report documents the verification, implementation, and test execution for Stage 0.3 of the ChhatraLekha platform. Following the findings of the Stage 0.2 audit, all critical (P0), high-severity (P1), and medium/CI-blocker (P2) vulnerabilities were resolved directly in the codebase without altering underlying database engines, violating architectural boundaries, or breaking API compatibility.

A dedicated test suite comprising 15 automated security regression tests was authored in `chhatralekha/tests/test_stage_0_3_security_remediation.py`. The full backend test suite now passes with 369 passed tests (100%), Ruff static analysis reports zero errors across all backend source files, the frontend test suite passes with 75 passed tests (100%), and the frontend production bundle builds cleanly.

---

## 2. Remediated Findings Matrix

| Finding ID | Severity | Category | Target Component | Status | Verification Evidence |
|---|---|---|---|---|---|
| **SEC-AUTH-01** | **Critical** | Authentication | `chhatralekha/app/api/auth.py` | Fixed | Gated behind `not settings.is_production`; rejected role escalation (`national_admin`, `platform_operator`); rejected invalid roles. |
| **SEC-ISO-01** | **Critical** | Data Isolation | `chhatralekha/app/api/profile.py` | Fixed | Removed unscoped `find_one()` query; unlinked student accounts receive `student_details = None`. |
| **SEC-ISO-02** | **Critical** | Data Isolation | `chhatralekha/app/api/me.py` | Fixed | Removed unscoped `find().limit(1)` fallback; strictly verified via `apaar_id` or user linkage; returns HTTP 404 if unlinked. |
| **SEC-ATT-01** | **High** | Access Control | `chhatralekha/app/api/attendance.py` | Fixed | Enforced ownership check: students restricted to self; parents restricted to verified wards; staff scoped to institution. |
| **SEC-ASM-01** | **High** | Access Control | `chhatralekha/app/api/assessments.py` | Fixed | Enforced ownership check: examination marks query rejects unauthorized cross-student queries with HTTP 403. |
| **SEC-NOTIF-01** | **High** | Access Control | `chhatralekha/app/modules/notifications/service.py` | Fixed | Scoped `mark_as_read` and `delete_notification` to caller's `user_id` / institutional broadcast view; returns HTTP 404 on mismatch. |
| **SEC-EMAIL-01** | **Medium** | Authentication | `chhatralekha/app/modules/profiles/service.py` | Fixed | Removed universal `"123456"` bypass; suppressed `demo_code` in production; added 15-minute TTL; enforced 5-attempt brute-force limit; prevented code reuse. |
| **CI-LINT-01** | **Informational** | CI / Quality | `app/modules/notifications/`, `app/modules/profiles/`, `app/schemas/` | Fixed | Resolved all 13 Ruff diagnostics (`I001` isort, `F401` unused imports, `B904` exception chaining); pinned `ruff==0.7.2` in CI workflow. |

---

## 3. Detailed Technical Remediation

### 3.1 SEC-AUTH-01: Demo Login Security Hardening (P0)

**Changed File:** `chhatralekha/app/api/auth.py`

**Corrections Implemented:**
1. **Production Gating:** Introduced explicit verification using `runtime_settings = get_settings()`. When `runtime_settings.is_production` is `True`, `POST /api/auth/demo-login` immediately raises `HTTPException(403, "Demo login is disabled in production environments.")`.
2. **Escalation Prevention:** Defined an explicit set of disallowed administrative roles (`national_admin`, `platform_operator`, `state_admin`, `district_admin`, `regulator_admin`). Attempting to request any of these roles via demo login raises HTTP 403 Forbidden.
3. **Strict Catalog Allowlist:** If a requested persona is not explicitly present in `DEMO_PERSONA_CATALOG`, the endpoint raises HTTP 400 Bad Request rather than silently falling back to a default account.
4. **Isolated Demo Seeding:** Seeded demo records in `db["students"]` only for authorized demo student personas so that demo profiles function cleanly without compromising real student isolation.

**Verification:** Tests 1, 2, and 3 in `test_stage_0_3_security_remediation.py` verify production rejection, escalation rejection, and permitted development demo login.

---

### 3.2 SEC-ISO-01 and SEC-ISO-02: Elimination of Unscoped Student Fallbacks (P0)

**Changed Files:**
- `chhatralekha/app/api/profile.py`
- `chhatralekha/app/api/me.py`

**Corrections Implemented:**
1. **Profile Resolution (`profile.py`):** Removed line 124 (`student_rec = await db["students"].find_one()`) and name-matching heuristics. A student profile is now resolved strictly if `user.get("apaar_id")` or `principal.apaar_id` exists and matches a document in `db["students"]`. If unlinked, `student_details` is set to `None`.
2. **Self-Service Student Resolution (`me.py`):** Removed lines 83-96 in `_resolve_student_record`, which matched students by display name, email prefix regex, or the first natural storage document (`db["students"].find().limit(1)`). If the authenticated principal has no verified `apaar_id` linked to their account, the function raises `HTTPException(404, "No student record linked to your account. Enter a claim code from your institution.")`.

**Verification:** Test 4 in `test_stage_0_3_security_remediation.py` verifies that an unlinked student account querying `/api/profile/me` receives `student_details = None`, and `/api/me/profile` returns HTTP 404 Not Found without leaking victim student PII.

---

### 3.3 SEC-ATT-01 and SEC-ASM-01: Attendance and Examination Results IDOR Fixes (P1)

**Changed Files:**
- `chhatralekha/app/api/attendance.py`
- `chhatralekha/app/api/assessments.py`

**Corrections Implemented:**
1. **Attendance Summary (`attendance.py`):** Added authorization verification to `GET /api/attendance/my-summary`:
   - If caller is a `student`: caller can only query their own record; passing an unrelated `student_id` raises HTTP 403 Forbidden.
   - If caller is a `parent`: caller can only query verified linked children confirmed via `db["guardian_relationships"]` or `ward_apaar_id`; unverified targets raise HTTP 403 Forbidden.
   - If caller is a `teacher`, `institution_admin`, or `academic_admin`: student must belong to caller's `institution_id`; cross-institution access raises HTTP 403 Forbidden.
2. **Assessment Results (`assessments.py`):** Implemented identical ownership and institutional boundaries in `GET /api/assessments/my-results`.

**Verification:** Tests 5, 6, 7, 8, 9, and 10 in `test_stage_0_3_security_remediation.py` verify that Student A cannot access Student B records, unlinked parents are rejected, verified parents are permitted, unassociated teachers are rejected, and cross-institution queries are rejected with HTTP 403.

---

### 3.4 SEC-NOTIF-01: Notification Ownership Enforcement (P1)

**Changed File:** `chhatralekha/app/modules/notifications/service.py`

**Corrections Implemented:**
1. **Scoping Mark-as-Read:** Modified `mark_as_read` to filter by `notification_id` and require either `user_id == principal.subject` or an institutional broadcast (`user_id == None` and `institution_id` matches). If no record matches the caller's scope, the endpoint raises HTTP 404 Not Found.
2. **Scoping Delete:** Modified `delete_notification` to enforce identical ownership filters. An attacker attempting to delete another user's notification receives HTTP 404 Not Found.

**Verification:** Test 11 in `test_stage_0_3_security_remediation.py` verifies that User B cannot mark read or delete User A's notifications, while User A can perform both operations on their own notifications.

---

### 3.5 SEC-EMAIL-01: Secure Email Verification Lifecycle (P2)

**Changed File:** `chhatralekha/app/modules/profiles/service.py`

**Corrections Implemented:**
1. **Removal of Universal Bypass:** Deleted hardcoded check `if payload.code == "123456"`.
2. **Suppression of Code in Responses:** `demo_code` is returned only in non-production environments (`not settings.is_production and settings.environment != "production"`).
3. **15-Minute Expiration Window:** Added `expires_at = now + timedelta(minutes=15)`. Codes presented after expiration raise HTTP 400 Bad Request and are marked consumed.
4. **Brute-Force Rate Limiting:** Enforced a maximum of 5 attempts per verification code. On the 5th failed attempt, the code is invalidated (`consumed = True`), and subsequent requests raise HTTP 400 Bad Request.
5. **Constant-Time Verification:** Used `hmac.compare_digest` to verify submitted code against stored code and SHA-256 HMAC digest to eliminate timing attacks.
6. **Code Consumption and Reuse Prevention:** Successful verification immediately pops the pending verification entry and records `verified_at` timestamp. Replay attempts fail with HTTP 400 Bad Request.
7. **MongoDB Dot Notation Resilience:** Refactored storage to prevent MongoDB from misinterpreting email dots as subdocument paths.

**Verification:** Tests 12, 13, 14, and 15 in `test_stage_0_3_security_remediation.py` verify expired code rejection, 5-attempt limit invalidation, universal bypass rejection, and single-use code consumption.

---

### 3.6 CI-LINT-01: Ruff Diagnostics and CI Workflow Pinning (P2)

**Changed Files:**
- `chhatralekha/app/modules/notifications/router.py`
- `chhatralekha/app/modules/notifications/schemas.py`
- `chhatralekha/app/modules/notifications/service.py`
- `chhatralekha/app/modules/profiles/router.py`
- `chhatralekha/app/modules/profiles/schemas.py`
- `chhatralekha/app/modules/profiles/service.py`
- `chhatralekha/app/schemas/profile.py`
- `frontend/src/components/ai/GroundedDataCard.jsx`
- `.github/workflows/chhatralekha.yml`

**Corrections Implemented:**
1. **Import Sorting (`I001`):** Formatted and organized import blocks across all newly scaffolded profile and notification files.
2. **Unused Imports (`F401`):** Removed unused symbols:
   - `NotificationPriority` from `notifications/service.py`
   - `fastapi.status` from `profiles/router.py`
   - `timezone` and `Optional` from `profiles/service.py`
   - `UserSessionOut` from `profiles/service.py`
3. **Exception Chaining (`B904`):** Updated `profiles/service.py:262` to add `from e` to the `HTTPException` raise clause.
4. **Frontend Design System Lint:** Replaced isolated em dash character in `GroundedDataCard.jsx` with standard hyphen `-`.
5. **CI Workflow Pinning:** Updated line 65 of `.github/workflows/chhatralekha.yml` from `pip install ruff` to `pip install ruff==0.7.2`, ensuring consistent behavior with `requirements.txt`.

---

## 4. Test Execution Records

### 4.1 Backend Ruff Static Analysis
- **Command:** `cd chhatralekha; ruff check app tests`
- **Output:**
  ```text
  All checks passed!
  ```
- **Exit Code:** 0

### 4.2 Security Regression Suite
- **Command:** `pytest chhatralekha/tests/test_stage_0_3_security_remediation.py`
- **Output:**
  ```text
  15 passed, 1 warning in 8.24s
  ```
- **Exit Code:** 0

### 4.3 Full Backend Test Suite
- **Command:** `pytest chhatralekha/tests`
- **Output:**
  ```text
  369 passed, 1 warning in 19.61s
  ```
- **Exit Code:** 0

### 4.4 Frontend Vitest Suite
- **Command:** `cd frontend && npm test`
- **Output:**
  ```text
  Test Files  11 passed (11)
       Tests  75 passed (75)
    Duration  21.54s
  ```
- **Exit Code:** 0

### 4.5 Frontend Production Build
- **Command:** `cd frontend && npm run build`
- **Output:**
  ```text
  ✓ 812 modules transformed.
  ✓ built in 16.50s
  ```
- **Exit Code:** 0

---

## 5. Remaining Risks and Next Steps

1. **Stateful Refresh Tokens:** Refresh tokens currently remain signed JWTs without active database tracking or `jti` revocation lists. This is scheduled as a P3 item for Stage 0.4.
2. **Explicit Logout Endpoint:** While client-side tokens can be cleared, an explicit `POST /api/auth/logout` endpoint remains a P3 documentation alignment item.
3. **Readiness Gate:** All P0, P1, and P2 security vulnerabilities and CI blockers are fully resolved and verified. The codebase is secure and ready for branch commit.

