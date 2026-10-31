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
    is_current: bool = True
    terms: List[str] = Field(default_factory=lambda: ["Term 1", "Term 2"])


class AcademicYearOut(BaseModel):
    id: str
    institution_id: str
    year_label: str
    start_date: str
    end_date: str
    is_current: bool
    terms: List[str]


class ClassSectionIn(BaseModel):
    """School class/grade and section definition."""

    grade_level: str = Field(..., min_length=1, max_length=30, example="Class 10")
    section: str = Field(..., min_length=1, max_length=10, example="A")
    academic_year: str = Field(..., example="2025-26")
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
    room_number: Optional[str] = None
    capacity: int
    class_teacher_id: Optional[str] = None
    class_teacher_name: Optional[str] = None


class SubjectIn(BaseModel):
    subject_code: str = Field(..., min_length=1, max_length=20, example="MATH-10")
    subject_name: str = Field(..., min_length=2, max_length=100, example="Mathematics")
    category: str = Field("CORE", example="CORE, ELECTIVE, LAB")
    applicable_to: str = Field(..., description="Class grade or College programme id", example="Class 10")


class SubjectOut(BaseModel):
    subject_id: str
    institution_id: str
    subject_code: str
    subject_name: str
    category: str
    applicable_to: str


class TeacherAssignmentIn(BaseModel):
    teacher_id: str = Field(...)
    teacher_name: str = Field(...)
    subject_id: str = Field(...)
    subject_name: str = Field(...)
    target_type: str = Field("CLASS", description="CLASS (school) or PROGRAMME_COURSE (college)")
    target_id: str = Field(..., description="class_id or programme_id")
    target_label: str = Field(..., description="e.g. Class 10-A or B.Tech CSE Year 2")


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
