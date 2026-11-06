# Security Policy & Specification: Dashboard Access Control

**Module:** Role-Based Access Control & Tenant Data Isolation  
**Version:** 2.0.0  
**Status:** Enforced  
**Date:** 2026-11-06  

---

## 1. Threat Model & Security Objectives

In a multi-institutional, multi-role educational platform, dashboard interfaces are primary targets for unauthorized vertical privilege escalation and horizontal data leakage.

The dashboard access control architecture enforces five core security guarantees:

1. **Zero Client-Side Trust:**  
   Hiding navigation links or buttons in the frontend UI is strictly considered a usability aid, never an access control measure. Every HTTP transaction requires valid JWT authorization and evaluates authoritative server-side permissions.

2. **Strict Horizontal Tenant Isolation:**  
   Institution administrators (`school_admin`, `college_admin`) cannot read, modify, or list records belonging to another institution. Scoping is enforced via `principal.require_scope(institution_id)`.

3. **Guardian Relationship Integrity:**  
   Parents and guardians cannot access records of arbitrary students. Parental endpoints verify that an active row exists in `guardian_relationships` with status `GuardianVerificationStatus.VERIFIED`.

4. **University Administrator Boundary Enforcement:**  
   University and national oversight roles have access to aggregated statistics, quota utilisations, and compliance reports. They cannot inspect individual student personal identifiable records (PII) or unmasked APAAR IDs across unaffiliated institutions.

5. **Student Self-Record Scoping:**  
   Students can only access records where `student_id == principal.student_id`. Arbitrary fallback queries returning the first record in the database are strictly eliminated (enforced since Stage 0.3).

---

## 2. Server-Side Enforcement Mechanisms

### 2.1 Principal Validation & Identity Scoping

```python
# chhatralekha/app/api/me.py
@router.get("/dashboard")
async def get_my_dashboard(
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
    session: Session = Depends(get_db_session),
):
    student = session.exec(
        select(Student).where(Student.student_id == principal.student_id)
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found.")
    ...
```

### 2.2 Verified Guardian Boundary Verification

```python
# chhatralekha/app/api/parent.py
@router.get("/children/{student_id}/timetable")
def get_child_timetable(
    student_id: str,
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
    session: Session = Depends(get_db_session),
):
    relationship = session.exec(
        select(GuardianRelationship).where(
            GuardianRelationship.guardian_principal_id == principal.id,
            GuardianRelationship.student_id == student_id,
            GuardianRelationship.status == GuardianVerificationStatus.VERIFIED,
        )
    ).first()

    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view records for this student.",
        )
    ...
```

### 2.3 Institutional Tenant Isolation

```python
# chhatralekha/app/api/institutions.py
@router.get("/{institution_id}/dashboard-summary")
def get_institution_dashboard_summary(
    institution_id: str,
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
    session: Session = Depends(get_db_session),
):
    # Enforces that principal has authority for this specific institution
    principal.require_scope(institution_id)
    ...
```

---

## 3. Role-Based Permission Matrix

| Endpoint | Student | Parent | Teacher | School Admin | College Admin | Univ Admin |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `GET /me/dashboard` | Allow (Own) | Deny (403) | Deny (403) | Deny (403) | Deny (403) | Deny (403) |
| `GET /me/timetable` | Allow (Own) | Deny (403) | Deny (403) | Deny (403) | Deny (403) | Deny (403) |
| `GET /me/assignments` | Allow (Own) | Deny (403) | Deny (403) | Deny (403) | Deny (403) | Deny (403) |
| `GET /parent/children` | Deny (403) | Allow (Linked) | Deny (403) | Deny (403) | Deny (403) | Deny (403) |
| `GET /parent/children/{id}/timetable` | Deny (403) | Allow (Verified) | Deny (403) | Deny (403) | Deny (403) | Deny (403) |
| `GET /teacher/dashboard` | Deny (403) | Deny (403) | Allow (Own) | Deny (403) | Deny (403) | Deny (403) |
| `POST /teacher/assignments` | Deny (403) | Deny (403) | Allow (Assigned)| Deny (403) | Deny (403) | Deny (403) |
| `GET /{id}/dashboard-summary` | Deny (403) | Deny (403) | Deny (403) | Allow (Scoped) | Allow (Scoped) | Allow (Scoped) |
| `GET /dashboard/national` | Deny (403) | Deny (403) | Deny (403) | Deny (403) | Deny (403) | Allow (Aggregated) |

---

## 4. Verification Evidence & Security Invariants

1. **Regression Test 1 (Parent Cross-Student Access):**  
   Tested in `test_stage_0_6_dashboards.py::test_parent_child_timetable_verified_only`. Calling `GET /parent/children/{unlinked_student_id}/timetable` returns HTTP 403 Forbidden.

2. **Regression Test 2 (Tenant Cross-Institution Access):**  
   Tested in `test_stage_0_6_dashboards.py::test_institution_summary_cross_tenant_forbidden`. An administrator authenticating with token scoped to `INST-A` cannot query `GET /{INST-B}/dashboard-summary` (returns HTTP 403 Forbidden).

3. **Regression Test 3 (University Aggregated Boundary):**  
   University endpoints return aggregated capacity and compliance metrics without exposing raw student transcripts or PII.
