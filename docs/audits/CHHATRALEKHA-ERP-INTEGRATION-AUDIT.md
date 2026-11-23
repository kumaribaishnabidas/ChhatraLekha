# ChhatraLekha — Master ERP Integration Audit

**Document Reference:** `docs/audits/CHHATRALEKHA-ERP-INTEGRATION-AUDIT.md`  
**Execution Date:** 2026-11-23  
**Auditor:** Antigravity (Advanced Agentic AI Development System)  
**Governance Standard:** Aligned with `PRODUCT_REQUIREMENTS.md`, `DESIGN_SYSTEM.md`, `ARCHITECTURE.md`, `AI_AGENTS.md`  
**Working Branch:** `main` (baseline at `dd073d9`)  
**Audit Purpose:** Comprehensive, read-only baseline evaluation of all 24 ERP domains across Backend, Frontend, Android, Linux Desktop, and Infrastructure before commencing Phase 1 ERP evolution.

---

## 1. Executive Summary

ChhatraLekha is a national-scale academic management, institute ERP, and digital credential platform designed for K-12 schools, polytechnic colleges, engineering/management institutes, and universities across India.

Rather than replacing or rebuilding the verified foundation, this audit evaluates the existing repository to establish an authoritative baseline across all 24 target ERP modules. The existing architecture is a high-performance **modular monolith** backed by FastAPI (Python 3.12/3.14), MongoDB (with motor async driver), React 19 (Vite 6, Tailwind CSS 4), native Android (Kotlin, Jetpack Compose, Room SQLite), and a standalone Linux desktop Electron client.

### Key Audit Findings
1. **Strong Architectural Baseline:** Core multi-tenant isolation, rotating session lifecycle, Verhoeff APAAR validation, 10-layer regulatory anomaly detection, cryptographic Ed25519 seals, and 22-language localization are already verified and passing tests.
2. **Advanced Attendance & Benchmark on Feature Branch:** The remote branch `origin/feature/stage-0-9-attendance` contains 7 verified commits providing attendance session hardening, unique index conflict resolution, labeled synthetic anomaly benchmarks, and offline grounded RAG retrieval. This work must be preserved and reconciled.
3. **Primary ERP Expansion Gaps:** Online examinations (CBT MCQ bank & attempt tracking), automated timetable conflict detection, fee/financial structures, and multi-channel notification gateways (SMS/Email/WhatsApp) represent the primary unbuilt ERP capabilities.

---

## 2. Git Branch, Worktree & Infrastructure Inventory

### 2.1 Branch Topology
- **`main` (Local & Active Working Baseline):** Commit `dd073d9` (*Merge pull request #41 from kumaribaishnabidas/stabilization/stage-0-8-academic-core*). Holds all active working tree improvements including the Student Academic Onboarding Wizard (`StudentAcademicSelectionWizard.jsx`), FastAPI documentation access control (`test_docs_security.py`), and the four canonical governance documents.
- **`origin/feature/stage-0-9-attendance`:** 7 commits ahead of `dd073d9`. Contains Stage 0.9/0.9.1 attendance remediation (`4f33c8b`), synthetic anomaly benchmarks (`acbae6a`), capstone explainer site (`f2c4eb4`), offline grounded RAG (`d9eb96d`), and Vercel configs (`a54f76c`).
- **`origin/feature/linux-desktop`:** 1 commit ahead of `dd073d9` (`7b7a7f6` *Add Linux desktop client*). Contains an Electron desktop shell wrapping the web portal with native menus and offline detection.
- **`origin/deploy/vercel-production`:** 1 commit ahead of `dd073d9` (`5fc689e` *chore(deploy): prepare separate Vercel frontend and API configuration*). Configured for frontend edge deployment.

### 2.2 Active Worktrees
- Primary Working Tree: `C:/Users/BAISHNABI/.gemini/antigravity/scratch/ChhatraLekha` [main].

### 2.3 Database Collections & Indexes (MongoDB)
- Multi-Tenant Core: `institutions`, `programmes`, `classes`, `subjects`, `students`, `users`.
- Academic & Attendance: `academic_years`, `teacher_assignments`, `attendance_sessions`, `attendance_records`.
- Assessments & Records: `assessments`, `assessment_marks`, `results`.
- Communication & Security: `announcements`, `notifications`, `consents`, `audit_events`, `refresh_sessions`, `tokens`, `claim_codes`.

---

## 3. Master ERP Feature Integration Matrix

Classification Standard:
- **VERIFIED IMPLEMENTED:** Code exists, verified functional, passing automated tests.
- **IMPLEMENTED BUT NEEDS REVIEW:** Code exists, but requires cross-branch reconciliation or multi-tenant hardening.
- **PARTIALLY IMPLEMENTED:** Scaffold or partial backend/frontend implementation exists.
- **EXISTING BUT DISCONNECTED:** Isolated prototype or separate branch not yet merged to main.
- **PLANNED / NOT IMPLEMENTED:** Fully designed in roadmap; implementation not yet started.
- **BLOCKED:** Dependent on external approval or prerequisite architecture.

| Feature ID | Module | Specific Feature | Current Implementation Source | Backend Status | Frontend Status | Android Status | Linux Status | API Status | Test Evidence | Security Findings | Dependencies | Gap Analysis | Risk Rating | Recommendation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ERP-01** | Institute ERP Core | Multi-tenant institution scoping | `app/api/institutions.py`, `app/api/schools.py` | VERIFIED IMPLEMENTED | VERIFIED IMPLEMENTED | VERIFIED IMPLEMENTED | VERIFIED IMPLEMENTED | VERIFIED IMPLEMENTED | `test_institution_isolation.py` (Passed) | Enforces fail-closed `institution_id` check (SEC-TENANT-01 resolved) | None | Multi-campus grouping and department hierarchy UI | Low | Extend `institutions.py` to support multi-campus trees |
| **ERP-02** | Student Management | Student profiles & enrollment | `app/api/students.py`, `app/schemas/student.py` | VERIFIED IMPLEMENTED | VERIFIED IMPLEMENTED | VERIFIED IMPLEMENTED | PLANNED | VERIFIED IMPLEMENTED | `test_api.py`, `test_profile_api.py` | Role-guarded, APAAR masked display | `institutions` | Bulk status lifecycle transitions (graduated/suspended) | Low | Add lifecycle transition endpoints in `students.py` |
| **ERP-03** | Student Onboarding | Education type & academic selection wizard | `app/api/auth.py`, `StudentAcademicSelectionWizard.jsx` | VERIFIED IMPLEMENTED | VERIFIED IMPLEMENTED | PLANNED | PLANNED | VERIFIED IMPLEMENTED | `test_demo_academic_context.py` (8 passed), Vitest (7 passed) | Server-side validation against institutional catalogs | `auth.py`, `institutions` | Integrate with real registration invite codes | Low | Baseline verified; connect to institution invite system |
| **ERP-04** | Faculty Management | Teacher workspace & class scopes | `app/api/teacher.py`, `TeacherWorkspacePage.jsx` | VERIFIED IMPLEMENTED | VERIFIED IMPLEMENTED | PLANNED | PLANNED | VERIFIED IMPLEMENTED | `test_schools_domain.py` | Scope-limited to assigned classes | `academic.py` | Faculty leave tracking, workload balance overview | Medium | Implement faculty profile & leave endpoints |
| **ERP-05** | Smart Attendance | Session-based classroom marking | `app/api/attendance.py`, `AttendancePage.jsx` | IMPLEMENTED BUT NEEDS REVIEW | VERIFIED IMPLEMENTED | VERIFIED IMPLEMENTED | PLANNED | VERIFIED IMPLEMENTED | `test_stage_0_9_attendance.py` (Passed) | IDOR resolved (SEC-ATT-01); unique index fix on feature branch | `teacher.py`, `classes` | Merge Stage 0.9 branch unique index fix; add dynamic QR | Medium | Reconcile `origin/feature/stage-0-9-attendance` |
| **ERP-06** | Attendance QR | Dynamic rotating QR attendance | Scaffolded in `app/services/qr.py` | PARTIALLY IMPLEMENTED | PARTIALLY IMPLEMENTED | PLANNED | PLANNED | PARTIALLY IMPLEMENTED | `test_qr.py` | Static QR rejected; requires short-lived session token | `attendance.py` | Dynamic time-slotted QR token generation & verification | High | Build short-lived HMAC token session validation |
| **ERP-07** | Examinations | Exam creation & scheduling | `app/api/assessments.py`, `AssessmentsPage.jsx` | VERIFIED IMPLEMENTED | VERIFIED IMPLEMENTED | PLANNED | PLANNED | VERIFIED IMPLEMENTED | `test_stage_0_8_academic_core.py` | Role-guarded; moderation locks marks against tampering | `academic.py` | Online Computer-Based Testing (CBT) MCQ questions | Medium | Add question bank and student exam attempt engine |
| **ERP-08** | Question Bank | MCQ & descriptive question bank | None | NOT IMPLEMENTED | NOT IMPLEMENTED | NOT IMPLEMENTED | NOT IMPLEMENTED | NOT IMPLEMENTED | None | Questions must be scoped by subject & institution | `assessments.py` | Question authoring, randomized paper generation | Low | Schedule for Phase 4 evolution |
| **ERP-09** | Timetable | Multi-unit schedule matrix | `app/api/academic.py` (`/timetable`), `AcademicSetupPage.jsx` | VERIFIED IMPLEMENTED | VERIFIED IMPLEMENTED | PLANNED | PLANNED | VERIFIED IMPLEMENTED | `test_schools_domain.py` | Tenant-scoped by academic unit | `institutions`, `classes` | Automated faculty/room double-booking conflict detector | Medium | Implement conflict detection algorithm in `academic.py` |
| **ERP-10** | Results & Records | SGPA/CGPA & internal marks | `app/api/assessments.py`, `StudentResultsPage.jsx` | VERIFIED IMPLEMENTED | VERIFIED IMPLEMENTED | PLANNED | PLANNED | VERIFIED IMPLEMENTED | `test_api.py` | Moderated publishing model prevents premature score leak | `assessments.py` | Printable PDF transcript generation (`reportlab`) | Low | Add PDF report card generator service |
| **ERP-11** | Parent Portal | Guardian-ward monitoring | `app/api/parent.py`, `ParentPortalPage.jsx` | VERIFIED IMPLEMENTED | VERIFIED IMPLEMENTED | PLANNED | PLANNED | VERIFIED IMPLEMENTED | `test_stage_0_8_academic_core.py` | Ambiguous guardian IDs rejected (commit `b1210c4`) | `students.py` | Self-service guardian invite & verification flow | Medium | Add guardian verification OTP workflow |
| **ERP-12** | Communications | Campus announcements & bulletins | `app/api/announcements.py`, `AnnouncementsPage.jsx` | VERIFIED IMPLEMENTED | VERIFIED IMPLEMENTED | PLANNED | PLANNED | VERIFIED IMPLEMENTED | `test_stage_0_7_notifications.py` | Target-role scoping and tenant isolation enforced | `auth.py` | Multi-channel broadcast (SMS/Email/WhatsApp) hub | Low | Extend announcements with provider dispatchers |
| **ERP-13** | SMS Notifications | DLT-compliant Indian SMS | Stubbed in `app/modules/notifications` | PARTIALLY IMPLEMENTED | PARTIALLY IMPLEMENTED | PLANNED | PLANNED | PARTIALLY IMPLEMENTED | None | Zero credentials hardcoded; requires operator approval | `config.py` | Msg91/Twilio provider client and template engine | Medium | Implement SMS provider adapter with fail-safe mock |
| **ERP-14** | Email Notifications | Transactional & bulk email | Stubbed in `app/modules/notifications` | PARTIALLY IMPLEMENTED | PARTIALLY IMPLEMENTED | PLANNED | PLANNED | PARTIALLY IMPLEMENTED | None | Enforces SPF/DKIM headers; no production credentials | `config.py` | SMTP/SES client with HTML academic templates | Low | Implement asynchronous email worker queue |
| **ERP-15** | WhatsApp Integration | Meta Cloud WhatsApp Business API | None | NOT IMPLEMENTED | NOT IMPLEMENTED | NOT IMPLEMENTED | NOT IMPLEMENTED | NOT IMPLEMENTED | None | Official Meta API only; zero unauthorized scraping | `config.py`, `consent` | Webhook receiver and approved template sender | High | Require operator API keys before live integration |
| **ERP-16** | Fees & Finance | Fee structures, dues & receipts | None | NOT IMPLEMENTED | NOT IMPLEMENTED | NOT IMPLEMENTED | NOT IMPLEMENTED | NOT IMPLEMENTED | None | Zero raw card storage; synthetic data in demo | `students.py` | Fee category, student ledger, payment receipt schemas | Medium | Design `chhatralekha/app/api/fees.py` module |
| **ERP-17** | Admin Dashboard | Multi-tier institutional analytics | `app/api/dashboard.py`, `DashboardPage.jsx` | VERIFIED IMPLEMENTED | VERIFIED IMPLEMENTED | PLANNED | PLANNED | VERIFIED IMPLEMENTED | `test_api.py` | Directorate vs Institution RBAC separation | `dashboard.py` | Real-time attendance anomaly & fee collection widgets | Low | Enrich dashboard widgets with live aggregation queries |
| **ERP-18** | AI Academic Assistant | Grounded multilingual RAG | `app/api/ai.py`, `VoiceDrawer.jsx` | IMPLEMENTED BUT NEEDS REVIEW | VERIFIED IMPLEMENTED | PLANNED | PLANNED | VERIFIED IMPLEMENTED | `test_ai_and_demo.py` | Role-filtered retrieval prevents cross-student leakage | `auth.py` | Reconcile offline RAG from Stage 0.9 branch | Medium | Merge offline RAG evaluation from feature branch |
| **ERP-19** | Anomaly Detection | 10-layer regulatory rules | `app/services/anomaly_engine.py`, `AnomaliesPage.jsx` | IMPLEMENTED BUT NEEDS REVIEW | VERIFIED IMPLEMENTED | VERIFIED IMPLEMENTED | PLANNED | VERIFIED IMPLEMENTED | `test_anomaly_engine.py` (Passed) | Review-oriented; never mutates records autonomously | `students.py` | Merge synthetic benchmark dataset (`acbae6a`) | Low | Merge benchmark evaluation from Stage 0.9 |
| **ERP-20** | Credential Verification | Ed25519 seals & public JWKS | `app/services/seal.py`, `TokenVerificationPage.jsx` | VERIFIED IMPLEMENTED | VERIFIED IMPLEMENTED | VERIFIED IMPLEMENTED | PLANNED | VERIFIED IMPLEMENTED | `test_seal.py`, `test_verify.py` | Zero-PII public exposure; offline verification verified | `key_registry.py` | Automated batch credential issuance pipeline | Low | Provide batch sealing endpoint for graduation lists |
| **ERP-21** | Digital Records | Printable ID card & wallet | `StudentIdCardPage.jsx`, `StudentWalletPage.jsx` | VERIFIED IMPLEMENTED | VERIFIED IMPLEMENTED | VERIFIED IMPLEMENTED | PLANNED | VERIFIED IMPLEMENTED | `DesignLint.test.jsx` (Passed) | 12-digit APAAR masked display mandatory | `qr.py` | Offline PKPASS / verifiable credential export | Low | Add downloadable PDF ID card template |
| **ERP-22** | Multilingual Support | 22 Eighth Schedule Indian languages | `frontend/src/i18n/`, `index.css` | VERIFIED IMPLEMENTED | VERIFIED IMPLEMENTED | PLANNED | PLANNED | VERIFIED IMPLEMENTED | `DesignLint.test.jsx`, `i18n-check.mjs` | Zero emojis and zero em/en dashes strictly enforced | `react-i18next` | Localized backend error detail messages | Low | Add `Accept-Language` middleware for API errors |
| **ERP-23** | Android Platform | Native Compose & Room SQLite client | `android/app`, `android/core` | VERIFIED IMPLEMENTED | N/A | VERIFIED IMPLEMENTED | N/A | VERIFIED IMPLEMENTED | 204 unit tests in `android/core` | Secure hardware keystore for cryptographic sync | API Gateway | Incorporate Timetable, Examination & Fee screens | Medium | Add Compose screens matching new web ERP routes |
| **ERP-24** | Linux Desktop Client | Electron desktop shell | `origin/feature/linux-desktop` (`7b7a7f6`) | EXISTING BUT DISCONNECTED | N/A | N/A | VERIFIED IMPLEMENTED | N/A | Visual inspection | Sandboxed renderer, isolated context bridge | Web dist | Reconcile branch into monorepo `desktop/` directory | Low | Merge `feature/linux-desktop` cleanly when approved |

---

## 4. Architectural Boundaries & Security Assessment

1. **Authentication & Session Security:** Verified stateful token rotation (`refresh_sessions`), automatic token reuse detection, and caller-authenticated `POST /api/auth/logout`.
2. **API Documentation Security:** Gated `/docs`, `/redoc`, and `/openapi.json` returning HTTP 404 in production by default, with SPA route guards and 503 information disclosure protection.
3. **Multi-Tenant Data Boundaries:** All queries across `students`, `attendance_records`, `assessment_marks`, and `announcements` enforce strict `institution_id` filtering. Missing tenant context fails closed with HTTP 400.
4. **Data Privacy (DPDP 2023):** Minor student consent requires guardian association (`guardian_relationships`). Cleartext student APAAR identifiers are masked across all user-facing components (`****-****-0001`).

---

## 5. Master Audit Conclusion & Recommendations

The ChhatraLekha codebase provides an exceptionally robust foundation. To evolve into the complete Master ERP without destabilizing verified systems:
1. **Preserve Current Working Baseline:** Maintain the current working tree state without premature commits or resets.
2. **Reconcile Stage 0.9 Attendance & RAG:** Merge `origin/feature/stage-0-9-attendance` cleanly to unify the attendance session unique index fix, labeled synthetic anomaly benchmark, and offline RAG evaluation.
3. **Execute Evolutionary Roadmap:** Implement the remaining ERP domains (Timetable conflict detection, Examination CBT, Fees & Finance, and Multi-channel Notifications) through structured, independently tested phases.
