# ChhatraLekha — Module Boundaries & Domain Architecture

**Document Version:** 1.0.0  
**Status:** Approved Target Architecture (Stage 0 Deliverable)

---

## 1. Domain Boundary Rules

To ensure modularity and prevent spaghetti dependencies, all business logic is organized into bounded contexts.

1. **No Direct Inter-Module Database Access:**
   Module A must never directly query or mutate collections/tables owned by Module B. Cross-module data retrieval must occur via documented service methods or domain events.
2. **Repository Decoupling:**
   Each module defines its repository interface independently of persistence mechanics (Motor MongoDB or PostgreSQL).
3. **Domain Event Broadcasting:**
   Lifecycle changes (e.g., `ENROLMENT_CREATED`, `ATTENDANCE_RECORDED`, `RESULT_PUBLISHED`) emit structured domain events consumed by notifications, audit logging, and reporting.

---

## 2. Comprehensive 19-Module Functional Specification

### 1. Identity Module (`app/modules/identity/`)
- **Owns:** `User`, `InstitutionMembership`, `Session`, `APIKey`.
- **Responsibilities:** Central identity management, credentials, multi-institution membership linkages, session management, and authentication token issuance.
- **Boundaries:** Does not store academic enrolments or class details.

### 2. Institutions Module (`app/modules/institutions/`)
- **Owns:** `Institution`, `InstitutionSettings`, `Department`.
- **Responsibilities:** Institutional metadata, grading scale policies, institutional category (School, College, University), department configurations.
- **Boundaries:** Isolated from student-specific records.

### 3. Students Module (`app/modules/students/`)
- **Owns:** `StudentProfile`, `AcademicHistory`.
- **Responsibilities:** Core student demographic data, date of birth, APAAR ID masking, category, and historical institutional records.
- **Boundaries:** Independent of login accounts; links to central `User` identity via verified claim codes.

### 4. Parents & Guardians Module (`app/modules/guardians/`)
- **Owns:** `GuardianRelationship`.
- **Responsibilities:** Formal linkage between a parent user and an enrolled student, relationship verification workflow, and authorized ward access control.
- **Boundaries:** Cannot access another student's data or administrative records.

### 5. Teachers & Staff Module (`app/modules/staff/`)
- **Owns:** `StaffProfile`, `TeacherAssignment`.
- **Responsibilities:** Faculty profiles, departmental appointments, class/subject assignments, and teacher permissions.
- **Boundaries:** Teachers can only access classes and subjects explicitly assigned to them.

### 6. Academics Module (`app/modules/academics/`)
- **Owns:** `AcademicYear`, `Programme`, `Course`, `ClassGroup`, `Section`, `Subject`.
- **Responsibilities:** Academic calendar, course syllabus definitions, intake capacities, senior secondary streams, and prerequisite structures.
- **Boundaries:** Reusable across schools, colleges, and universities.

### 7. Attendance Module (`app/modules/attendance/`)
- **Owns:** `AttendanceSession`, `AttendanceRecord`.
- **Responsibilities:** Classroom attendance taking, period locking, cumulative percentage computation, holiday overrides, and change-impact audit tracking.
- **Boundaries:** Never overwrites locked history without formal audit reason.

### 8. Timetable Module (`app/modules/timetable/`)
- **Owns:** `TimetableSlot`, `RoomAllocation`.
- **Responsibilities:** Daily scheduled periods, room and faculty allocations, voice-assisted timetable queries.
- **Boundaries:** Coordinates with teacher assignments and campus facilities.

### 9. Learning Management (LMS) Module (`app/modules/learning/`)
- **Owns:** `LearningMaterial`, `SyllabusTopic`, `QuizSession`.
- **Responsibilities:** Faculty notes, PDF resources, video lecture links, subject-wise organization, student self-quizzes.
- **Boundaries:** Material access is restricted to students enrolled in that specific subject/class.

### 10. Assignments Module (`app/modules/assignments/`)
- **Owns:** `Assignment`, `Submission`.
- **Responsibilities:** Assignment prompts, rubrics, due dates, student file submissions, teacher evaluation, marks, and feedback.
- **Boundaries:** Submissions are private to the submitting student and the assigned grading teacher.

### 11. Examinations & Results Module (`app/modules/examinations/`)
- **Owns:** `Assessment`, `AssessmentMarks`, `ResultPublication`, `TranscriptRecord`.
- **Responsibilities:** Exam scheduling, internal assessment scoring, grade moderation committee review, result publication, and transcripts.
- **Boundaries:** Final results cannot be published automatically by AI; requires authorized staff approval.

### 12. Admissions Module (`app/modules/admissions/`)
- **Owns:** `AdmissionApplication`, `MeritList`, `ApplicationDocument`.
- **Responsibilities:** Configurable admission forms, document checklists, application status tracking, and conversion to active enrolment.
- **Boundaries:** Pre-enrolment data is kept separate from active student registers.

### 13. Communication Module (`app/modules/communication/`)
- **Owns:** `Announcement`, `Notification`, `NotificationPreference`.
- **Responsibilities:** Institutional announcements, targeted class broadcasts, urgent parent alerts, and user notification delivery preferences.
- **Boundaries:** Does not support unrestricted unmoderated peer-to-peer social messaging.

### 14. Documents Module (`app/modules/documents/`)
- **Owns:** `DocumentVault`, `Certificate`, `VerificationToken`.
- **Responsibilities:** Tamper-evident verifiable credentials, degree certificates, transfer certificates, and opaque QR token verification.
- **Boundaries:** Verification links reveal only minimum necessary validation fields; zero raw PII.

### 15. Digital Library Module (`app/modules/library/`)
- **Owns:** `LibraryBook`, `BookCopy`, `BookLoan`.
- **Responsibilities:** OPAC catalog search (Title, Author, ISBN, Subject), copy availability tracking, loan issuing, due date reminders.
- **Boundaries:** Isolated from non-library academic workflows.

### 16. Finance Module (`app/modules/finance/`)
- **Owns:** `FeeStructure`, `StudentInvoice`, `PaymentReceipt`.
- **Responsibilities:** Institutional fee structure definitions, concessions, invoice generation, payment status tracking.
- **Boundaries:** Financial ledgers are append-only; receipts are cryptographically sealed.

### 17. Career & Opportunities Module (`app/modules/opportunities/`)
- **Owns:** `Opportunity`, `Scholarship`, `Internship`, `StudentPortfolio`.
- **Responsibilities:** Central scholarship directory, campus placement drives, student skill profiles, and verifiable resume export.
- **Boundaries:** Opportunities clearly distinguish institution-verified listings from external resources.

### 18. Campus Services Module (`app/modules/campus/`)
- **Owns:** `CampusFacility`, `FacilityBooking`, `MaintenanceRequest`.
- **Responsibilities:** Classroom, laboratory, and auditorium reservations; facility maintenance ticketing and status tracking.
- **Boundaries:** Bookings check for timetable conflicts before confirmation.

### 19. AI Assistant & Multilingual Voice Module (`app/modules/ai/`)
- **Owns:** `KnowledgeChunk`, `ConversationThread`, `VoiceIntent`.
- **Responsibilities:** Role-aware grounded RAG retrieval, speech-to-text voice commands, text-to-speech audio playback across all 22 Eighth Schedule languages.
- **Boundaries:** Strictly enforces signed-in user permissions; cannot bypass database security guards.
