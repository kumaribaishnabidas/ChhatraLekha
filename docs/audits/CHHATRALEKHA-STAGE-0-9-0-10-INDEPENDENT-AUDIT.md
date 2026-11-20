# ChhatraLekha — Independent Security & Stability Audit
## Comprehensive Audit of Stage 0.9 (Attendance) & Stage 0.10 (Session Lifecycle) on Current Main

**Repository:** `https://github.com/kumaribaishnabidas/ChhatraLekha`  
**Primary / Target Branch:** `main`  
**Verified Target Commit SHA:** `dd073d9c0c5817baa67eb4532e7647114478c27a`  
**Active Working Branch:** `feature/stage-0-9-attendance` (HEAD: `dc552f1bc805134ea53356aa0788e3a1597cb89a`)  
**Auditor:** Antigravity (Application Security Auditor & Senior Software Architect)  
**Execution Date:** November 18, 2026  
**Audit Mode:** STRICT READ-ONLY AUDIT — ZERO CODE CHANGES ENFORCED  
**Final Verdict:** **REJECTED** (High-Severity Security & Reliability Defects Identified)

---

## 1. Executive Summary

This independent audit delivers a comprehensive evaluation of **Stage 0.9 (Attendance Management System)** and **Stage 0.10 (Secure Authentication Session Lifecycle)** in the ChhatraLekha educational super-platform. The audit independently verified the code, schemas, RBAC rules, tenant isolation boundaries, and automated test suites against statutory educational mandates (NEP 2020, CBSE By-Laws, UGC/AICTE guidelines) and cryptographic standards.

### Summary of Critical Findings
1. **Parent Ward Authorization Bypass (`SEC-BE-001` - High Severity):** In `/api/attendance/my-summary`, parent relationship validation trusts `(principal.user or {}).get("ward_apaar_id")` and marks the relationship `linked = True` without verifying against the `guardian_relationships` collection for `status: "VERIFIED"`. A parent account with an unverified self-asserted child APAAR ID in their profile document can view full student attendance records without administrative verification.
2. **Non-Atomic Token Rotation & Split-Brain Risk (`SEC-AUTH-04` - High Severity):** In `SessionRepository.rotate_session` (`chhatralekha/app/repositories/sessions.py`), predecessor consumption (`find_one_and_update`) and descendant creation (`insert_one`) are non-atomic. If `insert_one` fails due to a network glitch, primary election, or duplicate key error, the predecessor token is marked rotated while the child is never persisted. When the client retries with the predecessor token, the server misidentifies the retry as **Token Reuse / Replay Attack** and revokes all sessions in the family (`revoke_family`), causing unexpected mass user logout.
3. **Broken Attendance Correction Workflow (`DEF-FE-002` - High Severity):** In `frontend/src/pages/AttendancePage.jsx`, clicking "Request Correction" in the roll call roster hardcodes `session_id: 'ATT-PREV'` without a session selector. Submitting this request to `/api/attendance/corrections` consistently fails with HTTP 404 (`Student attendance record not found in the specified session.`).
4. **CSV Formula Injection (`SEC-BE-002` - Medium Severity):** In `/api/attendance/reports/export-csv`, fields (`target_label`, `student_name`, `remarks`) are written raw to CSV without neutralizing formula trigger characters (`=`, `+`, `-`, `@`), exposing spreadsheet users to CSV Formula Injection (CWE-1236).
5. **Fake Success Banner on Export Failure (`DEF-FE-001` - Medium Severity):** In `AttendancePage.jsx`, the CSV export error `catch` block calls `notify('Attendance CSV report downloaded.', 'success')`, rendering a misleading green success banner when an export fails or is rejected with HTTP 403.
6. **Unenrolled Student Identifier Acceptance (`SEC-BE-004` - Medium Severity):** Batch attendance sessions validate teacher assignment and intra-batch uniqueness but do not verify whether student IDs in `payload.records` are actively enrolled in the target class or institution.
7. **Test Suite Status:** 806 automated tests were executed and passed across Backend (457), Frontend (138), and Android Core (211). However, key negative security regression tests are missing from the test suite.

---

## 2. Repository Baseline

- **Repository URL:** `https://github.com/kumaribaishnabidas/ChhatraLekha`
- **Main Branch Commit (Verified):** `dd073d9c0c5817baa67eb4532e7647114478c27a`  
  `Merge pull request #41 from kumaribaishnabidas/stabilization/stage-0-8-academic-core`
- **Current Branch:** `feature/stage-0-9-attendance`
- **Current HEAD Commit:** `dc552f1bc805134ea53356aa0788e3a1597cb89a`  
  `docs: add Stage 0.9 planning inspection audit`
- **Working Tree Status:** 9 modified files and 2 untracked audit documents preserved intact. No code modifications were made during this audit.

---

## 3. Branch and Commit Analysis

```
* dc552f1 (HEAD -> feature/stage-0-9-attendance) docs: add Stage 0.9 planning inspection audit
* dd073d9 (origin/main, main) Merge pull request #41 from kumaribaishnabidas/stabilization/stage-0-8-academic-core
|\  
| * b1210c4 fix(security): reject ambiguous guardian student IDs
| * 64781d1 fix(security): tenant-scope guardian academic summaries
| * 1ac66e3 fix(security): close tenant and auth regressions
| * bcd5302 security: remediate Python dependency vulnerabilities
| * 0b10461 docs(audit): add Stage 0.8.1 merge and remote synchronization reports
| * f8451cb feat(academic-core): Stage 0.8 stabilization, contract repair and security verification
| *   59e5e6e chore(merge): sync with origin/main
| |\  
| |/  
|/|   
* |   c8693bc Merge pull request #38 from kumaribaishnabidas/chore/security-audit-gating
|\ \  
| * | 728ed49 ci(security): audit every pull request
|/ /  
| * 00921e3 test(auth): add backend and frontend registration test suites
| * 0ad5386 feat(frontend): connect SignupPage to real registration endpoint
| * 48a3d54 feat(auth): add secure self-service registration endpoint
| * 288ffec fix(security): stop onboarding completion from granting role or tenant
| * 252e772 feat(security): Stage 0.10 Secure Authentication Session Lifecycle implementation, tests & docs
|/  
* 84e0c31 ci(security): fail audit checks on vulnerabilities
*   40393fd Merge pull request #37 from kumaribaishnabidas/fix/dependency-security
|\  
| * 8d226f1 fix(frontend): remediate npm audit vulnerabilities
|/  
* 4559557 docs: normalize trailing newline in Stage 0.4 remediation report
* 14466f9 feat(security): complete Stage 0.4 tenant isolation and access control remediation
* f75cf73 feat(attendance): Stage 0.9 Attendance Management System implementation, tests & docs
```

### Lineage Insights:
1. **Stage 0.9 History:** The original Stage 0.9 implementation was committed at `f75cf73` on Nov 6, 2026. However, `f75cf73` contained architectural gaps (synthetic demo cohorts, hardcoded 92.4% metrics, missing intra-batch checks, and uppercase-only `ACTIVE` enrolment queries). The current working branch `feature/stage-0-9-attendance` resolves these gaps, but has not yet merged to `main`.
2. **Stage 0.10 History:** Stage 0.10 was committed at `252e772` on Nov 6, 2026, and is **already merged into `main`** as an ancestor of `dd073d9`.

---

## 4. Stage 0.9 — Attendance Security Audit

### 4.1 Teacher Assignment Authorization
- `_is_teacher_assigned_to_target` verifies `teacher_assignments` (matching `target_id`, `class_id`, `target_label`, and optional `subject_id`) and designated teacher fields in `classes`.
- Unassigned teachers attempting to record roll call receive `HTTP 403 Forbidden` (`Staff without an institution association cannot record attendance` or `You are not assigned to class or subject...`).
- **Defect Noted (`SEC-BE-005`):** While roll call is properly gated, `request_attendance_correction` does not verify teacher assignment to the cohort, allowing any teacher in the institution to submit correction requests for any class.

### 4.2 Student Ownership & Parent Verification
- **Students:** `/api/attendance/my-summary` validates that students may only view their own records (`student_id == own_id`). Mismatched requests return `HTTP 403 Forbidden` (`You may only access your own attendance record.`).
- **Parents:** **Critical vulnerability identified (`SEC-BE-001`):** Lines 1056–1057 trust `(principal.user or {}).get("ward_apaar_id")` and grant immediate access without validating `guardian_relationships` for `status: "VERIFIED"`.

### 4.3 Tenant Isolation
- Compound indexes enforce tenant scoping across `attendance_sessions`, `attendance_records`, `attendance_policies`, and `attendance_corrections`.
- Cross-tenant queries return `HTTP 403 Forbidden`.

### 4.4 Duplicate Submission Prevention
- `DAILY` mode prevents collisions on `(institution_id, target_id, session_date, mode='DAILY')`.
- `PERIOD_WISE` mode prevents collisions on `(institution_id, target_id, session_date, mode, period_number, [subject_id])`.
- Collisions return `HTTP 409 Conflict` with instructions to use an authorized correction request.

### 4.5 Batch Marking Atomicity & Student Validation
- Intra-batch duplicate student entries are rejected with `HTTP 422 Unprocessable Content`.
- **Integrity Gap (`SEC-BE-004`):** Batch submissions do not verify that submitted student IDs are actively enrolled in the target class or institution.

### 4.6 Correction Workflow & Append-Only Audit History
- Corrections require documented justification `reason`.
- Reviews are restricted to administrative roles (`ADMIN_ROLES`).
- Upon approval, the record is updated and an immutable audit entry (`previous_status`, `new_status`, `changed_by`, `timestamp`, `review_notes`) is appended to `attendance_records.audit_trail`.
- Session counters (`present_count`, `absent_count`, `late_count`, `excused_count`) are recalculated atomically.

### 4.7 CSV Export Security & Authorization
- Gated by `EXPORT_REPORTS` permission.
- **Vulnerability Identified (`SEC-BE-002`):** Missing CSV formula injection neutralization on user-controlled fields (`remarks`, `student_name`, `target_label`).

---

## 5. Stage 0.10 — Authentication & Session Security Audit

### 5.1 Refresh-Token Rotation & Token Identifiers
- Tokens carry unique `jti` and `family_id` claims minted via `secrets.token_urlsafe(32)`.
- At-rest storage in MongoDB collection `refresh_sessions` stores only SHA-256 digests (`token_hash`), never plaintext tokens.

### 5.2 Expiration, Revocation & Family Invalidation
- Expiration is checked against MongoDB `expires_at` and token claims, backed by a MongoDB TTL index.
- If an already consumed token (`rotated_at is not None`) is presented, the system detects replay, revokes all tokens in `family_id` (`revoke_family`), and records `REFRESH_TOKEN_REUSE_DETECTED` in `db["audit_events"]`.

### 5.3 Server-Side Logout (`POST /api/auth/logout`)
- Accepts optional `refresh_token` or `all_sessions: true`.
- Enforces principal ownership: cross-user session revocation returns `HTTP 403 Forbidden`.
- Repeated calls are idempotent and safe.

### 5.4 Token Rotation Atomicity & Failure Handling (`SEC-AUTH-04`)
- In `SessionRepository.rotate_session`:
  ```python
  updated_old = await self._collection.find_one_and_update(
      {"jti": old_jti, "rotated_at": None, "is_revoked": False},
      {"$set": {"rotated_at": now, "last_used_at": now, "child_jti": new_jti}},
  )
  if not updated_old:
      return False, None

  child_document = {...}
  await self._collection.insert_one(child_document)
  ```
- **High Severity Flaw:** If `insert_one(child_document)` fails, the predecessor token is already marked consumed (`rotated_at` set), but the child token was never persisted. Subsequent retries trigger false positive reuse detection, revoking all active sessions for that user.

### 5.5 Frontend De-Duplication & Session Handling
- `frontend/src/services/api.js` manages an `inFlightRefreshPromise` de-duplicating concurrent 401 refreshes to prevent race conditions during rotation.
- Clears local storage on logout and refresh failure, setting `sessionStorage.setItem('chhatralekha.session_expired', '1')` and redirecting to `/login?expired=1`.

---

## 6. Tenant Isolation Matrix

| Platform Resource | Scoping Control | Enforcement Point | Multi-Tenant Status |
|---|---|---|:---:|
| Attendance Sessions | `institution_id` index & filter | `attendance.py` / `database.py` | **PASS** |
| Attendance Records | `institution_id` index & filter | `attendance.py` / `database.py` | **PASS** |
| Attendance Policies | Unique on `institution_id` | `attendance.py` / `database.py` | **PASS** |
| Attendance Corrections | Scoped by `institution_id` | `attendance.py` / `database.py` | **PASS** |
| Class Rosters | Filtered by `institution_id` & class | `attendance.py` | **PASS** |
| Attendance Reports | Filtered by `target_inst` | `attendance.py` | **PASS** |
| Refresh Sessions | Scoped by `user_id` and token hash | `sessions.py` | **PASS** |
| Student / Parent Portal | Scoped by verified relationship | `attendance.py:1056` | **FAIL (`SEC-BE-001`)** |

---

## 7. RBAC Matrix

| Role | Roll Call | View Roster | Update Policy | Request Correction | Review Correction | Export CSV | View My Summary |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Platform / Super Admin** | Allowed | Allowed | Allowed | Allowed | Allowed | Allowed | Allowed |
| **School / College Admin** | Allowed | Allowed | Allowed | Allowed | Allowed | Allowed | Allowed |
| **Academic Admin** | Allowed | Allowed | Allowed | Allowed | Allowed | Allowed | Allowed |
| **Teacher (Assigned)** | Allowed | Allowed | Denied (403) | Allowed | Denied (403) | Denied (403) | Own Tenant Only |
| **Teacher (Unassigned)** | Denied (403) | Denied (403) | Denied (403) | Allowed (`SEC-BE-005`) | Denied (403) | Denied (403) | Own Tenant Only |
| **Student** | Denied (403) | Denied (403) | Denied (403) | Denied (403) | Denied (403) | Denied (403) | Own Record Only |
| **Parent (Verified)** | Denied (403) | Denied (403) | Denied (403) | Denied (403) | Denied (403) | Denied (403) | Verified Ward Only |
| **Parent (Unverified)** | Denied (403) | Denied (403) | Denied (403) | Denied (403) | Denied (403) | Denied (403) | **BYPASS (`SEC-BE-001`)** |

---

## 8. Authentication Security Findings

| Finding ID | Severity | CWE | Summary |
|---|---|---|---|
| **`SEC-AUTH-04`** | **High** | CWE-662 (Improper Handling of Synchronization / Atomicity) | Non-atomic session rotation in `rotate_session` can leave orphaned consumed tokens on `insert_one` failure, triggering false positive token reuse revocation. |
| **`SEC-AUTH-02`** | Low | CWE-613 (Insufficient Session Expiration) | Verified resolved in Stage 0.10: `POST /api/auth/logout` properly terminates sessions at rest. |
| **`SEC-AUTH-03`** | Low | CWE-384 (Session Fixation / Stateless Token Replay) | Verified resolved in Stage 0.10: Stateful refresh tokens with `jti`, SHA-256 hashing at rest, and family reuse detection. |

---

## 9. Data Integrity Findings

1. **Intra-batch Student Duplication:** Resolved via Pydantic validator on `AttendanceBatchSubmitIn` and backend loop verification rejecting batches with duplicate student IDs (HTTP 422).
2. **Compound Unique Session Constraints:** Resolved via MongoDB compound indexes preventing concurrent duplicate submissions for identical class/date/period.
3. **Un-enrolled Student Marking (`SEC-BE-004`):** Batch attendance marking accepts arbitrary student identifiers without verifying enrolment against `student_enrolments`.
4. **Append-Only Audit Trail:** Verified that corrections do not overwrite historical records; approval appends to the immutable `audit_trail` array and recalculates session tallies.

---

## 10. Frontend / API Integration

1. **Role Routing:** `AttendancePage.jsx` and `TeacherWorkspacePage.jsx` correctly distinguish roles and load authenticated views.
2. **Synthetic Data Elimination:** Verified zero hardcoded demo cohorts (`CLS-10A`, `CLS-9B`) and zero fallback attendance percentages (`92.4%`).
3. **Frontend Defect `DEF-FE-001`:** In `AttendancePage.jsx:315-316`, the CSV export error `catch` block shows a green success notification ("Attendance CSV report downloaded.") when the request fails.
4. **Frontend Defect `DEF-FE-002`:** In `AttendancePage.jsx:595-600`, "Request Correction" in the roster hardcodes `session_id: 'ATT-PREV'` without a session selector, causing HTTP 404 on submission.

---

## 11. Test Execution Results

All automated test suites were executed independently during this audit.

| Suite | Exact Command | Environment | Passed | Failed | Skipped | Status |
|---|---|---|:---:|:---:|:---:|:---:|
| **Backend Pytest** | `python -m pytest --tb=short chhatralekha/tests` | Python 3.13.11, pytest 8.3.4 | **457** | 0 | 0 | **PASS** |
| **Backend Lint** | `python -m ruff check chhatralekha` | Ruff 0.8.2 | — | 0 | 0 | **PASS** |
| **Frontend Vitest** | `npm.cmd test -- --run --pool=forks` | Node.js v22.14.0, Vitest 5.1.0 | **138** | 0 | 0 | **PASS** |
| **Frontend Build** | `npm.cmd run build` | Vite 6.4.5 | — | 0 | 0 | **PASS** |
| **Frontend i18n** | `npm.cmd run i18n:check` | Node.js v22.14.0 | **13 locales** | 0 | 0 | **PASS** |
| **Android Core** | `.\gradlew.bat :core:test --no-daemon` | OpenJDK 17.0.14, Gradle 8.14.6 | **211** | 0 | 0 | **PASS** |
| **TOTALS** | All Multi-Stack Automated Suites | — | **806** | **0** | **0** | **PASS** |

---

## 12. CI Status

- GitHub Actions workflow `.github/workflows/chhatralekha.yml` runs:
  - Legacy-name and term audit (`check-legacy-names.sh`)
  - Backend matrix across Python 3.11, 3.12, 3.13
  - Frontend matrix across Node 20, 22
  - Android unit tests and debug APK build
  - Container build and healthcheck
- Dependency security workflow `.github/workflows/dependency-security.yml` enforces zero-vulnerability audit gating.

---

## 13. Documentation Consistency Audit

1. **`DOC-GAP-001` (Informational):** `docs/audits/STAGE-0-10-SESSION-LIFECYCLE-REPORT.md` claims "Active pre-existing sessions without a jti are seamlessly upgraded on initial refresh", but `app/api/auth.py:335-339` deliberately rejects untracked tokens with HTTP 401.
2. **`DOC-GAP-002` (Informational):** `docs/IMPLEMENTATION_STATUS.md` lists `Date: 2026-10-31` and outdated test numbers (442 / 135 / 204 vs current 457 / 138 / 211), and omits Stage 0.9 and Stage 0.10 from core workflow statuses.
3. **`DOC-GAP-003` (Informational):** `docs/security/SECURITY-REMEDIATION-STATUS.md` lists `Active Working Branch: security/stage-0-4-tenant-isolation` and documents `ward_apaar_id` as an accepted bypass for parent access.

---

## 14. Defect Inventory

| Finding ID | Severity | Category | File & Line | Summary |
|---|:---:|---|---|---|
| **`SEC-BE-001`** | **High** | Authorization | `attendance.py:1056-1057` | Parent relationship bypass via self-asserted `ward_apaar_id` in user document. |
| **`SEC-AUTH-04`** | **High** | Reliability / Crypto | `sessions.py:109-135` | Non-atomic token rotation can trigger false positive token reuse revocation on insertion failure. |
| **`DEF-FE-002`** | **High** | UI / Workflow | `AttendancePage.jsx:595-600` | Hardcoded `'ATT-PREV'` session ID causes correction submissions to fail with HTTP 404. |
| **`SEC-BE-002`** | **Medium** | Injection | `attendance.py:990-1014` | CSV Formula Injection (CWE-1236) in attendance report export. |
| **`DEF-FE-001`** | **Medium** | UI / Error Handling | `AttendancePage.jsx:315-316` | Fake success alert shown on CSV export failure. |
| **`SEC-BE-004`** | **Medium** | Data Integrity | `attendance.py:237-264` | Unenrolled student IDs accepted in batch attendance roll calls. |
| **`SEC-BE-005`** | **Low** | Authorization | `attendance.py:631-650` | Unassigned teachers can submit correction requests for any class in the institution. |
| **`TST-GAP-001`** | **Low** | QA / Coverage | `test_stage_0_9_attendance.py:480` | Missing negative security tests for unauthorized CSV export. |
| **`DOC-GAP-001`** | **Info** | Documentation | `STAGE-0-10-SESSION-LIFECYCLE-REPORT.md` | Legacy session upgrade claims contradict fail-closed code. |
| **`DOC-GAP-002`** | **Info** | Documentation | `IMPLEMENTATION_STATUS.md` | Stale metadata and test counts. |

---

## 15. Prioritized Remediation Plan

### Priority 1: High-Severity Fixes (Blocking)
1. **Remediate `SEC-BE-001`:** Delete lines 1056–1057 in `attendance.py`. Require explicit lookup in `guardian_relationships` with `status: "VERIFIED"`.
2. **Remediate `SEC-AUTH-04`:** In `sessions.py:rotate_session`, wrap rotation in a `try...except` block that reverts the predecessor token's `rotated_at` and `child_jti` if `insert_one` fails.
3. **Remediate `DEF-FE-002`:** In `AttendancePage.jsx`, pass the active session ID to the correction modal or provide a session/date picker.

### Priority 2: Medium-Severity Fixes
4. **Remediate `SEC-BE-002`:** Sanitize CSV cells in `attendance.py` by prepending `'` to values beginning with `=`, `+`, `-`, `@`, `\t`, or `\r`.
5. **Remediate `DEF-FE-001`:** Replace the fake success message in `AttendancePage.jsx:315-316` with an authentic error notification.
6. **Remediate `SEC-BE-004`:** Validate that all student IDs in batch roll call exist in `student_enrolments` for the target class.

### Priority 3: Low & Documentation Fixes
7. Add teacher assignment check to `request_attendance_correction` (`SEC-BE-005`).
8. Add missing negative authorization test for CSV export (`TST-GAP-001`).
9. Update `IMPLEMENTATION_STATUS.md` and `SECURITY-REMEDIATION-STATUS.md`.

---

## 16. Final Go / No-Go Recommendation

**Final Verdict:** **REJECTED**

**Recommendation:** While the foundational multi-tenant architecture, stateful refresh-token lifecycle, and 806 automated tests demonstrate strong architectural rigor, the presence of **three High-Severity findings** (`SEC-BE-001`, `SEC-AUTH-04`, `DEF-FE-002`) and **three Medium-Severity findings** (`SEC-BE-002`, `DEF-FE-001`, `SEC-BE-004`) represents unacceptable security and operational risk.

Merge to `main` and progression to Stage 0.11 must remain **blocked** until the Priority 1 and Priority 2 remediations are implemented and verified.

