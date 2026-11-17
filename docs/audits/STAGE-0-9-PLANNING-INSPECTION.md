# ChhatraLekha — Stage 0.9 Attendance Management System
## Phase 0.9.0: Repository Inspection & Architectural Design Alignment Report

**Date:** November 9, 2026  
**Stage:** 0.9.0 (Planning, Inspection & Architectural Alignment)  
**Status:** **READY FOR IMPLEMENTATION**  
**Role:** Senior Software Architect, Application Security Engineer & QA Lead  
**Prerequisites Verified:**
- PR #41 merged into `main` at commit `dd073d9`.
- All 20 CI checks passed on PR #41 merge commit.
- Stage 0.8.1 Academic Core stabilization complete.
- Python backend dependencies remediated (0 CVEs across all direct and transitive dependencies).

---

## 1. Executive Summary

This report completes Phase 0.9.0 of Stage 0.9 (Attendance Management System). In accordance with the Stage 0.9 charter:
> *"Inspect the repository before implementation. This plan must be checked against the current architecture, API conventions, and security controls... Identify reusable components and avoid duplicate models or APIs... Report blockers or conflicts before implementation."*

The repository was thoroughly inspected across backend models, API routes, security/RBAC layers, database schemas, frontend pages, and existing unit tests. 

While an initial draft of the attendance module existed from prior iterations (`chhatralekha/app/api/attendance.py`, `frontend/src/pages/AttendancePage.jsx`, `test_stage_0_9_attendance.py`), our audit revealed **10 critical architectural mismatches, tenant-isolation vulnerabilities, and frontend anti-patterns** that conflict directly with the newly stabilized Stage 0.8.1 Academic Core and the platform's security standards.

This document details all discovered discrepancies, provides the unified target architecture, and establishes the formal implementation roadmap for Phases 0.9.1 through 0.9.5.

---

## 2. Current Implementation Inventory

| Component | File Path | Existing State | Alignment Status |
| :--- | :--- | :--- | :--- |
| **Backend Endpoints** | `chhatralekha/app/api/attendance.py` (1,128 lines) | Implements sessions, roster, policy, corrections, reports, my-summary, teacher-classes | **Needs Contract & Security Repair** |
| **Pydantic Schemas** | `chhatralekha/app/schemas/campus.py` (lines 322–445) | Defines 10 attendance request/response schemas | **Align with Academic Core** |
| **Models & Enums** | `chhatralekha/app/models/enums.py` | `AttendanceMode` (`DAILY`, `PERIOD_WISE`), `AttendanceStatus` (6 statuses) | **Aligned** |
| **RBAC Permissions** | `chhatralekha/app/core/rbac.py` | `RECORD_ATTENDANCE`, `VIEW_ATTENDANCE` mapped across roles | **Aligned** |
| **Backend Test Suite** | `chhatralekha/tests/test_stage_0_9_attendance.py` (513 lines) | 10 tests passing, but relying on legacy query assumptions | **Expand for Regression & Isolation** |
| **Frontend UI** | `frontend/src/pages/AttendancePage.jsx` (1,185 lines) | Roll call, student summary, reports, policy, corrections modal | **Requires Frontend Contract Repair** |
| **Frontend Tests** | `frontend/src/test/Stage09.test.jsx` (312 lines) | 5 tests passing with mock data | **Update for Repaired Contracts** |
| **App Routing** | `frontend/src/App.jsx` | Routes `/attendance` and `/me/attendance` | **Fix Duplicate Route Definition** |
| **Navigation Config** | `frontend/src/modules/navigation/NavigationConfig.js` | Sidebar and mobile bottom bar links for attendance | **Aligned** |

---

## 3. Discovered Architectural Mismatches & Security Gaps

Our deep codebase inspection uncovered 10 specific issues in the pre-existing attendance implementation that must be repaired:

### Gap 1: Teacher Assignment Field Mismatch (`class_id` vs `target_id`)
- **Issue:** In `chhatralekha/app/api/attendance.py:74`, the authorization helper `_is_teacher_assigned_to_target` queries `teacher_assignments` with:
  ```python
  query_target = [{"class_id": target_id}]
  ```
- **Conflict:** In `chhatralekha/app/api/academic.py:1529-1531`, `create_teacher_assignment` stores assignments using the schema:
  ```python
  "target_type": payload.target_type,  # e.g., "CLASS"
  "target_id": payload.target_id,      # e.g., "CLS-10A"
  ```
- **Consequence:** Real teacher assignments stored by the Stage 0.8 Academic Core do not have a `class_id` key, causing legitimate assigned teachers to be falsely rejected with HTTP 403.
- **Resolution:** `_is_teacher_assigned_to_target` must query `{"$or": [{"target_id": target_id}, {"class_id": target_id}]}` and match `target_type == "CLASS"`.

### Gap 2: Silent Demo Bypass in Teacher Assignment Authorization
- **Issue:** In `chhatralekha/app/api/attendance.py:101-104`:
  ```python
  any_asg = await db["teacher_assignments"].find_one({"institution_id": inst_id})
  if not any_asg:
      # No assignments configured yet for institution; allow initial setup
      return True
  ```
- **Violation:** This silent fallback allows any teacher to record attendance for *any* class if an institution has not yet populated assignments. This directly violates the platform's core security mandate: *"No silent fallback to synthetic data, no bypass of access control."*
- **Resolution:** Remove this bypass. If an institution has not configured teacher assignments, unassigned teachers must be denied with a clear, actionable error message instructing the administrator to configure faculty assignments.

### Gap 3: Student Enrolment Query Mismatches (Case Sensitivity & Key Name)
- **Issue:** In `chhatralekha/app/api/attendance.py:404-412`, `/attendance/roster` queries `student_enrolments` with:
  ```python
  enrol_query = {
      "institution_id": inst_id,
      "class_id": class_id,
      "is_current": True,
      "status": "active",          # <--- Lowercase!
      "academic_year_id": year_id  # <--- Field name mismatch!
  }
  ```
- **Conflict:** In `app/api/academic.py:1289-1296`, enrolments are created with:
  ```python
  "academic_year": payload.academic_year, # <--- 'academic_year', not 'academic_year_id'
  "status": "ACTIVE",                     # <--- Uppercase!
  ```
- **Consequence:** Because MongoDB field queries are case-sensitive, this query consistently returned zero enrolments, forcing the endpoint into its fallback path (`students` collection).
- **Resolution:** Query `status` with `{"$in": ["ACTIVE", "active"]}` and query both `academic_year` and `academic_year_id`.

### Gap 4: Hardcoded Synthetic Roster Percentages
- **Issue:** In `attendance.py:429` and `446`:
  ```python
  recent_attendance_rate=95.0  # and 92.5
  ```
- **Violation:** The roster endpoint emits hardcoded floating-point rates (`95.0%`, `92.5%`) for every student rather than computing their actual recent attendance rate or returning `None` when no prior sessions exist.
- **Resolution:** Calculate the actual attendance rate dynamically from `attendance_records` over the last 30 days, or return `None` (null) if no records exist.

### Gap 5: Tenant Isolation Omission in Summary Endpoint (`/my-summary`)
- **Issue:** In `attendance.py:993`:
  ```python
  records = await db["attendance_records"].find({"student_id": resolved_id}).to_list(500)
  ```
- **Security Vulnerability:** The query fails to include `"institution_id": inst_id`. If student IDs or roll numbers collide across institutions, a student or guardian could receive attendance records from an unrelated tenant.
- **Resolution:** Strictly scope the query with `{"institution_id": inst_id, "student_id": resolved_id}`.

### Gap 6: Guardian Ambiguity Resolution Gap
- **Issue:** In `attendance.py:966-972`, if a parent supplies a student ID, the system looks up `students.find_one({"$or": [{"apaar_id": resolved_id}, {"_id": resolved_id}]})` without an institution filter.
- **Security Vulnerability:** This re-introduces the exact cross-tenant student lookup ambiguity that was patched in `app/api/parent.py` under commit `b1210c4`.
- **Resolution:** Validate guardian links using tenant-scoped queries against verified relationships: `{"parent_user_id": principal.subject, "student_id": resolved_id, "status": "VERIFIED"}`.

### Gap 7: Intra-Session Duplicate Student Vulnerability
- **Issue:** `AttendanceBatchSubmitIn.records` does not validate that each `student_id` is unique within the submitted batch.
- **Business Rule Violation:** Business Rule 5 requires: *"Prevent duplicate attendance records for the same student and attendance session."*
- **Resolution:** Enforce unique student IDs in `AttendanceBatchSubmitIn` Pydantic validator, and insert records with a unique compound index on `(institution_id, session_id, student_id)`.

### Gap 8: Session Duplicate Check Conflict between Modes
- **Issue:** `duplicate_query` in `attendance.py:142-152` does not distinguish between `DAILY` (where `period_number` is null) and `PERIOD_WISE` (where `period_number` is required).
- **Resolution:**
  - For `DAILY` sessions: Duplicate key is `(institution_id, target_id, session_date, mode="DAILY")`.
  - For `PERIOD_WISE` sessions: Duplicate key is `(institution_id, target_id, session_date, period_number, subject_id, mode="PERIOD_WISE")`.

### Gap 9: Frontend Synthetic Fallback and Fake Success Anti-Patterns
- **Issue:** `frontend/src/pages/AttendancePage.jsx` contains:
  1. Fake classes injected when API returns empty (`lines 102-105`).
  2. Fake student summary injected on catch (`lines 126-154`).
  3. Fake student roster injected on network error (`lines 191-202`).
  4. Fake success notifications on failed submissions:
     ```javascript
     catch (err) {
       notify(`Attendance recorded for ${targetLabel}.`, 'success')
     }
     ```
- **Violation:** Violates the Stage 0.8.1 stabilization mandate.
- **Resolution:** Remove all fake fallbacks. On error, display clear banner errors, keep form inputs intact, and display authentic empty states.

### Gap 10: Duplicate Route Definition in `frontend/src/App.jsx`
- **Issue:** `path="/me/attendance"` is defined twice:
  - Lines 332–338: renders `<AttendancePage />`.
  - Lines 384–392: renders `<WorkspacePlaceholderPage />`.
- **Resolution:** Delete the duplicate placeholder route in `App.jsx`.

---

## 4. Proposed Target Data Model & MongoDB Collections

### 4.1 Collection: `attendance_policies`
Stores institutional attendance configuration and compliance rules.
```json
{
  "_id": "POL-INST-0421",
  "institution_id": "INST-0421",
  "mode": "DAILY",
  "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
  "periods_per_day": 7,
  "minimum_attendance_percentage": 75.0,
  "late_arrival_threshold_minutes": 15,
  "early_departure_threshold_minutes": 15,
  "consecutive_absent_alert_threshold": 3,
  "allowed_statuses": ["PRESENT", "ABSENT", "LATE", "EXCUSED", "ON_LEAVE", "HALF_DAY"],
  "updated_by": "USR-ADMIN-01",
  "updated_at": "2026-11-09T02:00:00Z"
}
```
**Indexes:**
- `{"institution_id": 1}` (Unique)

### 4.2 Collection: `attendance_sessions`
Represents an attendance roll-call session for a cohort class or subject.
```json
{
  "_id": "ATT-INST-0421-20261109-CLS10A",
  "session_id": "ATT-INST-0421-20261109-CLS10A",
  "institution_id": "INST-0421",
  "session_date": "2026-11-09",
  "mode": "DAILY",
  "period_number": null,
  "target_type": "CLASS",
  "target_id": "CLS-10A",
  "target_label": "Class 10 Section A",
  "subject_id": "SUB-MATH",
  "subject_name": "Mathematics",
  "academic_year": "2025-26",
  "recorded_by": "USR-TEA-01",
  "total_students": 30,
  "present_count": 28,
  "absent_count": 1,
  "late_count": 1,
  "excused_count": 0,
  "created_at": "2026-11-09T03:30:00Z"
}
```
**Indexes:**
- `{"institution_id": 1, "target_id": 1, "session_date": 1, "period_number": 1, "subject_id": 1}` (Unique)
- `{"institution_id": 1, "session_date": -1}`
- `{"institution_id": 1, "target_id": 1}`

### 4.3 Collection: `attendance_records`
Stores individual student attendance marks for each session with an immutable audit trail.
```json
{
  "_id": "REC-ATT-0421-STU001",
  "session_id": "ATT-INST-0421-20261109-CLS10A",
  "institution_id": "INST-0421",
  "session_date": "2026-11-09",
  "student_id": "992100000001",
  "student_name": "Aarav Patel",
  "target_id": "CLS-10A",
  "target_label": "Class 10 Section A",
  "subject_id": "SUB-MATH",
  "subject_name": "Mathematics",
  "academic_year": "2025-26",
  "status": "PRESENT",
  "remarks": null,
  "audit_trail": [
    {
      "previous_status": "ABSENT",
      "new_status": "PRESENT",
      "changed_by": "USR-ADMIN-01",
      "changed_by_name": "Principal Sharma",
      "reason": "Late arrival bus delay verified",
      "review_notes": "Approved per transport log",
      "timestamp": "2026-11-09T05:00:00Z"
    }
  ],
  "created_at": "2026-11-09T03:30:00Z"
}
```
**Indexes:**
- `{"institution_id": 1, "session_id": 1, "student_id": 1}` (Unique)
- `{"institution_id": 1, "student_id": 1, "session_date": -1}`
- `{"institution_id": 1, "target_id": 1, "session_date": -1}`

### 4.4 Collection: `attendance_corrections`
Auditable change requests submitted by teachers, students, or guardians.
```json
{
  "_id": "CORR-INST-0421-a1b2c3",
  "id": "CORR-INST-0421-a1b2c3",
  "institution_id": "INST-0421",
  "session_id": "ATT-INST-0421-20261109-CLS10A",
  "student_id": "992100000001",
  "student_name": "Aarav Patel",
  "target_id": "CLS-10A",
  "session_date": "2026-11-09",
  "previous_status": "ABSENT",
  "requested_status": "EXCUSED",
  "reason": "Medical appointment certificate submitted",
  "supporting_document_url": null,
  "requested_by": "USR-TEA-01",
  "requested_by_name": "Prof. Rajesh Kumar",
  "requested_at": "2026-11-09T04:00:00Z",
  "status": "PENDING",
  "reviewed_by": null,
  "reviewed_at": null,
  "review_notes": null
}
```
**Indexes:**
- `{"institution_id": 1, "status": 1, "requested_at": -1}`
- `{"institution_id": 1, "session_id": 1, "student_id": 1}`

---

## 5. API Contracts & Endpoint Specifications

All endpoints are prefixed with `/attendance` and enforce tenant context via `principal.require_tenant_context()`.

| Method | Endpoint | Permission | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/attendance/sessions` | `RECORD_ATTENDANCE` | Submit batch attendance session; checks teacher assignment and duplicate prevention |
| `GET` | `/attendance/sessions` | `VIEW_ATTENDANCE` | List submitted sessions with date and class filters |
| `GET` | `/attendance/sessions/{id}`| `VIEW_ATTENDANCE` | Retrieve session details and full student roll marks |
| `GET` | `/attendance/roster` | `RECORD_ATTENDANCE` | Load eligible students from `student_enrolments` (`status: "ACTIVE"`) |
| `GET` | `/attendance/policy` | `VIEW_ATTENDANCE` | Retrieve institutional policy rules |
| `POST` | `/attendance/policy` | `MANAGE_ACADEMIC_SETUP`| Update institutional policy (admin only) |
| `POST` | `/attendance/corrections` | `RECORD_ATTENDANCE` / `VIEW_OWN_RECORD` | Submit formal adjustment request with mandatory reason |
| `GET` | `/attendance/corrections` | `VIEW_ATTENDANCE` | List pending and reviewed correction requests |
| `POST` | `/attendance/corrections/{id}/review` | `MANAGE_ACADEMIC_SETUP` | Approve or reject correction (updates marks & counters) |
| `GET` | `/attendance/reports/summary`| `VIEW_ATTENDANCE` | Institution-wide and class-wise attendance analytics |
| `GET` | `/attendance/reports/export-csv` | `EXPORT_REPORTS` | Stream CSV attendance ledger |
| `GET` | `/attendance/my-summary` | `VIEW_ATTENDANCE` | Tenant-scoped student personal or guardian ward summary |
| `GET` | `/attendance/teacher-classes`| `RECORD_ATTENDANCE` | Active classes assigned to the authenticated teacher |

---

## 6. Role-Based Authorization & Tenant-Isolation Matrix

| Operation | Student | Parent / Guardian | Teacher | Academic Admin | Institution Admin | Platform Operator |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Mark Attendance (`POST /sessions`)** | ❌ Denied | ❌ Denied | ✅ Assigned Classes Only | ✅ All Classes | ✅ All Classes | ❌ Denied |
| **View Roster (`GET /roster`)** | ❌ Denied | ❌ Denied | ✅ Assigned Classes Only | ✅ All Classes | ✅ All Classes | ❌ Denied |
| **View Personal Summary (`/my-summary`)** | ✅ Own Record | ✅ Verified Wards | ✅ Assigned Cohorts | ✅ Any Student | ✅ Any Student | ❌ Denied |
| **Request Correction (`POST /corrections`)**| ✅ Own Record | ✅ Verified Wards | ✅ Assigned Classes | ✅ Any Record | ✅ Any Record | ❌ Denied |
| **Review Correction (`/corrections/{id}/review`)**| ❌ Denied | ❌ Denied | ❌ Denied | ✅ Full Review | ✅ Full Review | ❌ Denied |
| **Configure Policy (`/policy`)** | ❌ Denied | ❌ Denied | ❌ Denied | ✅ Allowed | ✅ Allowed | ❌ Denied |
| **Institutional Reports (`/reports/summary`)** | ❌ Denied | ❌ Denied | ✅ Assigned Classes Only | ✅ Full Access | ✅ Full Access | ❌ Denied |
| **Export CSV (`/reports/export-csv`)** | ❌ Denied | ❌ Denied | ✅ Assigned Classes Only | ✅ Full Access | ✅ Full Access | ❌ Denied |

---

## 7. Implementation Roadmap (Phases 0.9.1 – 0.9.5)

### Phase 0.9.1: Database & Backend Core Repair
1. Patch `_is_teacher_assigned_to_target` to match `target_id` and remove the silent unassigned bypass.
2. Fix roster query case sensitivity (`ACTIVE`) and field naming (`academic_year`).
3. Replace hardcoded percentages with dynamic rate calculations.
4. Scope `get_my_attendance_summary` to `institution_id`.
5. Add intra-batch student ID duplicate validation to `AttendanceBatchSubmitIn`.
6. Enforce compound unique indexes in `ensure_indexes()`.
7. Expand `test_stage_0_9_attendance.py` with cross-tenant, unassigned teacher, duplicate batch, and correction audit tests.

### Phase 0.9.2: Teacher Attendance Interface Repair
1. Remove all synthetic data fallbacks in `AttendancePage.jsx` (lines 102-105, 126-154, 177-184, 191-202).
2. Remove fake success notifications from catch blocks.
3. Add robust error states and form input preservation.
4. Clean up `TeacherWorkspacePage.jsx` quick attendance submission.

### Phase 0.9.3: Student & Guardian Views
1. Verify student personal view renders authentic compliant percentages.
2. Verify parent portal view scopes strictly to verified linked wards with zero cross-tenant leakage.

### Phase 0.9.4: Administrative Reports & Corrections
1. Test class-wise, subject-wise, and date-wise aggregated analytics.
2. Verify CSV streaming export respects tenant and role boundaries.
3. Test end-to-end correction request approval and rejection with audit trail verification.

### Phase 0.9.5: Final Verification & Audit Report
1. Execute full backend pytest suite (target: 100% pass across all test modules).
2. Execute Ruff linting.
3. Execute frontend Vitest suite and production build.
4. Create `docs/audits/STAGE-0-9-VERIFICATION-REPORT.md`.

---

## 8. Conclusion & Sign-Off

The repository inspection for Stage 0.9 is complete. All architectural conflicts and security gaps have been cataloged with precise remediation steps. The codebase is now prepared to transition into Phase 0.9.1 (Database and Backend Implementation).

