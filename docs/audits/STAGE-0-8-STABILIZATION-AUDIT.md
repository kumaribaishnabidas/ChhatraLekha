# ChhatraLekha Stage 0.8 Stabilization and Production-Readiness Audit
## Academic Management Core — Pre-Stage 0.9 Baseline & Remediation Matrix

- **Repository:** `kumaribaishnabidas/ChhatraLekha`
- **Branch:** `stabilization/stage-0-8-academic-core`
- **Auditors:** Senior Software Architect, Senior Full-Stack Engineer, QA Engineer, Application Security Engineer
- **Audit Date:** November 2026
- **Target Milestone:** Stage 0.8 Stabilization before Stage 0.9 (Attendance Management System)

---

## 1. Executive Summary

Stage 0.8 implemented the foundational Academic Management Core for ChhatraLekha, delivering endpoints, schemas, database models, and frontend management interfaces for academic sessions, semester terms, institutional hierarchy (departments, programmes, classes, sections), curriculum subjects, student enrolments, promotions, section transfers, faculty assignments, and institutional calendars.

This stabilization audit assesses the production-readiness of the merged Stage 0.8 codebase. While the core domain logic, data models, and automated integration tests are architecturally sound, the audit identifies three critical deficiencies requiring remediation prior to proceeding to Stage 0.9 (Attendance Management):

1. **GET Request Write Side Effects (Idempotency Violation)**: 10 GET endpoints in `chhatralekha/app/api/academic.py` invoke `_ensure_academic_seeds()`, causing automatic writes to MongoDB during read operations. This violates HTTP GET semantics, introduces concurrency contention, and automatically pollutes newly created institutions with synthetic demo data.
2. **Frontend-to-Backend Contract Mismatches**: Several form submit handlers in `frontend/src/pages/AcademicSetupPage.jsx` submit payload field names differing from the backend Pydantic models in `chhatralekha/app/schemas/campus.py` (e.g. `admission_start` vs `admission_start_date`, `term_name` vs `name`, `dept_code` vs `department_code`, missing required `applicable_to` in subjects, etc.).
3. **Synthetic Mock Fallbacks on Request Failure**: In `AcademicSetupPage.jsx`, catch blocks across all modal submit handlers inject synthetic in-memory objects and show false success toasts when backend requests fail (e.g. on 400, 422, or 500 responses). This masks failures from users, desynchronizes frontend state from the database, and violates production integrity standards.

---

## 2. Baseline Environment & Test Counts

The baseline test suite was executed prior to modifying any code:

| Test Suite | Environment | Total Tests | Passed | Failed | Status |
|:---|:---|:---:|:---:|:---:|:---:|
| **Backend Pytest** | Python 3.14.2, in-memory MongoDB | 441 | 441 | 0 | **PASSED** |
| **Backend Ruff Linter** | Ruff v0.8+ (Python 3.11-3.14) | 1 | 1 | 0 | **PASSED** |
| **Frontend Vitest** | Node.js v22.14.0, Vite 6, React 19 | 133 | 133 | 0 | **PASSED** |
| **Frontend Design Lint** | 0 Emojis, 0 Em/En Dashes, Token rules | 7 | 7 | 0 | **PASSED** |
| **Frontend Production Build** | Vite production rollup bundle | 1 | 1 | 0 | **PASSED** |
| **i18n Check** | 13 locales, 441 translation keys | 1 | 1 | 0 | **PASSED** |

*Note: Test counts increased from Stage 0.8 original report (399 backend, 118 frontend) to 441 backend and 133 frontend following the merge of Stage 0.10 (Stateful Authentication Sessions, Refresh Token Rotation, and Revocation).*

---

## 3. Findings Classification Matrix

Each item evaluated in the Stage 0.8 Academic Management Core is classified according to the standard audit categories:
- **IMPLEMENTED AND VERIFIED**
- **IMPLEMENTED BUT NEEDS VERIFICATION**
- **PARTIALLY IMPLEMENTED**
- **NOT IMPLEMENTED**
- **DOCUMENTATION MISMATCH**

| Component / Feature | Classification | Description & Remediation Target |
|:---|:---|:---|
| **Academic Year Data Model** | `IMPLEMENTED AND VERIFIED` | MongoDB schema, Pydantic models, date boundary validators (`start_date < end_date`) verified in backend tests. |
| **Academic Year Lifecycle (Activate / Archive)** | `IMPLEMENTED AND VERIFIED` | Activation enforces single-current-year invariant across tenant; archive marks session inactive while preserving historical data. |
| **Semester / Term Model & Validation** | `IMPLEMENTED AND VERIFIED` | Semester terms validate start and end dates within academic year bounds. |
| **Flexible Hierarchy (Schools & Higher Ed)** | `IMPLEMENTED AND VERIFIED` | Supports Grade/Section for schools and Dept/Prog/Semester for colleges/universities without collision. |
| **Subject Registry & NEP 2020 Compliance** | `IMPLEMENTED AND VERIFIED` | Code, title, multilingual titles (`subject_name_hi`), credits, and practical/theory designations verified. |
| **Student Enrolment Duplicate Prevention** | `IMPLEMENTED AND VERIFIED` | Duplicate active enrolment for same student in same academic year returns `HTTP 409 Conflict`. |
| **Student Progression / Promotion** | `IMPLEMENTED AND VERIFIED` | Promotion marks prior record `is_current: false`, `status: 'promoted'` and creates new active enrolment. |
| **Section Transfer Audit Trail** | `IMPLEMENTED AND VERIFIED` | Appends immutable transfer audit log entry with previous section, target section, timestamp, and reason. |
| **Teacher Allocation & Revocation** | `IMPLEMENTED AND VERIFIED` | Allocation and safe deletion by authorized administrator verified. |
| **Academic Calendar Events** | `IMPLEMENTED AND VERIFIED` | Timezone standardized on `Asia/Kolkata`, category filtering supported. |
| **GET Route Idempotency & Seeding** | `PARTIALLY IMPLEMENTED` | 10 GET routes call `_ensure_academic_seeds()`, causing DB write side effects on read requests. Must be removed and isolated to an explicit CLI command. |
| **Frontend Form Schemas vs Pydantic Contract** | `PARTIALLY IMPLEMENTED` | Multiple field mismatches between `AcademicSetupPage.jsx` form state and `app/schemas/campus.py`. |
| **Frontend Request Error Handling** | `PARTIALLY IMPLEMENTED` | Catch blocks inject fake items into UI state and show success notifications on error. Must fail cleanly, preserve form state, and display backend errors. |
| **Hierarchy Existence Validation on Mutation** | `IMPLEMENTED BUT NEEDS VERIFICATION` | Backend endpoints verify tenant ID, but need explicit checks that parent department, programme, or class exists within the tenant before creating child entities. |
| **Cross-Tenant IDOR Protection** | `IMPLEMENTED AND VERIFIED` | Scoped via `get_scoped_institution_id()`; unauthorized cross-tenant requests fail closed (`HTTP 400` or `HTTP 403`). |
| **Role-Based Mutation Guards** | `IMPLEMENTED AND VERIFIED` | Mutations guarded by `require_permission(Permission.MANAGE_ACADEMIC_SETUP)`. Students and parents cannot modify academic structures. |
| **Authentication Backlog (SEC-AUTH-02 & 03)** | `IMPLEMENTED AND VERIFIED` | Server-side logout, refresh-token rotation, and token hash persistence in MongoDB implemented in Stage 0.10. |
| **Seed Documentation** | `DOCUMENTATION MISMATCH` | Documentation implied seed data was for test environments only, but runtime code triggered automatic seeding on all GET requests. |

---

## 4. Detailed Deficiency Analysis & Required Remediation

### 4.1 Phase 2: Frontend/Backend Contract Analysis

Analysis of `frontend/src/pages/AcademicSetupPage.jsx` against `chhatralekha/app/schemas/campus.py` identified the following contract discrepancies:

1. **Academic Year Creation**:
   - *Backend `AcademicYearIn`*: expects `admission_start_date: Optional[str]`, `admission_end_date: Optional[str]`.
   - *Frontend payload*: was sending `admission_start` and `admission_end`.
   - *Remediation*: Map frontend form fields to `admission_start_date` and `admission_end_date`.
2. **Semester Term Creation**:
   - *Backend `SemesterTermIn`*: expects `name: str`, `term_type: str = "SEMESTER"`, `academic_year: str`.
   - *Frontend payload*: was sending `term_name`, `term_type: "semester"` (lowercase), and `academic_year_id`.
   - *Table rendering*: was looking for `t.term_name` instead of `t.name || t.term_name`.
   - *Remediation*: Send `name`, uppercase `term_type`, and `academic_year`. Render both `t.name` and fallback `t.term_name`.
3. **Department Creation**:
   - *Backend `DepartmentIn`*: expects `department_code: str`, `head_of_department_name: Optional[str]`, `contact_email: Optional[str]`.
   - *Frontend payload*: was sending `dept_code`, `head_of_department`, and `email`.
   - *Table rendering*: was looking for `d.dept_code` and `d.head_of_department`.
   - *Remediation*: Send `department_code`, `head_of_department_name`, and `contact_email`. Support both in table views.
4. **Programme Creation**:
   - *Backend `ProgrammeIn`*: expects `academic_level: str` (e.g. `"UNDERGRADUATE"`), `degree_awarded: str`, `duration_years: int`, `total_semesters: int`, `approved_intake: int`.
   - *Frontend payload*: was sending `degree_type: "Bachelor"`, `total_credits: 160`, omitting required `degree_awarded`.
   - *Remediation*: Align payload with `ProgrammeIn` schema and render `degree_awarded` / `academic_level`.
5. **Subject Creation**:
   - *Backend `SubjectIn`*: expects `applicable_to: str` (required), `subject_name_hi: Optional[str]`.
   - *Frontend payload*: was sending `grade_level` and `multilingual_name`, omitting required `applicable_to` (causing 422 Unprocessable Entity).
   - *Remediation*: Send `applicable_to` and `subject_name_hi`.
6. **Student Enrolment Creation**:
   - *Backend `StudentEnrolmentIn`*: expects `academic_year: str`, `roll_number: Optional[str]`, `enrolled_date: Optional[str]`.
   - *Frontend payload*: was sending `academic_year_id` and `enrolment_number`.
   - *Remediation*: Map to `academic_year` and `roll_number`.
7. **Student Promotion**:
   - *Backend `StudentPromotionIn`*: expects `target_academic_year: str`, `target_grade_or_semester: str`, `target_section: Optional[str]`, `remarks: Optional[str]`.
   - *Frontend payload*: was sending `next_academic_year_id`, `next_grade_level`, `next_section`, `notes`.
   - *URL identifier*: was targeting `selectedEnrolment.id` which was undefined when backend returned `enrolment_id`.
   - *Remediation*: Send proper field names and use `selectedEnrolment.enrolment_id || selectedEnrolment.id`.
8. **Section Transfer**:
   - *Backend `SectionTransferIn`*: expects `target_class_id: str`, `target_section: str`, `transfer_reason: str`.
   - *Frontend payload*: was sending `new_section`, `reason`, omitting `target_class_id`.
   - *Remediation*: Send `target_class_id`, `target_section`, and `transfer_reason`.
9. **Teacher Assignment Creation & Deletion**:
   - *Backend `TeacherAssignmentIn`*: expects `subject_name: str`, `target_type: str`, `target_id: str`, `target_label: str`, `academic_year: str`.
   - *Frontend payload*: was missing `target_type` and `target_label`.
   - *Deletion*: called `asg.id` instead of `asg.assignment_id || asg.id`.
   - *Remediation*: Correct payload and deletion identifier.
10. **Calendar Event Creation & Deletion**:
    - *Backend `AcademicCalendarEventIn`*: expects `academic_year: str` (required), `event_type: str` (uppercase enum).
    - *Frontend payload*: was omitting `academic_year` and sending lowercase `'holiday'`.
    - *Deletion*: called `ev.id` instead of `ev.event_id || ev.id`.
    - *Remediation*: Include current academic year, uppercase `event_type`, and use `ev.event_id || ev.id`.

### 4.2 Phase 2: Elimination of Fake Synthetic Fallbacks

All catch blocks in `AcademicSetupPage.jsx` currently execute synthetic data injection:
```javascript
// ANTIPATTERN CURRENTLY IN CODE:
} catch (err) {
  // Silent fallback creating fake object client-side
  const fakeItem = { id: 'temp-' + Date.now(), ...formState };
  setItems(prev => [fakeItem, ...prev]);
  notify('Created successfully', 'success');
}
```
**Remediation Required**:
- Remove all fake fallback additions in `handleAddYear`, `handleAddTerm`, `handleAddDept`, `handleAddProgramme`, `handleAddClass`, `handleAddSubject`, `handleAddEnrolment`, `handlePromoteStudent`, `handleTransferSection`, `handleAddAssignment`, `handleDeleteAssignment`, `handleAddEvent`, `handleDeleteEvent`, `handleActivateYear`, `handleArchiveYear`.
- When an API call fails:
  - Do not inject any item into the state.
  - Keep the modal open.
  - Preserve user input so changes are not lost.
  - Extract and display the actual server error message using `errorMessage(err)` in both an in-modal alert banner and a toast notification.
  - Update state only on confirmed 2xx HTTP response.

### 4.3 Phase 3: Elimination of GET Route Write Side Effects

In `chhatralekha/app/api/academic.py`, `_ensure_academic_seeds()` is currently invoked in:
1. `GET /academic/overview` (line 465)
2. `GET /academic/years` (line 583)
3. `GET /academic/terms` (line 770)
4. `GET /academic/departments` (line 850)
5. `GET /academic/programmes` (line 993)
6. `GET /academic/classes` (line 1099)
7. `GET /academic/subjects` (line 1195)
8. `GET /academic/enrolments` (line 1314)
9. `GET /academic/teacher-assignments` (line 1535)
10. `GET /academic/calendar/events` (line 1659)

**Remediation Required**:
- Remove all 10 calls to `_ensure_academic_seeds` from the GET route handlers.
- Create an explicit CLI / administrative command script: `chhatralekha/app/commands/seed_academic.py`.
- Ensure the seed command is idempotent and safe for development / staging use without contaminating production tenants.
- Add an automated test verifying that querying an empty institution via all 10 GET endpoints executes purely as read-only operations and writes 0 records to MongoDB.

### 4.4 Phase 4: Multi-Tenant Security, RBAC & Hierarchy Validation

- **Tenant Isolation**: All academic database queries must include `{"institution_id": inst_id}`. When non-directorate callers invoke routes without a resolved tenant context, the system must fail closed (`HTTP 400 Bad Request`).
- **Role Permission Enforcement**: All mutations require `Permission.MANAGE_ACADEMIC_SETUP`. Students and parents lack this permission and must be rejected with `HTTP 403 Forbidden`.
- **Hierarchy Validation**:
  - Programme creation should verify that the specified `department_id` belongs to the tenant.
  - Subject creation should verify that the specified `department_id` (if provided) belongs to the tenant.
  - Student enrolment should verify that the specified `class_id` belongs to the tenant.
  - Section transfer should verify that the target `class_id` belongs to the tenant.

### 4.5 Phase 5: Authentication Backlog Verification

- `SEC-AUTH-02` (Server-side logout with token revocation): Verified. Implemented in Stage 0.10 via `POST /auth/logout` which updates session state in MongoDB (`revoked_at: now()`).
- `SEC-AUTH-03` (Refresh-token persistence & rotation): Verified. Implemented in Stage 0.10 via `POST /auth/refresh` with SHA-256 token hashing, single-use rotation, and family-based revocation.

---

## 5. Remediation Plan & Execution Sequence

1. **Backend Route Cleanup (`chhatralekha/app/api/academic.py`)**:
   - Remove automatic seeding calls from all 10 GET endpoints.
   - Retain `_ensure_academic_seeds` as a helper function for explicit development seeding.
   - Enhance hierarchy validations for parent entity existence.
2. **CLI Development Seed Command (`chhatralekha/app/commands/seed_academic.py`)**:
   - Provide explicit, safe, and repeatable seeding CLI for test/dev environments.
3. **Frontend Contract Repair (`frontend/src/pages/AcademicSetupPage.jsx`)**:
   - Align all form models and request payloads with `app/schemas/campus.py`.
   - Remove all fake fallback additions in catch blocks and `Promise.allSettled`.
   - Add error alert banners in modals; preserve form input on failure.
   - Support both canonical backend response properties and legacy table column bindings.
4. **Automated Verification Tests**:
   - Add backend tests in `chhatralekha/tests/test_stage_0_8_academic_core.py` verifying read-only GET semantics (zero write side effects), tenant isolation, and hierarchy checks.
   - Update frontend tests in `frontend/src/test/Stage08.test.jsx` verifying strict contract adherence and failure handling without fallback mocks.
5. **Execution of Full Test Suite**:
   - Pytest, Ruff, Vitest, Design Lint, and Vite production build.
6. **Documentation Update & Stabilization Report**:
   - Produce `docs/audits/STAGE-0-8-STABILIZATION-REPORT.md` with final readiness verdict.

