# ChhatraLekha Stage 0.8: Test Report
## Academic Management Core Verification

- **Repository:** `kumaribaishnabidas/ChhatraLekha`
- **Branch:** `feature/stage-0-8-academic-core`
- **Date:** November 2026
- **Test Execution Environment:** Python 3.14, Node.js v22.14.0, Windows 11

---

## 1. Test Summary

| Test Suite | Scope | Tests Run | Passed | Failed | Status |
|:---|:---|:---:|:---:|:---:|:---:|
| **Backend Pytest** | Academic Endpoints, Services & Regressions | 399 | 399 | 0 | **PASSED** |
| **Backend Lint** | Ruff Python 3.11-3.14 Code Quality | 1 | 1 | 0 | **PASSED** |
| **Frontend Vitest** | UI Components, Navigation, Modals & Workflows | 118 | 118 | 0 | **PASSED** |
| **Frontend Design Lint** | 0 Emojis, 0 Em/En Dashes, 0 Harsh Gradients, Radius/Shadow | 7 | 7 | 0 | **PASSED** |
| **Frontend Build** | Production Vite Asset Compilation | 1 | 1 | 0 | **PASSED** |

---

## 2. Backend Automated Test Suite (`test_stage_0_8_academic_core.py`)

All 11 dedicated integration tests passed with zero failures:

1. `test_academic_overview_kpis`: Validates aggregation of active academic year, department counts, programme counts, classes, subjects, enrolled students, and faculty assignments.
2. `test_academic_year_lifecycle`: Validates creating a new academic session, activating it (ensuring other years lose active status), and archiving past years while preserving historical data.
3. `test_academic_year_date_validation`: Confirms validation rejection when end date is earlier than start date.
4. `test_semester_term_date_validation`: Validates date order constraint on semester and term boundaries.
5. `test_department_and_programme_hierarchy`: Tests organizational hierarchy links between departments and degree programmes.
6. `test_subject_creation_multilingual_and_credits`: Tests subject creation with NEP 2020 credit allocation and multilingual (Hindi/Odia/Tamil) naming.
7. `test_student_enrolment_duplicate_prevention`: Verifies rejection of duplicate active student enrolments in the same academic year (`HTTP 409 Conflict`).
8. `test_student_promotion_preserves_historical_enrolment`: Verifies student promotion creates a new active enrolment while marking the previous enrolment as `status='promoted'` and `is_current=False`.
9. `test_student_section_transfer_audit_log`: Verifies section transfers log previous section, target section, timestamp, and administrative reason.
10. `test_teacher_assignment_lifecycle`: Tests faculty assignment to subjects and sections, and subsequent unassign/deletion.
11. `test_academic_calendar_events_and_unauthorized_rejection`: Tests calendar event publishing and confirms non-admin callers are denied administrative modifications (`HTTP 403 Forbidden`).

---

## 3. Frontend Automated Test Suite (`Stage08.test.jsx`)

All 8 frontend integration tests passed with zero failures:

1. `renders overview KPI metrics and active academic session`: Validates KPI cards and active academic year display.
2. `navigates to Academic Years & Terms tab and displays session registry`: Validates session table, active session badge, and term durations.
3. `navigates to Departments & Programmes tab and shows department codes`: Validates department listing, HOD names, and degree types.
4. `navigates to Classes & Sections tab and displays cohort details`: Validates grade levels, sections, room numbers, capacities, and class teachers.
5. `navigates to Curriculum & Subjects tab and renders theory/practical courses`: Validates course codes, credits, and practical lab badges.
6. `navigates to Student Enrolments and triggers Promotion dialog preserving history`: Tests opening the promotion modal and confirming promotion.
7. `navigates to Faculty Allocations and verifies teacher assignment roster`: Tests viewing teacher assignments and unassign actions.
8. `navigates to Academic Calendar and filters events by type`: Tests category filtering for holidays, exams, admissions, and institution events.

---

## 4. Frontend Design Lint Verification (`DesignLint.test.jsx`)

- **0 Emojis**: PASSED (zero emojis detected across `.jsx`, `.js`, `.css`, and `.json` files).
- **0 Em Dashes (—) / En Dashes (–)**: PASSED (zero em or en dashes in user text and translation keys).
- **0 Harsh Gradients**: PASSED (zero `bg-gradient-` or `gradient-to-` occurrences).
- **0 Backdrop Blur**: PASSED (zero `backdrop-blur` classes).
- **Corner Radius Compliance**: PASSED (zero `rounded-xl`, `rounded-2xl`, `rounded-3xl` classes).
- **Drop Shadow Compliance**: PASSED (zero `shadow-lg`, `shadow-xl`, `shadow-2xl` classes).
- **APAAR Masking**: PASSED (`sanitizeCopyPayload` properly masks raw 12-digit student IDs).

---

## 5. Production Build Verification

Executed `npm.cmd --prefix frontend run build`:
- Transformed 830 modules cleanly.
- Produced optimized production bundle: `dist/assets/AcademicSetupPage-DPNuN4J9.js` (62.78 kB raw, 9.57 kB gzip).
- Zero warnings, zero syntax errors, zero missing imports.
