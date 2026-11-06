# ChhatraLekha Security: Academic Data Access Control

- **Document:** `ACADEMIC-DATA-ACCESS-CONTROL.md`
- **Stage:** 0.8 (Academic Management Core)
- **Status:** Approved
- **Scope:** Role-Based Access Control (RBAC), Multi-Tenant Isolation, and Enrolment Integrity

---

## 1. Threat Model & Security Objectives

1. **Cross-Tenant Data Exposure**: An administrator or student from Institution A must never access, view, or modify academic years, classes, or student enrolments of Institution B.
2. **Unauthorized Curriculum Tampering**: Students, parents, or unauthorized staff must never be able to create, alter, or delete curriculum subjects, grade allocations, or academic schedules.
3. **Ghost Enrolments & Double Counting**: Students must not have multiple concurrent active enrolments in the same academic year within an institution.
4. **Destructive History Erasure**: Progression and transfer events must never delete past academic records. Past records must be preserved for compliance and verification.

---

## 2. RBAC Permissions Matrix

| Academic Resource / Operation | Student | Parent | Teacher / Faculty | School Admin | College Admin | University Admin | Platform Admin |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **View Academic Overview** | Read | Read | Read | Read | Read | Read | Read |
| **View Academic Years & Terms** | Read | Read | Read | Read | Read | Read | Read |
| **Manage Academic Years (Create/Activate/Archive)** | Deny | Deny | Deny | Manage | Manage | Manage | Manage |
| **View Departments & Programmes** | Read | Read | Read | Read | Read | Read | Read |
| **Manage Departments & Programmes** | Deny | Deny | Deny | Manage | Manage | Manage | Manage |
| **View Classes & Sections** | Read | Read | Read | Read | Read | Read | Read |
| **Create / Edit Classes & Sections** | Deny | Deny | Deny | Manage | Manage | Manage | Manage |
| **View Curriculum & Subjects** | Read | Read | Read | Read | Read | Read | Read |
| **Create / Modify Subjects** | Deny | Deny | Deny | Manage | Manage | Manage | Manage |
| **View Student Enrolments** | Own | Child | Cohort | All | All | All | All |
| **Enrol Student** | Deny | Deny | Deny | Manage | Manage | Manage | Manage |
| **Promote Student / Progression** | Deny | Deny | Deny | Manage | Manage | Manage | Manage |
| **Transfer Section** | Deny | Deny | Deny | Manage | Manage | Manage | Manage |
| **View Faculty Allocations** | Read | Read | Read | Read | Read | Read | Read |
| **Assign / Unassign Faculty** | Deny | Deny | Deny | Manage | Manage | Manage | Manage |
| **View Academic Calendar** | Read | Read | Read | Read | Read | Read | Read |
| **Create / Delete Calendar Events** | Deny | Deny | Deny | Manage | Manage | Manage | Manage |

---

## 3. Tenant Isolation Enforcement

All database queries across `academic.py` enforce institutional scoping:

```python
# Automatic scoping to caller's verified institution
institution_id = current_user.get("institution_id") or "INST-0421"

# Queries are strictly anchored to institution_id
query = {"institution_id": institution_id}
```

If an unauthenticated caller attempts to query or manipulate academic endpoints, the request is immediately rejected with `HTTP 401 Unauthorized`.

If an authenticated non-administrative user (such as a student or parent) attempts to execute a state-changing operation (`POST`, `PUT`, `DELETE`), the endpoint enforces:

```python
admin_roles = {"school_admin", "college_admin", "university_admin", "admin", "institution_admin"}
if current_user.get("role") not in admin_roles:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Academic configuration requires administrator privileges")
```

---

## 4. Student Promotion & Historical Audit Integrity

When a student is promoted:
1. The endpoint validates that the source enrolment exists and belongs to the caller's institution.
2. The current record is never deleted or overwritten. Its status is updated to `"promoted"` and `is_current` is set to `False`.
3. A new enrolment record is inserted with the target `academic_year_id` and `class_id`, linking the historical trail.
4. When a section is transferred, the `section_transfer_history` array records the old section, new section, timestamp, and audit justification.
