# ChhatraLekha — Student Enrolment Workflow

**Document Version:** 1.0.0  
**Status:** Approved Target Architecture (Stage 0 Deliverable)

---

## 1. End-to-End Enrolment Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Institution Administrator
    participant Sys as ChhatraLekha Core
    participant Anomaly as Regulatory Anomaly Engine
    participant Repo as Student & Enrolment Store
    participant Audit as Hash-Chained Audit Trail
    actor Student as Student / Parent
    
    Admin->>Sys: POST /api/v1/enrolments (Roster / CSV Import)
    Sys->>Sys: Validate Required Fields (Name, DOB, Gender, Programme, Quota)
    Sys->>Anomaly: Check Sanctioned Intake & Supernumerary Quota Ceilings
    
    alt Quota Exceeded
        Anomaly-->>Sys: Flag Breach (EXCESS_APPROVED_INTAKE or QUOTA_BREACH)
        Sys-->>Admin: 422 Unprocessable (Requires Regulatory Override or Rejection)
    else Caps Respected
        Sys->>Sys: Generate Masked APAAR ID & SHA-256 HMAC Token
        Sys->>Repo: Create StudentProfile & StudentEnrolment (Status: ACTIVE)
        Sys->>Audit: Append Signed Event (ENROLMENT_CREATED, actor=Admin)
        Sys->>Sys: Generate Single-Use Claim/Activation Code
        Sys-->>Admin: Enrolment Completed (Claim Codes Generated)
        Admin-->>Student: Deliver Onboarding Notification with Claim Code
        Student->>Sys: POST /api/v1/identity/claim (Claim Code, Account Auth)
        Sys->>Sys: Bind StudentProfile to User Identity
        Sys->>Audit: Append Signed Event (STUDENT_CLAIMED_PROFILE)
        Sys-->>Student: Membership Activated. Direct to Student Hub (/me)
    end
```

---

## 2. Business Rules & Safeguards

1. **Intake Cap Compliance:**
   - Every programme specifies `approved_intake` and supernumerary caps (NRI 5%, OCI/FN 15%, TFW 5%, PMSSS cap).
   - Enrolments beyond the approved capacity are halted unless explicitly granted an authorized regulatory waiver.
2. **Duplicate APAAR Protection:**
   - When a student enrolment is submitted, the backend computes `match_token(apaar_id)`.
   - If the same match token exists in another active higher education institution for the same academic year, a `DUPLICATE_CROSS_COLLEGE` anomaly is automatically flagged.
3. **Roll Number Uniqueness:**
   - Roll numbers must be strictly unique within the composite tuple `(institution_id, programme_id, academic_year)`.

