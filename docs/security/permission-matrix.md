# ChhatraLekha — Role & Permission Matrix

**Document Version:** 1.0.0  
**Status:** Approved Target Architecture (Stage 0 Deliverable)

---

## 1. Role Catalog

ChhatraLekha defines 7 core institutional and platform roles:

1. `platform_super_admin`: Central platform maintainer (infrastructure health, institution onboarding, zero access to private student records).
2. `university_admin`: University rector / registrar / directorate (department structures, degree approval, aggregate institution compliance).
3. `institution_admin`: School or College Principal / Dean (course quotas, marksheet verification, faculty assignments, calendar).
4. `teacher`: Faculty / instructor (assigned class attendance, assignment creation, student grading).
5. `student`: Enrolled learner (personal timetable, attendance, wallet, submissions, portfolio).
6. `parent`: Verified guardian (ward attendance rates, published marksheets, institutional circulars).
7. `support_staff`: Lab assistants, administrative staff, librarians, and credential verifiers.

---

## 2. Comprehensive Permission Matrix

| Permission Key | Platform Admin | University Admin | Institution Admin | Teacher / Faculty | Student | Parent / Guardian | Support Staff |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`institution:onboard`** | Yes | No | No | No | No | No | No |
| **`institution:read`** | Yes | Yes | Yes | Yes | No | No | Yes |
| **`institution:write`** | No | Yes | Yes | No | No | No | No |
| **`academics:manage`** | No | Yes | Yes | No | No | No | No |
| **`students:enrol`** | No | Yes | Yes | No | No | No | No |
| **`students:read`** | No | Aggregate | Yes | Assigned Class | No | No | Assigned Desk |
| **`attendance:record`** | No | No | Override | Assigned Period | No | No | No |
| **`attendance:view_own`** | No | No | No | No | Yes | Ward Only | No |
| **`attendance:correct`** | No | No | Yes | With Audit | No | No | No |
| **`assignments:create`** | No | No | No | Assigned Class | No | No | No |
| **`assignments:submit`** | No | No | No | No | Yes | No | No |
| **`marks:enter`** | No | No | No | Assigned Class | No | No | No |
| **`marks:moderate`** | No | Yes | Yes | No | No | No | No |
| **`results:publish`** | No | Yes | Yes | No | No | No | No |
| **`results:view_own`** | No | No | No | No | Yes | Ward Only | No |
| **`opportunities:post`**| No | Yes | Yes | No | No | No | No |
| **`opportunities:apply`**| No | No | No | No | Yes | No | No |
| **`library:manage`** | No | No | Yes | No | No | No | Yes (Librarian) |
| **`facilities:book`** | No | Yes | Yes | Yes | No | No | Yes |
| **`tickets:create`** | No | No | No | Yes | Yes | Yes | Yes |
| **`tickets:manage`** | No | Yes | Yes | No | No | No | Designated |
| **`credential:verify`** | No | No | No | No | No | No | Yes (Verifier) |
| **`audit:read`** | Yes (System) | Yes (University)| Yes (Tenant) | No | No | No | No |
| **`ai:query`** | Yes | Yes | Yes | Yes | Yes | Yes | Yes |

---

## 3. Enforcement Pattern in Backend Dependencies

```python
def require_permission(permission: str):
    async def dependency(
        tenant: TenantContext = Depends(get_tenant_context),
    ) -> TenantContext:
        if permission not in tenant.permissions:
            raise HTTPException(
                status_code=403,
                detail=f"User lacks required permission '{permission}' for institution '{tenant.institution_id}'.",
            )
        return tenant
    return dependency
```
