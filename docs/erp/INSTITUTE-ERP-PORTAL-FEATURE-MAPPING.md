# Institute ERP Portal Feature Mapping Report

**Document Reference:** `docs/erp/INSTITUTE-ERP-PORTAL-FEATURE-MAPPING.md`  
**Report Identifier:** `REP-ERP-MAP-2026-11-23`  
**Project:** ChhatraLekha Unified Education Platform  
**Evaluated Branch:** `main` (commit `dd073d9`)  
**Target:** Schools, Colleges, Institutes and Universities across India  
**Author:** Google Antigravity  

---

## 1. Feature Classification Taxonomy

Every identified feature from the master ERP directive is categorized using the project's standard classification taxonomy:

* `EXISTING — VERIFIED`: Fully implemented, active, verified with automated tests.
* `EXISTING — NEEDS IMPROVEMENT`: Implemented but requires schema extension, UI alignment, or validation hardening.
* `PARTIALLY IMPLEMENTED`: Core backend or frontend exists, but end-to-end integration is incomplete.
* `MISSING`: Functional requirement identified in ERP specification not yet present in repository.
* `REQUIRES ARCHITECTURAL INTEGRATION`: Cross-cutting capability requiring multi-module schema or RBAC coordination.
* `NOT APPLICABLE`: Unrelated or incompatible with ChhatraLekha's national mission.
* `UNVERIFIED`: Implementation exists on unmerged branch pending validation.

---

## 2. Comprehensive Module-by-Module Feature Mapping

### Module A: Institute Administration & Configuration

| Feature Name | Status | Observed / Specified Functionality | Existing Implementation | Relevant Files | Integration Action | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Institute Profile & Settings** | `EXISTING — VERIFIED` | View and edit institute metadata, contact details, affiliation, and board. | `GET /api/institutions/{id}`, `PUT /api/institutions/{id}` | `app/api/institutions.py`, `InstitutionDashboardPage.jsx` | Retain existing; add logo upload support. | P2 |
| **Academic Year Management** | `EXISTING — VERIFIED` | Define active academic year (e.g. 2024-25, 2025-26) and term boundaries. | `GET /api/academic/terms`, `POST /api/academic/terms` | `app/api/academic.py`, `AcademicSetupPage.jsx` | Fully verified. | P1 |
| **Class & Grade Management (School)** | `EXISTING — NEEDS IMPROVEMENT` | Configure offered grades (Classes 1-12) and sections (A, B, C). | Hardcoded demo catalogs + basic academic setup. | `app/api/auth.py`, `app/api/schools.py`, `AcademicSetupPage.jsx` | Introduce dynamic class/section creation per school tenant. | P0 |
| **Course & Program Management (College)** | `EXISTING — VERIFIED` | Define degree programs (UG, PG, Diploma), duration, and credit rules. | `GET/POST /api/academic/programmes` | `app/api/academic.py`, `app/repositories/programmes.py` | Add department association. | P1 |
| **Department Management** | `PARTIALLY IMPLEMENTED` | Create departments (e.g., Computer Science, Mechanical) linking faculty and students. | Referenced as text fields in users/students. | `app/api/students.py`, `app/schemas/auth.py` | Model formal `departments` collection within institution scope. | P1 |

---

### Module B: Student Management & Identity

| Feature Name | Status | Observed / Specified Functionality | Existing Implementation | Relevant Files | Integration Action | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Student Roster & Directory** | `EXISTING — VERIFIED` | Searchable, filterable student table with pagination and role scoping. | `GET /api/students` with full parameter filtering. | `app/api/students.py`, `StudentsPage.jsx` | Fully verified. | P0 |
| **Student Profile & Identity** | `EXISTING — VERIFIED` | Comprehensive profile with APAAR ID, roll number, admission quota, minor flag. | `GET /api/students/{id}` with strict tenant scoping. | `app/api/students.py`, `ProfilePage.jsx` | Fully verified. | P0 |
| **APAAR ID Masking & Validation** | `EXISTING — VERIFIED` | Verhoeff/Luhn checksum validation, privacy masking (`XXXXXXXX1234`), hashed match keys. | `apaar_validator.py`, `seal.py` | `app/services/apaar_validator.py` | Fully verified. | P0 |
| **Student Status Lifecycle** | `EXISTING — VERIFIED` | Record status transitions (`ACTIVE`, `SUSPENDED`, `ALUMNI`, `TRANSFERRED`). | `PATCH /api/students/{id}/status` with audit event logging. | `app/api/students.py` | Fully verified. | P1 |
| **Digital ID Card & Wallet** | `EXISTING — VERIFIED` | Printable/shareable digital identity card with QR verification token. | `GET /api/students/{id}/id-card.pdf`, `qr.py` | `app/services/pdf.py`, `StudentIdCardPage.jsx` | Fully verified. | P1 |

---

### Module C: Admission & Registration Processing

| Feature Name | Status | Observed / Specified Functionality | Existing Implementation | Relevant Files | Integration Action | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Self-Service Join Request** | `EXISTING — VERIFIED` | Student/parent submits registration request selecting institution and academic context. | `POST /api/onboarding/join-request` | `app/api/onboarding.py`, `OnboardingPage.jsx` | Fully verified. | P0 |
| **Admin Join Request Review Queue** | `PARTIALLY IMPLEMENTED` | Institute admin views pending join requests, reviews applicant data, approves or rejects. | Backend endpoints exist; dedicated administrative review UI pending. | `app/api/onboarding.py`, `InstitutionDashboardPage.jsx` | Build dedicated `JoinRequestsReviewWidget.jsx` in Institute Dashboard. | P0 |
| **Admission to Student Record Promotion** | `PARTIALLY IMPLEMENTED` | Approving admission request automatically provisions active student document and APAAR record. | Logic in onboarding service; needs atomic transaction wrap. | `app/api/onboarding.py`, `app/repositories/students.py` | Harden approval handler with transaction safety. | P0 |
| **Admission Status Tracking** | `EXISTING — VERIFIED` | Applicant tracks status (`PENDING_APPROVAL`, `APPROVED`, `REJECTED`). | `GET /api/onboarding/join-request/{id}` | `app/api/onboarding.py`, `OnboardingPage.jsx` | Fully verified. | P1 |

---

### Module D: Smart Attendance System

| Feature Name | Status | Observed / Specified Functionality | Existing Implementation | Relevant Files | Integration Action | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Daily & Period-wise Attendance** | `EXISTING — VERIFIED` | Mark attendance for classes/sections with session type, date, and status. | `POST /api/attendance`, `POST /api/attendance/batch` | `app/api/attendance.py`, `AttendancePage.jsx` | Fully verified. | P0 |
| **Attendance Session Hardening** | `UNVERIFIED (IN BRANCH)` | Compound unique index `(institution_id, academic_unit_id, date, session_type)`. | Implemented on `feature/stage-0-9-attendance`. | `app/core/database.py`, `test_attendance_index_creation.py` | Awaiting branch merge to `main`. | P0 |
| **Student Attendance Analytics** | `EXISTING — VERIFIED` | Aggregate attendance percentage, low-attendance warnings, threshold checks. | `GET /api/attendance/my-summary`, `GET /api/attendance/summary` | `app/api/attendance.py`, `AttendancePage.jsx` | Fully verified. | P1 |
| **Attendance Anomaly Detection** | `EXISTING — VERIFIED` | Detect ghost attendance, pattern shifts, biometric mismatches via heuristic engine. | `app/services/anomaly_detector.py` | `app/api/anomalies.py`, `AnomaliesPage.jsx` | Fully verified. | P1 |

---

### Module E: Document Management & Verification

| Feature Name | Status | Observed / Specified Functionality | Existing Implementation | Relevant Files | Integration Action | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Document Upload & Storage** | `EXISTING — VERIFIED` | Secure upload of admission certificates, marksheets, identity proofs. | `POST /api/upload`, `POST /api/upload/ocr` | `app/api/upload.py`, `UploadPage.jsx` | Fully verified. | P1 |
| **OCR Document Parsing** | `EXISTING — VERIFIED` | Automated text extraction from uploaded certificates and IDs. | Tesseract/in-memory OCR fallback service. | `app/services/ocr.py` | Fully verified. | P2 |
| **Admin Document Verification Queue**| `PARTIALLY IMPLEMENTED` | Admin inspects uploaded documents, compares with applicant data, marks verified/rejected. | Backend status flag exists; dedicated verification modal needed. | `app/api/students.py`, `VerificationPage.jsx` | Add approval actions to `VerificationPage.jsx`. | P1 |
| **Cryptographic Credential Sealing** | `EXISTING — VERIFIED` | Ed25519 asymmetric and HMAC-SHA256 tamper-proof credential signing. | `app/services/seal.py`, `app/api/tokens.py` | `app/services/seal.py`, `TokenVerificationPage.jsx`| Fully verified. | P0 |

---

### Module F & G: Reporting, Analytics & Forms

| Feature Name | Status | Observed / Specified Functionality | Existing Implementation | Relevant Files | Integration Action | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Administrative Data Tables** | `EXISTING — VERIFIED` | Paginated, sortable, filterable tables for students, faculty, and records. | React reusable table components with search and badges. | `frontend/src/components/common/` | Fully verified. | P0 |
| **Regulatory Compliance Reports** | `EXISTING — VERIFIED` | AICTE/CBSE format exports, attendance rollbooks, student registers. | `GET /api/reports/students.csv`, `GET /api/reports/attendance.pdf` | `app/api/reports.py`, `ReportsPage.jsx` | Fully verified. | P1 |
| **Institutional Dashboard Analytics**| `EXISTING — VERIFIED` | Role-specific summary widgets (School, College, University, Teacher). | Metrics aggregations for enrollment, attendance, alerts. | `SchoolDashboardPage.jsx`, `CollegeDashboardPage.jsx` | Fully verified. | P1 |

---

### Module H & J: Student Portal & Multi-Channel Communication

| Feature Name | Status | Observed / Specified Functionality | Existing Implementation | Relevant Files | Integration Action | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Student Workspace Portal** | `EXISTING — VERIFIED` | Unified learner dashboard: timetable, attendance, marks, wallet, consent. | `StudentHomePage.jsx`, `StudentWalletPage.jsx`, `StudentResultsPage.jsx` | `frontend/src/pages/` | Fully verified. | P0 |
| **Parent Portal & Ward Tracking**| `EXISTING — VERIFIED` | Cryptographically linked parent view with attendance and report cards. | `ParentPortalPage.jsx`, `app/api/parent.py` | `frontend/src/pages/ParentPortalPage.jsx` | Fully verified. | P1 |
| **Institutional Announcements** | `EXISTING — VERIFIED` | Broadcast urgent notices with mandatory acknowledgment tracking. | `POST /api/announcements`, `POST /api/announcements/{id}/acknowledge` | `app/api/announcements.py`, `AnnouncementsPage.jsx` | Fully verified. | P1 |
| **Notification Notification Bell**| `EXISTING — VERIFIED` | Real-time notifications with unread counts and mark-read actions. | `GET /api/notifications`, `PATCH /api/notifications/{id}/read` | `NotificationsPage.jsx` | Fully verified. | P1 |

---

## 3. Summary of Gaps & Strategic Recommendations

1. **Foundational Phase 1 (Zero-Risk):** Formalize the dynamic department and class hierarchy schema within `institutions.py` and `academic.py`.
2. **Administrative Admission Review:** Provide institute admins with an interactive review card to approve/reject join requests directly from `InstitutionDashboardPage.jsx`.
3. **Preserve Monolith:** All features must integrate into existing routes (`/api/academic`, `/api/onboarding`, `/api/institutions`), reusing `Principal` tenant scoping.
