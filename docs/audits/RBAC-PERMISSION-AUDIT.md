# Role-Based Access Control (RBAC) and Permission Security Audit

**Project:** ChhatraLekha  
**Audit ID:** AUD-STG02-RBAC-01  
**Target Codebase:** `chhatralekha/app/core/rbac.py`, `app/api/deps.py`, `app/api/*.py`  
**Audit Date:** 2026-11-06  
**Auditor:** Antigravity (Advanced Agentic Coding)  
**Overall Status:** PASS WITH ISSUES (Comprehensive RBAC Model, Scoping Gaps in Enforcement)

---

## 1. Executive Summary

ChhatraLekha implements a well-structured Role-Based Access Control (RBAC) model defined in `app/core/rbac.py` and enforced via FastAPI dependencies in `app/api/deps.py`. The design explicitly caters to the multi-tiered Indian educational hierarchy, spanning national regulatory authorities down to individual students and parents.

The framework defines 13 roles and 28 granular permissions. Permission enforcement at the endpoint route level is consistently applied across core administrative routes. However, two primary structural risks exist:
1. **Decoupled Permission vs. Scope:** RBAC dependencies verify *action authorization* (e.g., `students:read`) but do not enforce *tenant boundary authorization* (e.g., `institution_id == principal.institution_id`). Scoping must be manually implemented by each route handler, creating vulnerabilities when query filters are omitted or malformed.
2. **Static JWT Permission Baking:** Permissions are computed at token generation and encoded into the JWT claims. Changes to a user's role in the database do not revoke or alter granted permissions until the token expires.

---

## 2. Role Definitions and Hierarchy

The platform defines 13 roles categorized into four governance tiers:

### 2.1 National and Regulatory Tier
- `national_admin`: Ministry of Education / national oversight; full system administration and nationwide analytics.
- `aicte_admin`: Regulatory authority oversight for technical universities and polytechnics.
- `platform_operator`: Cloud operations and platform maintenance; technical audit and settings access.
- `regulator_admin`: General education board or state council auditor.

### 2.2 Regional Governance Tier
- `state_admin`: State education directorate oversight; monitors all districts and institutions in a state.
- `district_admin`: District education officer (DEO); oversight of schools/colleges in a district.

### 2.3 Institutional Tier
- `institution_admin`: Principal, Registrar, or Head of Institution; manages users, students, staff, and institutional settings.
- `academic_admin`: Dean, Vice-Principal, or HOD; manages timetable, terms, subjects, and curriculum.
- `teacher`: Faculty / instructor; manages attendance, marks, and assessments for assigned classes.

### 2.4 End-User and Auxiliary Tier
- `student`: Learner; reads own academic record, attendance, results, and notifications.
- `parent`: Guardian; reads academic and attendance records for verified linked children.
- `verifier`: Third-party employer, admissions officer, or enforcement verifier (QR code and credential verification only).
- `pending`: Newly registered account awaiting verification or identity linkage; zero privileged permissions.

---

## 3. Permission Catalog (28 Permissions)

| Category | Permissions | Description |
|---|---|---|
| **Students** | `students:read`, `students:write`, `students:delete` | Query, create/edit, and soft-delete student records |
| **Attendance** | `attendance:read`, `attendance:write`, `attendance:export` | View daily records, submit attendance rosters, export reports |
| **Assessments** | `assessments:read`, `assessments:write`, `assessments:publish` | View scores, enter marks, publish exam results to students |
| **Institutions** | `institutions:read`, `institutions:write`, `institutions:delete` | View institution metadata, update profile, manage status |
| **Users** | `users:read`, `users:write`, `users:delete` | User management and account provisioning |
| **Transfers** | `transfers:read`, `transfers:write`, `transfers:approve` | Initiate student transfer certificates, review and approve transfers |
| **Reports** | `reports:generate`, `reports:export` | Execute analytical reports and download CSV/PDF exports |
| **Announcements** | `announcements:read`, `announcements:write` | Read circulars and post institutional notices |
| **Verification** | `verification:verify` | Perform APAAR ID and QR code integrity checks |
| **System** | `system:settings`, `system:audit` | Manage platform configurations and inspect security audit logs |
| **Directorate** | `directorate:analytics`, `directorate:interventions` | High-level dropout prediction, macro trends, and state interventions |
| **Consent** | `consent:read`, `consent:revoke` | Manage student/guardian data sharing consent and DigiLocker access |

---

## 4. Role-to-Permission Mapping Matrix

| Role | Student Perms | Attendance Perms | Assessment Perms | Institution Perms | User Perms | Transfer Perms | Reports Perms | Announcements | System / Dir | Verif / Consent |
|---|---|---|---|---|---|---|---|---|---|---|
| `national_admin` | R, W, D | R, W, E | R, W, P | R, W, D | R, W, D | R, W, A | G, E | R, W | Settings, Audit, Dir-All | Verif, Consent-All |
| `aicte_admin` | R | R, E | R | R, W | R | R | G, E | R | Audit, Dir-All | Verif |
| `platform_operator`| R | R | R | R | R | R | G | R | Settings, Audit | Verif |
| `state_admin` | R | R, E | R | R, W | R, W | R, A | G, E | R, W | Audit, Dir-All | Verif |
| `district_admin` | R | R, E | R | R | R | R, A | G, E | R, W | Dir-Analytics | Verif |
| `regulator_admin` | R | R | R | R | - | R | G | R | Audit, Dir-Analytics | Verif |
| `institution_admin`| R, W, D | R, W, E | R, W, P | R, W | R, W, D | R, W, A | G, E | R, W | Audit | Verif, Consent-Read |
| `academic_admin` | R, W | R, W, E | R, W, P | R | R | R, W | G, E | R, W | - | - |
| `teacher` | R | R, W | R, W | R | - | - | G | R, W | - | - |
| `student` | R (self) | R (self) | R (self) | R (enrolled) | - | R (self) | - | R | - | Consent-All |
| `parent` | R (linked) | R (linked) | R (linked) | R (enrolled) | - | - | - | R | - | Consent-All |
| `verifier` | - | - | - | - | - | - | - | - | - | Verif |
| `pending` | - | - | - | - | - | - | - | - | - | - |

*Legend: R = Read, W = Write, D = Delete, E = Export, P = Publish, A = Approve, G = Generate.*

---

## 5. Enforcement Architecture and Dependency Audit

### 5.1 Enforcement Primitives (`app/api/deps.py`)

1. **`require_permission(permission: str)`**:
   ```python
   def require_permission(required_permission: str):
       def dependency(principal: Principal = Depends(get_current_principal)) -> Principal:
           if required_permission not in principal.permissions:
               raise HTTPException(
                   status_code=status.HTTP_403_FORBIDDEN,
                   detail=f"Permission denied: {required_permission} required",
               )
           return principal
       return dependency
   ```
2. **`require_any_permission(permissions: list[str])`**:
   Verifies that the principal's permission set intersects with the required list.

### 5.2 Identified Structural Risks and Gaps

1. **Missing Scope Parameterization:**
   `require_permission("students:read")` passes as long as the user possesses that permission, regardless of which institution or student record is being queried. If a route handler simply performs `db["students"].find(query)` without enforcing `query["institution_id"] = principal.institution_id`, any teacher or institution admin can view or manipulate records belonging to competing institutions.
2. **Stale Permission Window:**
   Because `principal.permissions` is serialized into the JWT token during login (`app/core/security.py:84`), revoking an administrative role in MongoDB has no immediate effect on existing tokens. An attacker with a compromised token retains full permissions until the token expires (default: 24 hours).

---

## 6. Recommendations

1. **Implement Scoped Permission Guards:** Create enhanced dependencies such as `require_institution_permission(perm, institution_id_getter)` that validate both the permission and the target tenant boundary in a single atomic check.
2. **Centralize Dynamic Permission Verification:** For critical operations (e.g., `users:delete`, `institutions:delete`), query MongoDB to verify that the principal's active roles match the token claims before executing destructive actions.
3. **Automate RBAC Unit Tests:** Add test suites verifying that users with restricted roles (e.g., `teacher`, `student`, `parent`) receive HTTP 403 Forbidden on administrative endpoints (`/api/students/delete`, `/api/institutions`, `/api/reports/export`).

