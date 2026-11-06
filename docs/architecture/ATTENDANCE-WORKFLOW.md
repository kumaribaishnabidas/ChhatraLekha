# ChhatraLekha Architecture: Attendance Workflows

- **Document:** `ATTENDANCE-WORKFLOW.md`
- **Stage:** 0.9 (Attendance Management System)
- **Status:** Approved
- **Scope:** Teacher Roll Call, Duplicate Protection, Absence Notification, and Auditable Corrections

---

## 1. Teacher Attendance Roll Call Workflow

```mermaid
sequenceDiagram
    autonumber
    actor Teacher
    participant Frontend as Web/Mobile Client
    participant API as Attendance API (/sessions)
    participant Auth as RBAC / Security
    participant DB as MongoDB
    participant Notif as Notification Stream

    Teacher->>Frontend: Selects assigned Class, Date & Period
    Frontend->>API: GET /api/attendance/roster?class_id=CLS-10A
    API->>Auth: Verify caller is assigned to CLS-10A
    Auth-->>API: Authorized
    API->>DB: Query active student_enrolments
    DB-->>API: Student Roster
    API-->>Frontend: Returns Roster Items

    Teacher->>Frontend: Marks statuses (Present, Absent, Late, Excused)
    Teacher->>Frontend: Clicks Submit Attendance
    Frontend->>API: POST /api/attendance/sessions (batch records)
    API->>Auth: Verify caller institution and role
    API->>DB: Check for duplicate session on same date & target
    alt Duplicate Session Found
        DB-->>API: Existing Session Doc
        API-->>Frontend: HTTP 409 Conflict (Duplicate Submission)
    else No Duplicate
        API->>DB: Insert attendance_sessions record
        API->>DB: Insert attendance_records (with audit_trail: [])
        API->>Notif: Dispatch Absence Notifications for ABSENT students
        API->>Notif: Dispatch Submission Confirmation to Teacher
        API->>DB: Write Audit Event
        API-->>Frontend: HTTP 200 OK (AttendanceSessionOut)
        Frontend-->>Teacher: Displays Confirmation & Notification Status
    end
```

---

## 2. Attendance Correction & Audit Workflow

```mermaid
sequenceDiagram
    autonumber
    actor Requester as Teacher / Student
    actor Admin as Institution Administrator
    participant API as Attendance API
    participant DB as MongoDB
    participant Notif as Notification Stream

    Requester->>API: POST /api/attendance/corrections (session_id, student_id, requested_status, reason)
    API->>DB: Verify original attendance record exists in caller's institution
    API->>DB: Insert attendance_corrections (status="PENDING")
    API-->>Requester: Correction Request Logged (status="PENDING")

    Admin->>API: GET /api/attendance/corrections?status=PENDING
    API-->>Admin: Returns Pending Correction Requests

    alt Admin Approves Correction
        Admin->>API: POST /api/attendance/corrections/{id}/review (decision="APPROVE", review_notes)
        API->>DB: Update attendance_records.status = requested_status
        API->>DB: Push audit entry to attendance_records.audit_trail
        API->>DB: Recalculate attendance_sessions counters
        API->>DB: Update correction doc status = "APPROVED"
        API->>Notif: Send approval notification to Student & Teacher
        API-->>Admin: HTTP 200 OK (Status: APPROVED)
    else Admin Rejects Correction
        Admin->>API: POST /api/attendance/corrections/{id}/review (decision="REJECT", review_notes)
        API->>DB: Update correction doc status = "REJECTED"
        API->>Notif: Send rejection notification to Requester
        API-->>Admin: HTTP 200 OK (Status: REJECTED)
    end
```

---

## 3. Statutory Attendance Compliance Monitoring

1. **Threshold Rule**: Aligned with the National Education Policy (NEP 2020) and State Education Boards across India, students must maintain a minimum cumulative attendance of **75.0%** to qualify for semester examinations and internal assessments.
2. **Real-Time Evaluation**:
   $$\text{Attendance Rate} = \frac{\text{Present Sessions} + \text{Late Sessions}}{\text{Total Sessions}} \times 100$$
3. **Defaulter Escalation**:
   - Students whose cumulative rate falls below 75.0% receive proactive status warnings.
   - Administrators can review the "Statutory Defaulters" roster in the Attendance Overview tab.
   - Absence triggers consecutive alerts if a student is absent for 3 consecutive working days.

