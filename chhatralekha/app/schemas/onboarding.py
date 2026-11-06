"""Schemas for user onboarding, role selection and institution joining."""

from __future__ import annotations

from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class OnboardingAccountPurpose(str, Enum):
    STUDENT = "student"
    PARENT = "parent"
    TEACHER = "teacher"
    INSTITUTION_ADMIN = "institution_admin"


class BasicProfileIn(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    preferred_language: str = Field("en", min_length=2, max_length=10)
    phone: Optional[str] = Field(None, max_length=25)
    avatar_url: Optional[str] = None


class JoinRequestIn(BaseModel):
    institution_id: str = Field(..., min_length=2, max_length=64)
    requested_role: str = Field(..., min_length=2, max_length=64)
    course_name: Optional[str] = Field(None, max_length=120)
    class_grade: Optional[str] = Field(None, max_length=60)
    academic_year: Optional[str] = Field(None, max_length=20)
    student_identifier: Optional[str] = Field(None, max_length=64)
    student_dob: Optional[str] = Field(None, max_length=32)
    relationship: Optional[str] = Field(None, max_length=32)
    department: Optional[str] = Field(None, max_length=120)
    subject_specialization: Optional[str] = Field(None, max_length=120)
    employee_id: Optional[str] = Field(None, max_length=64)
    designation: Optional[str] = Field(None, max_length=120)
    authority_proof_notes: Optional[str] = Field(None, max_length=500)


class JoinRequestOut(BaseModel):
    request_id: str
    user_id: str
    user_name: str
    user_email: str
    institution_id: str
    institution_name: str
    requested_role: str
    role_details: dict[str, Any] = Field(default_factory=dict)
    status: str = "PENDING"
    created_at: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    review_notes: Optional[str] = None


class JoinRequestReviewIn(BaseModel):
    decision: str = Field(..., pattern="^(APPROVED|REJECTED)$")
    notes: Optional[str] = Field(None, max_length=300)


class InstitutionSearchItem(BaseModel):
    institution_id: str
    name: str
    category: str
    institution_type: str
    city: str
    state: str
    is_registered: bool = True
    is_active: bool = True
    affiliation: Optional[str] = None


class OnboardingStatusOut(BaseModel):
    user_id: str
    full_name: str
    email: str
    profile_completed: bool
    selected_role: Optional[str] = None
    active_institution_id: Optional[str] = None
    active_institution_name: Optional[str] = None
    memberships_count: int = 0
    pending_requests: List[JoinRequestOut] = Field(default_factory=list)
    can_proceed_to_dashboard: bool
    recommended_dashboard: str


class OnboardingCompletionIn(BaseModel):
    selected_role: str = Field(..., min_length=2, max_length=64)
    institution_id: Optional[str] = None
    notes: Optional[str] = None
