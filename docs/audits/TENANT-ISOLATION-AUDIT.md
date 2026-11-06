# Multi-Tenancy and Data Isolation Security Audit

**Project:** ChhatraLekha  
**Audit ID:** AUD-STG02-TENANT-01  
**Target Codebase:** `chhatralekha/app/api/*.py`, `chhatralekha/app/modules/*.py`  
**Audit Date:** 2026-11-06  
**Auditor:** Antigravity (Advanced Agentic Coding)  
**Overall Status:** FAIL (Critical Cross-Tenant and Student PII Leakage Identified)

---

## 1. Executive Summary

ChhatraLekha utilizes a single shared MongoDB database with logical tenant partitioning based on an `institution_id` discriminator field across collections (`students`, `attendance`, `assessments`, `academic_terms`, `academic_subjects`, `academic_sections`, `announcements`, `reports`, `transfers`).

This audit identified severe data isolation vulnerabilities that breach tenant boundaries and leak private student Personally Identifiable Information (PII):
1. **Unscoped Fallback Queries (SEC-ISO-01, SEC-ISO-02):** In both `profile.py` and `me.py`, fallback routines intended for demo environments execute unconditioned queries (`db["students"].find_one()` and `db["students"].find().limit(1)`) whenever an exact identifier match fails. This inadvertently exposes arbitrary student and guardian records to unrelated users in all environments.
2. **Insecure Direct Object References (SEC-ATT-01, SEC-ASM-01):** Endpoints intended for student self-service (`/api/attendance/my-summary` and `/api/assessments/my-results`) allow arbitrary `student_id` query parameters without verifying that the caller owns the record or has legitimate parental guardianship.
3. **Fail-Open Query Filtering (SEC-TENANT-01):** Multi-tenant query builders omit `institution_id` constraints when `principal.institution_id` is null or empty, falling open to match the entire database rather than failing closed.

---

## 2. Findings Summary Table

| ID | Severity | File and Line | Title | Impact |
|---|---|---|---|---|
| **SEC-ISO-01** | **Critical** | `app/api/profile.py:124` | Unscoped Student Fallback in Profile Retrieval | Arbitrary student PII and guardian contacts exposed to non-student accounts |
| **SEC-ISO-02** | **Critical** | `app/api/me.py:94` | Unscoped Single-Document Student Fallback in `_resolve_student_record` | Unmatched student logins arbitrarily assume the identity of the first student in DB |
| **SEC-ATT-01** | **High** | `app/api/attendance.py:153–165` | IDOR on Attendance Summary Endpoint (`my-summary`) | Any student can exfiltrate complete daily attendance logs of any peer |
| **SEC-ASM-01** | **High** | `app/api/assessments.py:272–282` | IDOR on Assessment Results Endpoint (`my-results`) | Any student can exfiltrate examination marks and teacher remarks of any peer |
| **SEC-TENANT-01** | **Medium** | `app/api/academic.py:98`, `announcements.py:96`, `reports.py:32` | Fail-Open Query Filtering on Missing `institution_id` | Unscoped queries return records across all institutions when tenant ID is null |

---

## 3. Detailed Vulnerability Analysis

### 3.1 SEC-ISO-01: Unscoped Student Fallback in Profile Retrieval (Critical)

**Location:** `chhatralekha/app/api/profile.py:124`

```python
@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    principal: Principal = Depends(get_current_principal),
    db: Any = Depends(get_database),
) -> ProfileResponse:
    ...
    # Look up student record if applicable
    student = None
    if apaar_id:
        student = await db["students"].find_one({"apaar_id": apaar_id})
    if not student:
        # Fallback to first student record for demo profiles
        student = await db["students"].find_one()
```

**Flaws Identified:**
- If a user logged into the system does not have an `apaar_id` in their user profile (e.g., an administrator, staff member, teacher, or newly provisioned student), the backend executes `await db["students"].find_one()`.
- MongoDB executes this query with zero filters, returning the first document in natural storage order.
- The user's profile response (`ProfileResponse`) is populated with this arbitrary student's legal name, APAAR ID, date of birth, gender, guardian contact phone number, address, and enrolled institution!
- There is zero restriction to demo mode; this query executes in production.

**Remediation:**
Remove the fallback completely:
```python
if apaar_id:
    student = await db["students"].find_one({"apaar_id": apaar_id})
# Do not fall back to arbitrary student records
```

---

### 3.2 SEC-ISO-02: Unscoped Single-Document Student Fallback in `_resolve_student_record` (Critical)

**Location:** `chhatralekha/app/api/me.py:84–102`

```python
async def _resolve_student_record(principal: Principal, db: Any) -> dict[str, Any] | None:
    """Find the student document corresponding to the authenticated principal."""
    # Try username as APAAR ID or student ID
    doc = await db["students"].find_one({
        "$or": [
            {"apaar_id": principal.subject},
            {"student_id": principal.subject},
            {"user_id": principal.subject},
        ]
    })
    if doc:
        return doc

    # Fallback: return the first record for local testing / demo mode
    async for item in db["students"].find().limit(1):
        return item

    return None
```

**Flaws Identified:**
- `app/api/me.py` powers the primary student self-service endpoints:
  - `GET /api/me/student` (Student academic details)
  - `GET /api/me/attendance` (Student attendance history)
  - `GET /api/me/assessments` (Student examination grades)
- If the logged-in principal's `subject` is not matched in `students`, instead of returning HTTP 404 Not Found, it iterates `db["students"].find().limit(1)` and assigns that student record to the user.
- This creates arbitrary identity conflation and exposes academic history, guardian details, and attendance records to unrelated users.

**Remediation:**
Eliminate the fallback or strictly gate it:
```python
if settings.is_production:
    return None
# If in non-production, return None unless explicitly in DEMO_MODE
return None
```

---

### 3.3 SEC-ATT-01 & SEC-ASM-01: Insecure Direct Object References in Self-Service Endpoints (High)

**Location:**  
- `chhatralekha/app/api/attendance.py:153–165` (`/api/attendance/my-summary`)  
- `chhatralekha/app/api/assessments.py:272–282` (`/api/assessments/my-results`)

```python
@router.get("/my-summary", response_model=AttendanceSummaryResponse)
async def get_my_attendance_summary(
    student_id: Optional[str] = None,
    principal: Principal = Depends(get_current_principal),
    db: Any = Depends(get_database),
):
    target_id = student_id or principal.subject
    # Query database using target_id directly without ownership verification:
    records = await db["attendance"].find({"student_id": target_id}).to_list(...)
```

**Flaws Identified:**
1. Both endpoints allow the caller to supply an arbitrary `student_id` parameter.
2. The endpoint fails to verify:
   - Whether `principal.subject == student_id` (ownership).
   - Whether `principal.role == "parent"` and `student_id` is in `principal.linked_children` (authorized guardianship).
   - Whether `principal.role` is an authorized educator/administrator within the same `institution_id`.
3. Consequently, any authenticated student can enumerate student IDs or APAAR IDs to inspect the full attendance history and published test scores of any other student.

**Remediation:**
Verify authorization before accepting `student_id`:
```python
if student_id and student_id != principal.subject:
    # Allow only parents of that child or institutional staff
    if principal.role == "parent":
        parent_doc = await db["parents"].find_one({"user_id": principal.subject})
        if not parent_doc or student_id not in parent_doc.get("linked_students", []):
            raise HTTPException(status_code=403, detail="Not authorized to access this student")
    elif principal.role not in {"teacher", "academic_admin", "institution_admin", "national_admin"}:
        raise HTTPException(status_code=403, detail="Cannot access records of other students")
```

---

### 3.4 SEC-TENANT-01: Fail-Open Institution Query Filtering (Medium)

**Location:** `app/api/academic.py:98`, `announcements.py:96`, `reports.py:32`

In query builders across multiple routers:
```python
query: dict[str, Any] = {}
if principal.role not in DIRECTORATE_ROLES:
    if principal.institution_id:
        query["institution_id"] = principal.institution_id
```

**Flaws Identified:**
- If `principal.institution_id` is `None` or an empty string `""` (for instance, an unassigned user or a corrupted user record), the inner conditional is skipped.
- The `query` object remains `{}` (empty filter).
- MongoDB executes an unbounded query across all institutions, returning academic sections, announcements, or reports belonging to all tenants.

**Remediation:**
Adopt a **Fail-Closed** security posture:
```python
if principal.role not in DIRECTORATE_ROLES:
    if not principal.institution_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Principal is not associated with an institution",
        )
    query["institution_id"] = principal.institution_id
```

---

## 4. Architectural Recommendations

1. **Introduce a TenantContext Helper:** Create a standardized database query utility that automatically injects tenant constraints based on principal credentials.
2. **Eliminate Blind Fallback Queries:** Prohibit unconditioned queries (`find_one()` or `find().limit(1)`) across all routers. Fallback data must only be served from synthetic in-memory fixtures when `DEMO_MODE=True` and `ENVIRONMENT != "production"`.
3. **Automate Tenant Isolation Integration Tests:** Add automated regression tests verifying that:
   - Institution A users cannot view Institution B resources.
   - Student A cannot access Student B attendance or results via query manipulation.
   - Non-associated users receive HTTP 400/403 rather than full tenant listings.

