"""Student, institution and enrolment schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    AdmissionQuota,
    Gender,
    SocialCategory,
    VerificationStatus,
)
from app.schemas.anomaly import AnomalyOut


class StudentIn(BaseModel):
    """The fields an institution supplies when onboarding a student."""

    apaar_id: str = Field(..., min_length=1, max_length=32)
    student_name: str = Field("", max_length=255)
    date_of_birth: str = Field("", max_length=32)
    gender: Gender = Gender.OTHER
    institution_id: str = Field(..., max_length=32)
    program_id: str = Field(..., max_length=64)
    academic_year: str = Field("2024-25", max_length=16)
    admission_quota: AdmissionQuota = AdmissionQuota.MERIT
    enrollment_date: str = Field("", max_length=32)
    student_institute_roll_no: str = Field("", max_length=64)
    nationality: str = Field("Indian", max_length=80)
    passport_number: Optional[str] = Field(None, max_length=64)
    visa_validity: Optional[str] = Field(None, max_length=32)
    country_of_origin: Optional[str] = Field(None, max_length=80)
    abc_account_id: Optional[str] = Field(None, max_length=80)
    social_category: SocialCategory = SocialCategory.GENERAL
    admission_date: Optional[str] = Field(None, max_length=32)
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=40)
    state_of_domicile: Optional[str] = Field(None, max_length=80)
    # Extended academic unit & school/college fields:
    education_level: Optional[str] = Field(None, max_length=32)
    grade_level: Optional[str] = Field(None, max_length=32)
    section: Optional[str] = Field(None, max_length=16)
    stream: Optional[str] = Field(None, max_length=32)
    board: Optional[str] = Field(None, max_length=64)
    medium_of_instruction: Optional[str] = Field(None, max_length=32)
    guardian_name: Optional[str] = Field(None, max_length=255)
    guardian_relationship: Optional[str] = Field(None, max_length=32)
    guardian_contact: Optional[str] = Field(None, max_length=40)
    is_minor: Optional[bool] = None
    semester: Optional[int] = None
    batch: Optional[str] = Field(None, max_length=32)


class StudentCreate(StudentIn):
    """The body of ``POST /api/students``."""


class StudentUpdate(BaseModel):
    """The body of ``PUT /api/students/{apaar_id}`` - every field optional."""

    student_name: Optional[str] = Field(None, max_length=255)
    date_of_birth: Optional[str] = Field(None, max_length=32)
    gender: Optional[Gender] = None
    program_id: Optional[str] = Field(None, max_length=64)
    academic_year: Optional[str] = Field(None, max_length=16)
    admission_quota: Optional[AdmissionQuota] = None
    enrollment_date: Optional[str] = Field(None, max_length=32)
    student_institute_roll_no: Optional[str] = Field(None, max_length=64)
    nationality: Optional[str] = Field(None, max_length=80)
    passport_number: Optional[str] = None
    visa_validity: Optional[str] = None
    country_of_origin: Optional[str] = None
    abc_account_id: Optional[str] = None
    social_category: Optional[SocialCategory] = None
    admission_date: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    state_of_domicile: Optional[str] = None
    record_status: Optional[str] = None
    education_level: Optional[str] = None
    grade_level: Optional[str] = None
    section: Optional[str] = None
    stream: Optional[str] = None
    board: Optional[str] = None
    medium_of_instruction: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_relationship: Optional[str] = None
    guardian_contact: Optional[str] = None
    is_minor: Optional[bool] = None
    semester: Optional[int] = None
    batch: Optional[str] = None


class StudentStatusUpdate(BaseModel):
    """Body of POST /api/students/{apaar_id}/status."""

    record_status: str = Field(..., pattern="^(ADMITTED|ACTIVE|ON_LEAVE|TRANSFERRED|GRADUATED|WITHDRAWN)$")
    reason: str = Field(..., min_length=3, max_length=500)
    effective_date: Optional[str] = None
    is_active: Optional[bool] = None


class StudentOut(BaseModel):
    """A student enrolment record as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    record_id: str = ""
    apaar_id: str
    student_name: str
    date_of_birth: str
    gender: Gender
    institution_id: str
    program_id: str
    academic_year: str
    admission_quota: AdmissionQuota
    enrollment_date: str
    student_institute_roll_no: str
    nationality: str
    passport_number: Optional[str] = None
    visa_validity: Optional[str] = None
    country_of_origin: Optional[str] = None
    abc_account_id: Optional[str] = None
    verification_status: VerificationStatus
    is_active: bool
    record_status: str = "ACTIVE"
    submission_source: str = "MANUAL"
    social_category: SocialCategory
    admission_date: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    state_of_domicile: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    masked_apaar_id: str = ""
    # Extended academic unit / school & college fields:
    education_level: Optional[str] = None
    grade_level: Optional[str] = None
    section: Optional[str] = None
    stream: Optional[str] = None
    board: Optional[str] = None
    medium_of_instruction: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_relationship: Optional[str] = None
    guardian_contact: Optional[str] = None
    is_minor: Optional[bool] = None
    semester: Optional[int] = None
    batch: Optional[str] = None


class VerificationResult(BaseModel):
    """The outcome of a credential verification."""

    verified: bool
    verdict: str
    reason: str
    algorithm: Optional[str] = None
    key_id: str = ""
    apaar_id: str
    student: Optional[StudentOut] = None
    institution_name: Optional[str] = None
    program_name: Optional[str] = None
    seal: Optional[str] = None
    consent_note: Optional[str] = None
    anomalies: list["AnomalyOut"] = []
    verified_at: str = ""


class BatchUploadResult(BaseModel):
    """The outcome of a bulk CSV commit."""

    total_rows: int
    committed: int
    skipped: int
    critical_rows: int
    warning_rows: int
    duplicate_rows: int
    unknown_programs: list[str] = []
    anomalies_detected: int = 0
    program_impacts: list[dict] = []


class InstitutionOut(BaseModel):
    """An AICTE-approved institution."""

    model_config = ConfigDict(from_attributes=True)

    institution_id: str
    name: str
    institution_type: str
    state: str
    city: str
    affiliation_university: str
    approval_year: int
    naac_grade: str
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True
    # Multi-tier institution fields:
    category: Optional[str] = None
    kind: Optional[str] = None
    district: Optional[str] = None
    management_type: Optional[str] = None
    affiliation: Optional[str] = None
    identifiers: list[dict] = []
    rule_pack: Optional[str] = None


class ProgrammeIntakeIn(BaseModel):
    """The body used to declare a programme's sanctioned capacity."""

    program_id: str = Field(..., max_length=64)
    institution_id: str = Field(..., max_length=32)
    program_name: str = Field(..., max_length=255)
    program_level: str = Field("UG", max_length=16)
    academic_year: str = Field("2024-25", max_length=16)
    policy_version: str = Field("aph-2024-01", max_length=32)
    approved_intake: int = Field(0, ge=0, le=10000)
    max_supernumerary_nri: int = Field(0, ge=0, le=10000)
    max_supernumerary_fn_oci: int = Field(0, ge=0, le=10000)
    max_supernumerary_tfw: int = Field(0, ge=0, le=10000)
    max_pmsss: int = Field(0, ge=0, le=10000)


class ProgrammeIntakeOut(ProgrammeIntakeIn):
    """A programme's sanctioned capacity."""

    model_config = ConfigDict(from_attributes=True)

    id: str = ""
    total_sanctioned: int = 0


VerificationResult.model_rebuild()
