# ChhatraLekha Security: Attendance Access Control

- **Document:** `ATTENDANCE-ACCESS-CONTROL.md`
- **Stage:** 0.9 (Attendance Management System)
- **Status:** Approved
- **Scope:** Role-Based Access Control (RBAC), Teacher Scoping, and Guardian Verification

---

## 1. Threat Model & Security Invariants

1. **Student Invariant**: A student cannot access, inspect, or modify another student's attendance records. Frontend-supplied student IDs are never trusted as proof of authorization.
2. **Guardian Invariant**: A parent or guardian can only access attendance records for verified linked wards (`guardian_relationships` collection with `status == "VERIFIED"`). Unlinked or pending relationships are strictly rejected.
3. **Teacher Invariant**: A teacher can only record attendance for classes, cohort sections, or subjects assigned to them in `teacher_assignments` or where they are designated class teachers. Teachers cannot record attendance for unassigned classes.
4. **Institution Invariant**: Staff and administrators cannot access or manipulate attendance data outside their authorized institution boundary.
5. **Audit Invariant**: Attendance marks cannot be silently modified or deleted post-submission. All adjustments must undergo an auditable correction request approved by an authorized administrator, recording actor identities and timestamps.

---

## 2. RBAC Permissions Matrix

| Attendance Operation | Student | Parent / Guardian | Teacher / Faculty | School Admin | College Admin | University Admin |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **View My Summary (`/my-summary`)** | Own Only | Verified Wards | Assigned Cohorts | Institutional | Institutional | Multi-Institution |
| **View Class Roster (`/roster`)** | Deny | Deny | Assigned Classes | All Classes | All Classes | All Classes |
| **Record Attendance (`POST /sessions`)** | Deny | Deny | Assigned Classes | All Classes | All Classes | All Classes |
| **Request Correction (`POST /corrections`)** | Own Record | Ward Record | Assigned Classes | Any Record | Any Record | Any Record |
| **Review Correction (`/corrections/{id}/review`)**| Deny | Deny | Deny | Approve/Reject | Approve/Reject | Approve/Reject |
| **View Reports (`/reports/summary`)** | Deny | Deny | Assigned Classes | Full Access | Full Access | Full Access |
| **Export CSV (`/reports/export-csv`)** | Deny | Deny | Assigned Classes | Full Export | Full Export | Full Export |
| **Configure Policy (`/policy`)** | Deny | Deny | Deny | Full Config | Full Config | Full Config |

---

## 3. Backend Ownership Verification Implementation

### 3.1 Student Self-Access Enforcement
```python
if principal.role == "student":
    own_id = principal.apaar_id or (principal.user or {}).get("apaar_id") or principal.subject
    if student_id and student_id != own_id and student_id != principal.subject:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You may only access your own attendance record.",
        )
```

### 3.2 Parent Verified Ward Enforcement
```python
elif principal.role == "parent":
    ward_apaar = (principal.user or {}).get("ward_apaar_id") or (principal.user or {}).get("apaar_id")
    linked = ward_apaar and (resolved_id == ward_apaar)
    if not linked:
        rel = await db["guardian_relationships"].find_one({
            "parent_user_id": principal.subject,
            "student_id": resolved_id,
            "status": "VERIFIED",
        })
        if not rel:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You may only access attendance records for verified linked children.",
            )
```

### 3.3 Teacher Class Assignment Enforcement
```python
if principal.role == "teacher":
    assigned = await _is_teacher_assigned_to_target(
        db, principal, target_id=payload.target_id, inst_id=inst_id
    )
    if not assigned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You are not assigned to class or subject '{payload.target_label}'.",
        )
```

---

## 4. Privacy & Notification Sanitization

When an absence notification is published to the notification stream:
- The notification title is standardized (`"Daily Attendance Notice: Absence Logged"`).
- The message preview contains only cohort and session date metadata (`"Student was marked absent in Class 10A on 2026-03-10."`).
- Sensitive medical remarks or subjective teacher comments are excluded from push previews and email headers to safeguard student privacy.
