# ChhatraLekha Architecture: Academic Data Model

- **Document:** `ACADEMIC-DATA-MODEL.md`
- **Stage:** 0.8 (Academic Management Core)
- **Status:** Approved
- **Scope:** MongoDB Schema Specifications, Field Definitions, and Validation Rules

---

## 1. Overview

The ChhatraLekha academic data layer is hosted within the primary MongoDB database. It uses distinct collections designed for flexibility across school and university structures while strictly adhering to tenant scoping.

---

## 2. Collections & Schema Specifications

### 2.1 Collection: `academic_years`
Represents an institutional academic cycle (e.g., 2025-26).

```json
{
  "_id": "AY-2025-26",
  "institution_id": "INST-0421",
  "year_label": "2025-26",
  "start_date": "2025-06-01",
  "end_date": "2026-05-31",
  "admission_start": "2025-04-01",
  "admission_end": "2025-06-15",
  "is_current": true,
  "is_archived": false,
  "created_at": "2025-03-01T00:00:00Z"
}
```

- **Indices**:
  - `{"institution_id": 1, "year_label": 1}` (Unique)
  - `{"institution_id": 1, "is_current": 1}`

---

### 2.2 Collection: `semester_terms`
Represents teaching intervals (semesters, trimesters, quarters, annual terms) within an academic year.

```json
{
  "_id": "TERM-2025-S1",
  "institution_id": "INST-0421",
  "academic_year_id": "AY-2025-26",
  "term_name": "Semester 1 (Autumn)",
  "term_type": "semester",
  "term_number": 1,
  "start_date": "2025-07-01",
  "end_date": "2025-11-30",
  "is_active": true,
  "created_at": "2025-03-01T00:00:00Z"
}
```

- **Validation**:
  - `term_type` must be one of: `annual`, `semester`, `trimester`, `quarterly`.
  - `start_date` must precede `end_date`.

---

### 2.3 Collection: `departments`
Represents organizational faculty divisions in colleges and universities.

```json
{
  "_id": "DEPT-CS",
  "institution_id": "INST-0421",
  "dept_code": "CSE",
  "name": "Computer Science and Engineering",
  "head_of_department": "Dr. Anita Roy",
  "email": "hod.cse@institution.ac.in",
  "phone": "+91 98765 43210",
  "campus_id": "CAMP-01",
  "is_active": true,
  "created_at": "2025-03-01T00:00:00Z"
}
```

---

### 2.4 Collection: `programmes`
Represents degrees, diplomas, or school curriculums offered by an institution.

```json
{
  "_id": "PROG-BTECH-CSE",
  "institution_id": "INST-0421",
  "department_id": "DEPT-CS",
  "programme_code": "BTECH-CS",
  "name": "Bachelor of Technology in Computer Science",
  "degree_type": "Bachelor",
  "total_semesters": 8,
  "total_credits": 160,
  "is_active": true,
  "created_at": "2025-03-01T00:00:00Z"
}
```

---

### 2.5 Collection: `classes`
Represents classes, grades, or cohort sections.

```json
{
  "_id": "CLS-10A",
  "institution_id": "INST-0421",
  "academic_year": "2025-26",
  "grade_level": "Class 10",
  "section": "A",
  "room_number": "Room 204",
  "capacity": 40,
  "class_teacher_name": "Priya Sharma",
  "class_teacher_id": "TEA-001",
  "programme_id": "CBSE-10",
  "campus_id": "CAMP-01",
  "created_at": "2025-03-01T00:00:00Z"
}
```

---

### 2.6 Collection: `subjects`
Represents courses and subjects with NEP 2020 credit allocations and multilingual descriptors.

```json
{
  "_id": "SUB-MATH-10",
  "institution_id": "INST-0421",
  "subject_code": "MATH-10",
  "subject_name": "Mathematics",
  "multilingual_name": "Ganita (Mathematics)",
  "credits": 4,
  "is_practical": false,
  "department_id": null,
  "programme_id": "CBSE-10",
  "grade_level": "Class 10",
  "applicable_to": "Class 10",
  "created_at": "2025-03-01T00:00:00Z"
}
```

---

### 2.7 Collection: `student_enrolments`
Represents student cohort enrolment with promotion tracking and section transfer audit trails.

```json
{
  "_id": "ENR-001",
  "institution_id": "INST-0421",
  "student_id": "STU-001",
  "student_name": "Aarav Patel",
  "enrolment_number": "ENR-2025-01",
  "academic_year_id": "AY-2025-26",
  "class_id": "CLS-10A",
  "programme_id": null,
  "status": "active",
  "is_current": true,
  "enrolment_date": "2025-06-05",
  "notes": "Regular annual intake",
  "section_transfer_history": [
    {
      "previous_section": "B",
      "new_section": "A",
      "transferred_at": "2025-07-02T10:00:00Z",
      "reason": "Parent request for second language compatibility"
    }
  ],
  "created_at": "2025-06-05T00:00:00Z"
}
```

- **Indices**:
  - `{"institution_id": 1, "student_id": 1, "academic_year_id": 1, "is_current": 1}`
  - `{"institution_id": 1, "enrolment_number": 1}`

---

### 2.8 Collection: `teacher_assignments`
Represents faculty allocations to subjects and classes.

```json
{
  "_id": "ASG-001",
  "institution_id": "INST-0421",
  "teacher_id": "TEA-001",
  "teacher_name": "Priya Sharma",
  "subject_id": "SUB-MATH-10",
  "class_id": "CLS-10A",
  "role_in_course": "Primary Teacher",
  "academic_year_id": "AY-2025-26",
  "created_at": "2025-06-01T00:00:00Z"
}
```

---

### 2.9 Collection: `academic_calendar`
Represents institutional events, exams, holidays, and deadlines.

```json
{
  "_id": "EVT-001",
  "institution_id": "INST-0421",
  "title": "Mid-Term Assessment Cycle",
  "event_type": "exam",
  "start_date": "2025-10-10",
  "end_date": "2025-10-22",
  "description": "Mid-term evaluations for all sections.",
  "academic_year_id": "AY-2025-26",
  "created_at": "2025-06-01T00:00:00Z"
}
```
