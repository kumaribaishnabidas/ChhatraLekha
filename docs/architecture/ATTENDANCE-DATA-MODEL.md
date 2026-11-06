# ChhatraLekha Architecture: Attendance Data Model

- **Document:** `ATTENDANCE-DATA-MODEL.md`
- **Stage:** 0.9 (Attendance Management System)
- **Status:** Approved
- **Scope:** MongoDB Schema Specifications, Field Definitions, and Audit Relationships

---

## 1. Overview

The ChhatraLekha attendance data model uses MongoDB collections structured to support both daily school attendance and period-wise university lecture tracking, with immutable audit trails for every adjustment.

---

## 2. Collections & Schema Specifications

### 2.1 Collection: `attendance_policies`
Defines institution-wide attendance tracking rules, modes, and statutory thresholds.

```json
{
  "_id": "POL-INST-0421",
  "institution_id": "INST-0421",
  "mode": "DAILY",
  "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
  "periods_per_day": 7,
  "minimum_attendance_percentage": 75.0,
  "late_arrival_threshold_minutes": 15,
  "early_departure_threshold_minutes": 15,
  "consecutive_absent_alert_threshold": 3,
  "allowed_statuses": ["PRESENT", "ABSENT", "LATE", "EXCUSED", "ON_LEAVE", "HALF_DAY"],
  "updated_by": "USR-ADMIN-01",
  "updated_at": "2026-11-06T10:00:00Z"
}
```

- **Indices**:
  - `{"institution_id": 1}` (Unique)

---

### 2.2 Collection: `attendance_sessions`
Represents an attendance session submitted for a cohort class or course subject on a specific date and period.

```json
{
  "_id": "ATT-98a72c10b4",
  "session_id": "ATT-98a72c10b4",
  "institution_id": "INST-0421",
  "session_date": "2026-03-10",
  "mode": "DAILY",
  "period_number": null,
  "target_type": "CLASS",
  "target_id": "CLS-10A",
  "target_label": "Class 10 Section A",
  "subject_id": "SUB-MATH",
  "subject_name": "Mathematics",
  "academic_year_id": "AY-2025-26",
  "recorded_by": "TEA-001",
  "total_students": 40,
  "present_count": 36,
  "absent_count": 2,
  "late_count": 1,
  "excused_count": 1,
  "created_at": "2026-03-10T09:15:00Z"
}
```

- **Indices**:
  - `{"institution_id": 1, "target_id": 1, "session_date": 1, "period_number": 1, "subject_id": 1}` (Unique)
  - `{"institution_id": 1, "session_date": -1}`

---

### 2.3 Collection: `attendance_records`
Individual student attendance marks linked to an attendance session, preserving an immutable audit trail.

```json
{
  "_id": "ObjectId('...')",
  "session_id": "ATT-98a72c10b4",
  "institution_id": "INST-0421",
  "session_date": "2026-03-10",
  "student_id": "STU-001",
  "student_name": "Aarav Patel",
  "status": "EXCUSED",
  "remarks": "Medical leave confirmed",
  "target_id": "CLS-10A",
  "target_label": "Class 10 Section A",
  "subject_id": "SUB-MATH",
  "subject_name": "Mathematics",
  "recorded_by": "TEA-001",
  "audit_trail": [
    {
      "previous_status": "ABSENT",
      "new_status": "EXCUSED",
      "changed_by": "USR-ADMIN-01",
      "changed_by_name": "Principal Meera Nair",
      "reason": "Submitted verified dental clinic appointment certificate.",
      "review_notes": "Approved by administration.",
      "timestamp": "2026-03-11T14:20:00Z"
    }
  ],
  "created_at": "2026-03-10T09:15:00Z"
}
```

- **Indices**:
  - `{"session_id": 1, "student_id": 1}` (Unique)
  - `{"institution_id": 1, "student_id": 1, "session_date": -1}`
  - `{"institution_id": 1, "target_id": 1, "session_date": -1}`

---

### 2.4 Collection: `attendance_corrections`
Formal correction requests submitted by teachers, students, or staff for administrative review.

```json
{
  "_id": "CORR-7f8e9a1b2c",
  "id": "CORR-7f8e9a1b2c",
  "institution_id": "INST-0421",
  "session_id": "ATT-98a72c10b4",
  "student_id": "STU-001",
  "student_name": "Aarav Patel",
  "target_id": "CLS-10A",
  "session_date": "2026-03-10",
  "previous_status": "ABSENT",
  "requested_status": "EXCUSED",
  "reason": "Submitted verified dental clinic appointment certificate.",
  "supporting_document_url": null,
  "requested_by": "TEA-001",
  "requested_by_name": "Prof. Rajesh Kumar",
  "requested_at": "2026-03-11T11:00:00Z",
  "status": "APPROVED",
  "reviewed_by": "USR-ADMIN-01",
  "reviewed_at": "2026-03-11T14:20:00Z",
  "review_notes": "Approved by administration."
}
```

- **Indices**:
  - `{"institution_id": 1, "status": 1, "requested_at": -1}`
  - `{"session_id": 1, "student_id": 1}`

