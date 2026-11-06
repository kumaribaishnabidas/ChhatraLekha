"""Schemas for ChhatraLekha Connected Campus (Schools and Colleges)."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.enums import (
    AnnouncementPriority,
    AssessmentStatus,
    AttendanceMode,
    AttendanceStatus,
    GuardianRelationshipType,
    GuardianVerificationStatus,
    InstitutionCategory,
    InstitutionVerificationStatus,
    TargetAudienceScope,
)


# ------------------------------------------------------------- 1. Onboarding
class InstitutionRegisterIn(BaseModel):
    """Payload to register an institution on ChhatraLekha."""

    name: str = Field(..., min_length=2, max_length=150)
    category: InstitutionCategory = Field(InstitutionCategory.SCHOOL, description="SCHOOL or COLLEGE")
    institution_type: str = Field("SCHOOL", min_length=2, max_length=50)
    state: str = Field(..., min_length=2, max_length=50)
    city: str = Field(..., min_length=2, max_length=50)
    address: str = Field("", max_length=250)
    affiliation: str = Field("", description="CBSE, ICSE, State Board, or University affiliation")
    contact_email: str = Field(..., min_length=5, max_length=100)
    contact_phone: str = Field("", max_length=20)
    admin_name: str = Field(..., min_length=2, max_length=100)
    admin_password: str = Field(..., min_length=8)


class InstitutionReviewIn(BaseModel):
    """Decision by platform operator on an institution registration."""

    decision: InstitutionVerificationStatus = Field(..., description="VERIFIED, REJECTED, or SUSPENDED")
    notes: str = Field("", max_length=500)


# ------------------------------------------------------------- 2. Academic Setup
class AcademicYearIn(BaseModel):
    year_label: str = Field(..., min_length=4, max_length=20, example="2025-26")
    start_date: str = Field(..., example="2025-06-01")
    end_date: str = Field(..., example="2026-05-31")
    admission_start_date: Optional[str] = None
    admission_end_date: Optional[str] = None
    is_current: bool = True
    status: str = Field("ACTIVE", description="ACTIVE, UPCOMING, COMPLETED, ARCHIVED")
    terms: List[str] = Field(default_factory=lambda: ["Term 1", "Term 2"])


class AcademicYearOut(BaseModel):
    id: str
    institution_id: str
    year_label: str
    start_date: str
    end_date: str
    admission_start_date: Optional[str] = None
    admission_end_date: Optional[str] = None
    is_current: bool
    status: str = "ACTIVE"
    terms: List[str]


class SemesterTermIn(BaseModel):
    academic_year: str = Field(..., example="2025-26")
    name: str = Field(..., min_length=2, max_length=100, example="Semester 1")
    term_type: str = Field("SEMESTER", description="SEMESTER, ANNUAL, TRIMESTER, QUARTER, CUSTOM")
    start_date: str = Field(..., example="2025-07-15")
    end_date: str = Field(..., example="2025-12-20")
    status: str = Field("ACTIVE", description="UPCOMING, ACTIVE, EXAM_PERIOD, CONCLUDED")


class SemesterTermOut(BaseModel):
    term_id: str
    institution_id: str
    academic_year: str
    name: str
    term_type: str
    start_date: str
    end_date: str
    status: str


class DepartmentIn(BaseModel):
    department_code: str = Field(..., min_length=1, max_length=20, example="CSE")
    name: str = Field(..., min_length=2, max_length=150, example="Department of Computer Science and Engineering")
    description: Optional[str] = None
    head_of_department_id: Optional[str] = None
    head_of_department_name: Optional[str] = None
    contact_email: Optional[str] = None
    campus_id: Optional[str] = None


class DepartmentOut(BaseModel):
    department_id: str
    institution_id: str
    department_code: str
    name: str
    description: Optional[str] = None
    head_of_department_id: Optional[str] = None
    head_of_department_name: Optional[str] = None
    contact_email: Optional[str] = None
    campus_id: Optional[str] = None
    faculty_count: int = 0
    programme_count: int = 0
    status: str = "ACTIVE"


class ProgrammeIn(BaseModel):
    programme_code: str = Field(..., min_length=1, max_length=30, example="BTECH-CSE")
    name: str = Field(..., min_length=2, max_length=150, example="Bachelor of Technology in Computer Science")
    department_id: Optional[str] = None
    academic_level: str = Field("UNDERGRADUATE", description="PRIMARY, SECONDARY, HIGHER_SECONDARY, UNDERGRADUATE, POSTGRADUATE, DOCTORAL")
    duration_years: int = Field(4, ge=1, le=8)
    total_semesters: int = Field(8, ge=1, le=16)
    degree_awarded: Optional[str] = "B.Tech"
    curriculum_framework: Optional[str] = "AICTE Model 2024"
    approved_intake: int = Field(60, ge=1, le=1000)


class ProgrammeOut(BaseModel):
    programme_id: str
    institution_id: str
    programme_code: str
    name: str
    department_id: Optional[str] = None
    academic_level: str
    duration_years: int
    total_semesters: int
    degree_awarded: Optional[str] = None
    curriculum_framework: Optional[str] = None
    approved_intake: int
    status: str = "ACTIVE"


class ClassSectionIn(BaseModel):
    """School class/grade and section definition."""

    grade_level: str = Field(..., min_length=1, max_length=30, example="Class 10")
    section: str = Field(..., min_length=1, max_length=10, example="A")
    academic_year: str = Field(..., example="2025-26")
    programme_id: Optional[str] = None
    room_number: Optional[str] = None
    capacity: int = Field(40, ge=1, le=200)
    class_teacher_id: Optional[str] = None
    class_teacher_name: Optional[str] = None


class ClassSectionOut(BaseModel):
    class_id: str
    institution_id: str
    grade_level: str
    section: str
    academic_year: str
    programme_id: Optional[str] = None
    room_number: Optional[str] = None
    capacity: int
    enrolled_count: int = 0
    class_teacher_id: Optional[str] = None
    class_teacher_name: Optional[str] = None
    status: str = "ACTIVE"


class SubjectIn(BaseModel):
    subject_code: str = Field(..., min_length=1, max_length=20, example="MATH-10")
    subject_name: str = Field(..., min_length=2, max_length=100, example="Mathematics")
    subject_name_hi: Optional[str] = None
    category: str = Field("CORE", example="CORE, ELECTIVE, LAB, PROJECT, FOUNDATION")
    applicable_to: str = Field(..., description="Class grade or College programme id", example="Class 10")
    department_id: Optional[str] = None
    programme_id: Optional[str] = None
    semester: Optional[int] = None
    credits: float = Field(3.0, ge=0, le=20)
    theory_hours: int = Field(3, ge=0, le=40)
    practical_hours: int = Field(0, ge=0, le=40)
    is_practical: bool = False


class SubjectOut(BaseModel):
    subject_id: str
    institution_id: str
    subject_code: str
    subject_name: str
    subject_name_hi: Optional[str] = None
    category: str
    applicable_to: str
    department_id: Optional[str] = None
    programme_id: Optional[str] = None
    semester: Optional[int] = None
    credits: float = 3.0
    theory_hours: int = 3
    practical_hours: int = 0
    is_practical: bool = False
    status: str = "ACTIVE"


class TeacherAssignmentIn(BaseModel):
    teacher_id: str = Field(...)
    teacher_name: str = Field(...)
    subject_id: str = Field(...)
    subject_name: str = Field(...)
    target_type: str = Field("CLASS", description="CLASS (school) or PROGRAMME (college)")
    target_id: str = Field(..., description="class_id or programme_id")
    target_label: str = Field(..., description="e.g. Class 10-A or B.Tech CSE Year 2")
    academic_year: Optional[str] = "2025-26"
    role_in_course: Optional[str] = "PRIMARY_INSTRUCTOR"


class TeacherAssignmentOut(BaseModel):
    assignment_id: str
    institution_id: str
    teacher_id: str
    teacher_name: str
    subject_id: str
    subject_name: str
    target_type: str
    target_id: str
    target_label: str
    academic_year: Optional[str] = "2025-26"
    role_in_course: Optional[str] = "PRIMARY_INSTRUCTOR"
    status: str = "ACTIVE"


class StudentEnrolmentIn(BaseModel):
    student_id: str = Field(..., min_length=2, max_length=100)
    student_name: str = Field(..., min_length=2, max_length=100)
    academic_year: str = Field(..., example="2025-26")
    roll_number: Optional[str] = None
    programme_id: Optional[str] = None
    programme_name: Optional[str] = None
    class_id: Optional[str] = None
    class_name: Optional[str] = None
    section: Optional[str] = None
    semester: Optional[int] = None
    remarks: Optional[str] = None


class StudentEnrolmentOut(BaseModel):
    enrolment_id: str
    institution_id: str
    student_id: str
    student_name: str
    roll_number: Optional[str] = None
    academic_year: str
    programme_id: Optional[str] = None
    programme_name: Optional[str] = None
    class_id: Optional[str] = None
    class_name: Optional[str] = None
    section: Optional[str] = None
    semester: Optional[int] = None
    status: str = "ACTIVE"
    enrolled_date: str
    promoted_date: Optional[str] = None
    is_current: bool = True
    remarks: Optional[str] = None


class StudentPromotionIn(BaseModel):
    target_academic_year: str = Field(..., example="2026-27")
    target_grade_or_semester: str = Field(..., example="Class 11")
    target_class_id: Optional[str] = None
    target_section: Optional[str] = None
    promotion_status: str = Field("PROMOTED", description="PROMOTED, RETAINED, COMPLETED")
    remarks: Optional[str] = None


class SectionTransferIn(BaseModel):
    target_class_id: str = Field(..., description="Target class_id with section")
    target_section: str = Field(..., example="B")
    transfer_reason: str = Field(..., min_length=3, max_length=200)


class AcademicCalendarEventIn(BaseModel):
    academic_year: str = Field(..., example="2025-26")
    title: str = Field(..., min_length=3, max_length=150)
    description: Optional[str] = None
    event_type: str = Field("HOLIDAY", description="HOLIDAY, EXAM, ADMISSION, SEMESTER_START, SEMESTER_END, ASSIGNMENT_DUE, INSTITUTION_EVENT")
    start_date: str = Field(..., example="2025-10-02")
    end_date: str = Field(..., example="2025-10-02")
    target_audience: str = Field("ALL", description="ALL, STUDENTS, TEACHERS, DEPARTMENT")
    is_holiday: bool = False
    timezone: str = "Asia/Kolkata"


class AcademicCalendarEventOut(BaseModel):
    event_id: str
    institution_id: str
    academic_year: str
    title: str
    description: Optional[str] = None
    event_type: str
    start_date: str
    end_date: str
    target_audience: str
    is_holiday: bool
    timezone: str


class AcademicOverviewOut(BaseModel):
    institution_id: str
    institution_name: str
    institution_category: str
    current_academic_year: Optional[str] = None
    total_departments: int = 0
    total_programmes: int = 0
    total_classes: int = 0
    total_subjects: int = 0
    total_enrolled_students: int = 0
    total_faculty_assigned: int = 0
    active_terms_count: int = 0
    upcoming_events_count: int = 0


# ------------------------------------------------------------- 3. Attendance
class AttendanceRecordItem(BaseModel):
    student_id: str = Field(..., description="Student APAAR or Internal reference")
    student_name: str = Field(...)
    status: AttendanceStatus = Field(AttendanceStatus.PRESENT)
    remarks: Optional[str] = None


class AttendanceBatchSubmitIn(BaseModel):
    session_date: str = Field(..., example="2026-10-31")
    mode: AttendanceMode = Field(AttendanceMode.DAILY)
    period_number: Optional[int] = None
    target_type: str = Field("CLASS", description="CLASS or COURSE")
    target_id: str = Field(..., description="class_id or programme_id")
    target_label: str = Field(...)
    records: List[AttendanceRecordItem]


class AttendanceSessionOut(BaseModel):
    session_id: str
    institution_id: str
    session_date: str
    mode: str
    period_number: Optional[int] = None
    target_type: str
    target_id: str
    target_label: str
    recorded_by: str
    total_students: int
    present_count: int
    absent_count: int
    late_count: int


# ------------------------------------------------------------- 4. Assessments & Marks
class AssessmentIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, example="Mid-Term Examination")
    academic_year: str = Field(..., example="2025-26")
    term: str = Field(..., example="Term 1")
    target_type: str = Field("CLASS", description="CLASS or PROGRAMME")
    target_id: str = Field(...)
    target_label: str = Field(...)
    subject_id: str = Field(...)
    subject_name: str = Field(...)
    max_marks: float = Field(100.0, gt=0)
    passing_marks: float = Field(35.0, ge=0)
    weightage_percent: Optional[float] = 100.0


class AssessmentMarkItem(BaseModel):
    student_id: str
    student_name: str
    marks_obtained: float = Field(..., ge=0)
    is_absent: bool = False
    remarks: Optional[str] = None


class AssessmentMarksSubmitIn(BaseModel):
    marks: List[AssessmentMarkItem]


class AssessmentOut(BaseModel):
    assessment_id: str
    institution_id: str
    name: str
    academic_year: str
    term: str
    target_type: str
    target_id: str
    target_label: str
    subject_id: str
    subject_name: str
    max_marks: float
    passing_marks: float
    status: AssessmentStatus
    created_by: str
    published_by: Optional[str] = None
    published_at: Optional[datetime] = None


class StudentResultOut(BaseModel):
    assessment_id: str
    assessment_name: str
    term: str
    subject_name: str
    max_marks: float
    passing_marks: float
    marks_obtained: float
    percentage: float
    grade: str
    status: str
    published_at: Optional[datetime] = None


# ------------------------------------------------------------- 5. Announcements
class AnnouncementIn(BaseModel):
    title: str = Field(..., min_length=3, max_length=150)
    content: str = Field(..., min_length=5, max_length=2000)
    priority: AnnouncementPriority = Field(AnnouncementPriority.NORMAL)
    target_scope: TargetAudienceScope = Field(TargetAudienceScope.ALL)
    target_id: Optional[str] = None
    target_label: Optional[str] = None
    target_role: Optional[str] = None
    target_departments: Optional[List[str]] = None
    target_classes: Optional[List[str]] = None
    scheduled_for: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    delivery_channels: Optional[List[str]] = Field(default_factory=lambda: ["IN_APP", "EMAIL"])
    attachment_title: Optional[str] = None
    attachment_url: Optional[str] = None


class AnnouncementUpdateIn(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=150)
    content: Optional[str] = Field(None, min_length=5, max_length=2000)
    priority: Optional[AnnouncementPriority] = None
    target_scope: Optional[TargetAudienceScope] = None
    target_id: Optional[str] = None
    target_label: Optional[str] = None
    target_role: Optional[str] = None
    target_departments: Optional[List[str]] = None
    target_classes: Optional[List[str]] = None
    scheduled_for: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    attachment_title: Optional[str] = None
    attachment_url: Optional[str] = None


class AnnouncementOut(BaseModel):
    announcement_id: str
    institution_id: str
    title: str
    content: str
    priority: str
    target_scope: str
    target_id: Optional[str] = None
    target_label: Optional[str] = None
    target_role: Optional[str] = None
    target_departments: Optional[List[str]] = None
    target_classes: Optional[List[str]] = None
    scheduled_for: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    delivery_channels: Optional[List[str]] = None
    delivery_summary: Optional[dict[str, int]] = None
    status: Optional[str] = "PUBLISHED"
    published_by: str
    published_at: datetime
    attachment_title: Optional[str] = None
    attachment_url: Optional[str] = None
    is_acknowledged: Optional[bool] = False


# ------------------------------------------------------------- 6. Guardian / Parent
class GuardianLinkRequestIn(BaseModel):
    student_identifier: str = Field(..., description="Student APAAR ID or internal student ref")
    student_dob: str = Field(..., example="2008-04-12")
    relationship: GuardianRelationshipType = Field(GuardianRelationshipType.FATHER)
    guardian_phone: str = Field(..., min_length=10, max_length=20)


class GuardianLinkVerifyIn(BaseModel):
    verification_status: GuardianVerificationStatus = Field(GuardianVerificationStatus.VERIFIED)
    notes: Optional[str] = None


class GuardianStudentOverviewOut(BaseModel):
    link_id: str
    student_id: str
    student_name: str
    institution_id: str
    institution_name: str
    academic_period: str
    class_or_programme: str
    relationship: str
    verification_status: str
    attendance_percentage: float
    total_sessions: int
    present_sessions: int
    published_results: List[StudentResultOut] = []
    recent_notices: List[AnnouncementOut] = []
