# Institute ERP Integration Implementation Plan

**Document Reference:** `docs/erp/INSTITUTE-ERP-INTEGRATION-IMPLEMENTATION-PLAN.md`  
**Report Identifier:** `PLAN-ERP-INT-2026-11-23`  
**Project:** ChhatraLekha Unified Education Platform  
**Target:** Phased, Safe Implementation across Schools, Colleges, and Universities  
**Author:** Google Antigravity  

---

## 1. Incremental Implementation Stages

To evolve ChhatraLekha into a unified institute management platform without breaking existing verified capabilities, development is phased across 5 sequential implementation stages:

```
[Stage 1: Foundational Hierarchy] ➔ [Stage 2: Admission Review Queue] ➔
[Stage 3: Document Verification Lifecycle] ➔ [Stage 4: Administrative Governance] ➔
[Stage 5: Cross-Platform & Release Gate]
```

---

## 2. Detailed Staging Specifications

### Stage 1: Foundational Academic Hierarchy & Department Configuration (CURRENT STAGE)
* **Objective:** Establish dynamic academic unit and department data models supporting schools (Classes 1-12, sections) and higher education (Colleges, Universities, Polytechnics, programs, departments, semesters).
* **Scope:**
  * Backend: Enhance `app/api/schools.py` and `app/api/academic.py` with dynamic department and academic unit listing endpoints.
  * Validation: Verify institutional tenant scoping on all hierarchy endpoints (`Principal.require_scope()`).
  * Acceptance Criteria:
    - Creating an academic unit requires valid `institution_id` matching authenticated caller.
    - School classes support section grouping; college programs support semester and department linkage.
    - Zero breaking changes to existing attendance or student schemas.
* **Testing:** Pytest unit tests in `tests/test_academic.py`.

### Stage 2: Admission Processing & Join Request Review Queue
* **Objective:** Deliver the administrative review interface for self-service onboarding join requests.
* **Scope:**
  * Backend: Implement `GET /api/onboarding/join-requests` (filtered by caller's institution), `POST /api/onboarding/join-requests/{id}/approve`, and `POST /api/onboarding/join-requests/{id}/reject`.
  * Frontend: Build `JoinRequestsReviewWidget.jsx` integrated into `InstitutionDashboardPage.jsx`.
  * Acceptance Criteria:
    - Approving a join request atomically promotes applicant to active student record with APAAR ID.
    - Rejecting a join request requires administrative review notes.
    - Cross-tenant approval attempts strictly fail closed with HTTP 403.
* **Testing:** Pytest workflow tests and Vitest UI component tests.

### Stage 3: Document Verification & Administrative Approval Pipeline
* **Objective:** Expand the upload module into a full administrative verification workflow.
* **Scope:**
  * Backend: Add verification status mutation endpoints (`PATCH /api/students/{id}/documents/{doc_id}/status`) with reviewer identity and timestamp tracking.
  * Frontend: Enhance `VerificationPage.jsx` with document preview, comparison against applicant profile, and one-click approve/reject actions.
  * Acceptance Criteria:
    - Non-administrators cannot alter document verification status.
    - State transitions emit audit log entries (`DOCUMENT_VERIFIED`, `DOCUMENT_REJECTED`).

### Stage 4: Institutional Analytics & Multi-Role Reporting
* **Objective:** Provide school principals, college deans, and university registrars with integrated operational reporting.
* **Scope:**
  * Aggregate daily attendance rates, fee collection milestones, admission conversion metrics, and compliance alerts.
  * Export AICTE and CBSE format compliance registers.

### Stage 5: Cross-Platform Sync & Release Readiness Gate
* **Objective:** Validate Android application, Linux desktop client, and responsive web portal against the unified ERP APIs.

---

## 3. Migration & Backward Compatibility Strategy

1. **Non-Destructive Schema Evolution:** New fields on existing collections (`students`, `institutions`) are defined as optional with safe fallback defaults in Pydantic models.
2. **Zero In-Place Rewrites:** Existing attendance records, student APAAR profiles, and cryptographic credential seals remain completely untouched.
3. **Rollback Procedures:** Each stage is independently committable. In the event of an unexpected regression, git revert operates cleanly at stage boundaries without affecting historical data.
