# ADR-002: Academic Unit Abstraction

**Status:** Accepted  
**Date:** October 2026  
**Context:**  
In higher education models, students are admitted to programmes or branches (e.g. `program_id = "BTECH-CSE"`), organized by semesters, batches, and course types. In primary and secondary schools, students are enrolled in classes/grades (e.g. `Class 10`), subdivided into sections (e.g. `Section A`), and senior secondary streams (e.g. `Science`, `Commerce`, `Arts`). Forcing schools to model grades as technical programmes or polluting the core student document with dozens of optional disjoint fields causes schema fragmentation and unclear business invariants.

**Decision:**  
We introduce an **Academic Unit** abstraction separating common identity attributes from level-specific academic metadata:
1. **Common Student Identity Core**:
   - `student_id`, `name`, `dob`, `gender`, `category`, `academic_year`, `enrollment_date`, `status`, `institution_id`.
   - External identifiers: optional APAAR ID or internal institutional reference (`student_institute_roll_no`).
2. **Level-Specific Extensions**:
   - **School Extension** (`SchoolAcademicUnit` / school fields):
     - `education_level` (e.g. `SECONDARY`, `SENIOR_SECONDARY`).
     - `grade_level` (e.g. "Class 10").
     - `section` (e.g. "A").
     - `stream` (e.g. "Science", optional for grades 11-12).
     - `board` (e.g. "CBSE", "ICSE", "State Board").
     - `medium_of_instruction` (e.g. "English", "Hindi").
     - `guardian_name`, `guardian_relationship`, `guardian_contact`.
     - `is_minor` (computed or explicit flag).
   - **College Extension** (`CollegeAcademicUnit` / higher ed fields):
     - `program_id`, `department`, `semester`, `batch`, `course_type`, `quota`.
3. Backward Compatibility:
   - All school fields on `StudentRecord` are optional with `None` default, ensuring existing college records deserialize and serialize without breakage.
   - APIs accept level-appropriate payloads and validate presence of relevant unit fields based on `institution.category`.

**Consequences:**  
- Positive: Single, clean mental model for administrators and queries across both schools and colleges.
- Positive: Enables unified reporting and audit trails across an individual student's entire educational lifecycle.
