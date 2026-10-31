# ChhatraLekha — Role & Permission Matrix

**Document Version:** 1.0.0  
**Status:** Approved Target Architecture (Stage 0 Deliverable)

---

## 1. Role Catalog

ChhatraLekha defines 8 institution-scoped roles and 1 platform-level role:

1. `platform_super_admin`: Central platform maintainer (infrastructure health, institution onboarding, no direct private student record access).
2. `aicte_admin` / `national_directorate`: National oversight (cross-institution anomaly reviews, regulatory intake reporting).
3. `university_admin`: University rector / registrar (department structures, degree approval, university-wide statistics).
4. `college_admin`: College principal / dean (course quotas, marksheet verification, faculty assignments).
5. `school_admin`: School principal (K-12 classes, student admissions, school calendar).
6. `teacher`: Faculty / instructor (assigned class attendance, assignment creation, grading).
7. `student`: Enrolled learner (personal timetable, attendance, wallet, submissions).
8. `parent`: Verified guardian (ward attendance, marks, announcements).
9. `verifier`: External credential verifier (time-bound token validation only).

---

## 2. Permission Matrix by Functional Domain

| Permission Key | Platform Admin | National Directorate | University Admin | College Admin | School Admin | Teacher | Student | Parent | Verifier |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`institution:onboard`** | Yes | No | No | No | No | No | No | No | No |
| **`institution:read`** | Yes | Yes | Yes | Yes | Yes | Yes | No | No | No |
| **`academics:manage`** | No | No | Yes | Yes | Yes | No | No | No | No |
| **`students:enrol`** | No | No | Yes | Yes | Yes | No | No | No | No |
| **`students:read`** | No | Aggregate | Yes | Yes | Yes | Assigned | No | No | No |
| **`attendance:record`** | No | No | No | Override | Override | Assigned | No | No | No |
| **`attendance:view_own`** | No | No | No | No | No | No | Yes | Ward | No |
| **`assignments:create`** | No | No | No | No | No | Assigned | No | No | No |
| **`assignments:submit`** | No | No | No | No | No | No | Yes | No | No |
| **`marks:enter`** | No | No | No | No | No | Assigned | No | No | No |
| **`marks:moderate`** | No | No | Yes | Yes | Yes | No | No | No | No |
| **`results:publish`** | No | No | Yes | Yes | Yes | No | No | No | No |
| **`results:view_own`** | No | No | No | No | No | No | Yes | Ward | No |
| **`opportunities:post`**| No | No | Yes | Yes | Yes | No | No | No | No |
| **`opportunities:apply`**| No | No | No | No | No | No | Yes | No | No |
| **`tickets:create`** | No | No | No | No | No | Yes | Yes | Yes | No |
| **`tickets:manage`** | No | No | Yes | Yes | Yes | No | No | No | No |
| **`credential:verify`** | No | No | No | No | No | No | No | No | Yes |
| **`audit:read`** | Yes | National | Scoped | Scoped | Scoped | No | No | No | No |
| **`ai:query`** | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | No |

---

## 3. Enforcement in FastAPI Endpoints

Permissions are enforced via the `has_permission` dependency:

```python
@router.post("/attendance/session/submit")
async def record_attendance(
    payload: AttendanceSubmitRequest,
    tenant: TenantContext = Depends(require_permission("attendance:record")),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    # Endpoint execution guaranteed to be tenant-authorized
    ...
```
