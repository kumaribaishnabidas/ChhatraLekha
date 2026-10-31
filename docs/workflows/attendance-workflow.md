# ChhatraLekha — Attendance Workflow & Verification

**Document Version:** 1.0.0  
**Status:** Approved Target Architecture (Stage 0 Deliverable)

---

## 1. Daily Classroom Attendance Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Teacher as Faculty / Teacher
    participant App as Teacher Workspace UI
    participant Backend as Attendance Service
    participant Repo as Attendance Store
    participant Audit as Hash-Chained Audit Trail
    participant Parent as Parent Notification Channel
    
    Teacher->>App: Opens Active Timetable Period
    App->>Backend: GET /api/v1/attendance/session/current?class_id=C1&subject_id=S1
    Backend->>Backend: Verify TeacherAssignment for Class & Subject
    Backend-->>App: Active Student Roster (Roll, Name, Photo, Recent Attendance %)
    
    Teacher->>App: Marks Status (Default: All Present; Toggles Absences & Tardy)
    Teacher->>App: Clicks "Submit & Lock Attendance Session"
    App->>Backend: POST /api/v1/attendance/session/submit { roster_records, period, date }
    Backend->>Repo: Create AttendanceSession & AttendanceRecords
    Backend->>Backend: Recompute Cumulative Attendance Percentage
    Backend->>Audit: Append Signed Event (ATTENDANCE_RECORDED, session_id, teacher_id)
    Backend-->>App: 200 OK (Session Sealed with Timestamp)
    
    opt Automated Guardian Alert
        Backend->>Parent: Dispatch Notice (if ward is marked Absent)
    end
```

---

## 2. Attendance Correction & Audit Policy

1. **No Silent Overwrites:**
   - Once an attendance session is submitted and locked, existing records cannot be edited in place.
   - Any correction requires an explicit correction request with an explanation/reason (e.g. "Medical Certificate Approved", "Late transport verified").
2. **Double-Entry Correction Event:**
   - The correction stores a `PREVIOUS_STATUS` and `NEW_STATUS`, the timestamp of alteration, and the ID of the authorizing staff member.
   - A cryptographic audit event (`ATTENDANCE_CORRECTED`) is immediately logged.
3. **Threshold Alerts:**
   - When a student's cumulative attendance drops below the institution threshold (typically 75%), automated warning notifications are flagged on both the student's personal dashboard and the verified parent portal.

