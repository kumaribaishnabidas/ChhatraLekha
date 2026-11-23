# Institute ERP Security & Risk Assessment

**Document Reference:** `docs/erp/INSTITUTE-ERP-SECURITY-AND-RISK-ASSESSMENT.md`  
**Report Identifier:** `SEC-ERP-RISK-2026-11-23`  
**Project:** ChhatraLekha Unified Education Platform  
**Compliance Standard:** DPDP Act 2023, AICTE/CBSE Guidelines, OWASP Top 10  
**Author:** Google Antigravity  

---

## 1. Security Architecture & Threat Model

The Institute ERP integration handles sensitive student personal data (PII), academic transcripts, attendance logs, and admission applications. The security architecture enforces defense-in-depth across the application lifecycle:

```
[Client Verification] ➔ [Gateway Authentication] ➔ [RBAC & Scope Guard] ➔
[Input Validation] ➔ [Audit Event Ledger] ➔ [Tenant-Isolated Storage]
```

### Key Security Assertions:
1. **Zero Real Student PII:** Testing and demonstration use synthetic identities only (`is_demo: true`).
2. **Minor Data Protection (DPDP Act 2023):** Minor student accounts (`is_minor: true`) cannot independently consent to data sharing or profile publication without verified guardian association (`guardian_name`, `guardian_relationship`).
3. **APAAR ID Cryptography:** Plaintext APAAR IDs are masked on display (`XXXXXXXX1234`). Identity matching uses keyed SHA-256 HMAC tokens derived from a secret salt (`MATCH_KEY`), preventing cross-database rainbow table attacks.
4. **Tamper-Evident Credentials:** All issued certificates, grade sheets, and ID cards carry Ed25519 digital signatures and 64-character verification tokens.

---

## 2. Permission Mapping Matrix

| ERP Workflow | Required Role | Required Permission Scope | Object-Level Verification |
| :--- | :--- | :--- | :--- |
| **View Institute Roster** | `school_admin`, `college_admin`, `university_admin`, `faculty` | `Principal.require_scope(institution_id)` | Caller must belong to institution. |
| **Approve Admission Request** | `school_admin`, `college_admin`, `university_admin` | `Principal.require_scope(institution_id)` | Join request must target caller's institution. |
| **Mark Class Attendance** | `teacher`, `faculty`, `school_admin` | `Principal.require_scope(institution_id)` | Academic unit must be assigned to teacher. |
| **View Student Profile** | `student` (self), `parent` (ward), `faculty` (assigned), `admin` | Subject match OR guardian link OR tenant scope | Cross-student access returns HTTP 404 / 403. |
| **Upload Document** | `student`, `applicant`, `admin` | Caller identity match | File type, size, and virus scan validation. |
| **Verify / Reject Document** | `school_admin`, `college_admin` | `Principal.require_scope(institution_id)` | Document must belong to institution student. |
| **Modify Academic Setup** | `institution_admin`, `university_admin` | `Principal.require_scope(institution_id)` | Term and class updates audit-logged. |

---

## 3. Risk Register & Mitigation Strategy

| Risk ID | Identified Risk | Severity | Likelihood | Impact | Mitigation Strategy | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **RSK-ERP-01** | Cross-tenant data leakage via admission join requests. | **High** | Low | Critical | Enforce `institution_id` query parameter validation against `principal.institution_id` on review queues. | **MITIGATED** |
| **RSK-ERP-02** | Accidental exposure of API documentation (`/docs`) in production. | **Medium** | Low | High | Gated by `ENABLE_DOCS=false` default in production, guarded by SPA router 404 handlers. | **RESOLVED** (`SEC-DOCS-01`) |
| **RSK-ERP-03** | Fabrication of client-submitted academic contexts in demo login. | **Low** | Low | Medium | Strict server-side validation against `DEMO_ACADEMIC_SCHOOLS` and `COLLEGES`. | **RESOLVED** (`SEC-ONB-01`) |
| **RSK-ERP-04** | Duplicate attendance sessions recorded for same class and date. | **High** | Low | High | Unique compound index `(institution_id, academic_unit_id, date, session_type)` on attendance collection. | **STAGED IN BRANCH** |
| **RSK-ERP-05** | Malicious file upload during admission document submission. | **High** | Low | High | Strict MIME-type checking (PDF/PNG/JPEG only), 5MB size limit, detached metadata storage. | **MITIGATED** |
| **RSK-ERP-06** | Privilege escalation via self-service role tampering. | **Critical** | Low | Critical | Registration strictly restricts self-service roles to `student`, `parent`, `teacher`, `institution_admin`. | **RESOLVED** |

---

## 4. Audit Trail & Compliance Logging

All administrative mutations, admission state changes, and document approvals emit structured audit events to `audit_events`:
* **Actor Identification:** Normalized user email, user ID, client IP address, and user agent.
* **Action Types:** `ADMISSION_JOIN_REQUEST_SUBMITTED`, `ADMISSION_REQUEST_APPROVED`, `DOCUMENT_VERIFIED`, `ACADEMIC_UNIT_CREATED`.
* **Category:** `ADMINISTRATIVE`, `SECURITY`, `ACADEMIC`.
* **Immutability:** Audit records are append-only; update and delete operations are prohibited on the repository.
