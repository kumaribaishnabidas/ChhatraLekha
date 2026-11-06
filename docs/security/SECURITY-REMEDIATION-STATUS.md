# Security Remediation Status & Governance Matrix

**Project:** ChhatraLekha  
**Last Updated:** 2026-11-06 (Post-Stage 0.4 Tenant Isolation Remediation)  
**Governance Level:** Production-Ready Baseline  
**Active Working Branch:** `security/stage-0-4-tenant-isolation`

---

## 1. Vulnerability Tracking Ledger

| Finding ID | Severity | Category | Component | Description | Status | Resolved In |
|---|---|---|---|---|---|---|
| **SEC-AUTH-01** | **Critical** | Authentication | `app/api/auth.py` | Unrestricted demo login administrative backdoor | **RESOLVED** | Stage 0.3 |
| **SEC-ISO-01** | **Critical** | Tenant Isolation | `app/api/profile.py` | Unscoped student fallback in profile retrieval | **RESOLVED** | Stage 0.3 |
| **SEC-ISO-02** | **Critical** | Tenant Isolation | `app/api/me.py` | Unscoped single-document student fallback in `_resolve_student_record` | **RESOLVED** | Stage 0.3 |
| **SEC-ATT-01** | **High** | Access Control | `app/api/attendance.py` | IDOR on student attendance summary endpoint (`my-summary`) | **RESOLVED** | Stage 0.3 |
| **SEC-ASM-01** | **High** | Access Control | `app/api/assessments.py` | IDOR on student assessment results endpoint (`my-results`) | **RESOLVED** | Stage 0.3 |
| **SEC-NOTIF-01** | **High** | Access Control | `app/modules/notifications/service.py` | IDOR on notification mark read and deletion | **RESOLVED** | Stage 0.3 |
| **SEC-EMAIL-01** | **Medium** | Authentication | `app/modules/profiles/service.py` | Plaintext verification code disclosure and universal bypass | **RESOLVED** | Stage 0.3 |
| **CI-LINT-01** | **Informational** | CI / Quality | `app/modules/` | 13 Ruff lint diagnostics breaking backend CI matrix | **RESOLVED** | Stage 0.3 |
| **SEC-TENANT-01** | **High** | Tenant Isolation | `app/api/academic.py`, `announcements.py`, `reports.py`, `attendance.py`, `teacher.py`, `transfers.py` | Fail-open queries on null/missing tenant context and unsafe default fallbacks | **RESOLVED** | Stage 0.4 |
| **SEC-AUTH-02** | **Low** | Authentication | `app/api/auth.py` | Documented `POST /api/auth/logout` endpoint not implemented | Scheduled (P3) | Stage 0.5 |
| **SEC-AUTH-03** | **Low** | Authentication | `app/core/security.py` | Stateless refresh tokens without database persistence or rotation | Scheduled (P3) | Stage 0.5 |

---

## 2. Implemented Security Controls

### 2.1 Demo Login and Production Hardening
- **Environment Gate:** In production (`settings.is_production is True`), demo login is completely disabled and returns HTTP 403 Forbidden.
- **Role Escalation Prevention:** High-privilege administrative roles (`national_admin`, `platform_operator`, `state_admin`, `district_admin`, `regulator_admin`) are strictly disallowed from being minted via demo login.
- **Fail-Closed Catalog:** Only pre-configured demo personas (`student`, `parent`, `teacher`, `school_admin`, `college_admin`, `university_admin`) are accepted. Unknown roles return HTTP 400 Bad Request.

### 2.2 Student Record and PII Isolation
- **Verified Linkage Only:** Student profile resolution requires an explicit, verified `apaar_id` linked to the principal's account.
- **No Natural Storage Fallbacks:** All unconditioned queries (`find_one()` or `find().limit(1)`) are prohibited. If an account has no verified relationship, the API returns `student_details = None` on profile endpoints and HTTP 404 Not Found on self-service endpoints.

### 2.3 Object-Level Access Control (IDOR Prevention)
- **Attendance Records:** `GET /api/attendance/my-summary` validates that:
  - Students may only view their own attendance.
  - Parents may only view attendance for verified linked wards (`db["guardian_relationships"]` or `ward_apaar_id`).
  - Educators may only view attendance for students enrolled in their assigned institution.
- **Examination Results:** `GET /api/assessments/my-results` enforces identical object-level authorization and requires that marks have been explicitly published by an instructor.
- **Notification Mutations:** `mark_as_read` and `delete_notification` enforce `user_id == principal.subject` or institutional broadcast scope, returning HTTP 404 if the target does not belong to the caller.

### 2.4 Cryptographic Verification Lifecycle
- **Cryptographic Randomness:** Codes are generated via Python's `secrets` module (`100000` to `999999`).
- **Timing-Safe Comparison:** Code verification utilizes `hmac.compare_digest` with SHA-256 HMAC digest validation.
- **15-Minute Expiry Window:** Pending codes carry explicit `expires_at` timestamps. Expired codes are automatically rejected and marked consumed.
- **Brute-Force Rate Limiting:** Codes enforce a strict 5-attempt limit. Exceeding 5 attempts permanently invalidates the pending verification.
- **Single-Use Consumption:** Successful verification immediately consumes and deletes the pending code, preventing replay attacks.
- **Production Suppression:** Plaintext verification codes (`demo_code`) are never returned in production API responses.

### 2.5 Multi-Tenant Isolation and Fail-Closed Access Control (Stage 0.4)
- **Fail-Closed Missing Context:** All institutional operations require verified `institution_id` on the authenticated principal. Missing tenant context strictly fails closed with HTTP 400 Bad Request.
- **No Unsafe Fallbacks:** Eliminated all occurrences of hardcoded fallback identifiers (`"INST-0421"`, `"INST-DEFAULT"`).
- **Cross-Institution Parameter Probing Blocked:** Institutional users specifying a mismatched `institution_id` query parameter are immediately rejected with HTTP 403 Forbidden.
- **Notice Acknowledgement Ownership Enforced:** The announcement acknowledgement endpoint (`POST /api/announcements/{id}/acknowledge`) enforces `principal.require_scope(doc.get("institution_id"))`, preventing cross-tenant acknowledgements.
- **Strictly Scoped Exports & Mutations:** Attendance sessions, corrections, review tasks, student registers, and academic setups enforce object-level ownership checks preventing cross-tenant reads or writes.
- **Directorate Governance Preserved:** Regulators and platform administrators (`national_admin`, `aicte_admin`, `platform_operator`) retain explicitly authorized multi-tenant and cross-institution oversight capabilities.

---

## 3. Engineering Security Guidelines

When introducing new endpoints or database queries in ChhatraLekha:

1. **Always Parameterize Multi-Tenant Queries:** Never execute queries on multi-tenant collections (`students`, `attendance_records`, `assessment_marks`, `announcements`) without including `institution_id` or `user_id` in the filter.
2. **Never Implement Blind Storage Fallbacks:** Never use `find_one()` without a filter to serve demo or fallback data. Fallback data must come from synthetic in-memory fixtures only.
3. **Verify IDOR on Parameterized Endpoints:** Whenever an endpoint accepts a resource ID (e.g., `student_id`, `notification_id`, `session_id`), verify that the authenticated caller owns the resource or has institutional authorization before executing the query.
4. **Adhere to the Zero Em/En Dash Design Rule:** User-facing strings and test assertions must use standard hyphens `-` instead of Unicode em dashes `—` or en dashes `–`.
5. **Run Pre-Commit Verification:** Run `ruff check app tests` and `pytest chhatralekha/tests` before submitting code.

