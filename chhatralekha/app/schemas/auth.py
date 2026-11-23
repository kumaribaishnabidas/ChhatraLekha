"""Authentication schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    """Credentials presented to ``POST /api/auth/login``."""

    email: str = Field(..., description="Registered e-mail address or user id.")
    password: str = Field(..., min_length=1, max_length=256)
    institution_id: str | None = None


class DemoLoginRequest(BaseModel):
    """Role and optional academic context presented to ``POST /api/auth/demo-login``."""

    role: str = Field(..., description="Demo role: student, parent, teacher, school_admin, college_admin, university_admin.")
    education_type: str | None = Field(None, description="Optional education category: 'school' or 'college'.")
    institution_id: str | None = Field(None, description="Selected institution identifier.")
    class_name: str | None = Field(None, description="Selected school class level, e.g. 'Class 10'.")
    section: str | None = Field(None, description="Selected school section, e.g. 'A'.")
    program_id: str | None = Field(None, description="Selected college degree programme, e.g. 'BTECH_CSE'.")
    semester: str | None = Field(None, description="Selected college semester, e.g. 'Semester 5'.")
    department: str | None = Field(None, description="Optional college department or specialization branch.")


class DemoSchoolClass(BaseModel):
    class_name: str
    sections: list[str] = Field(default_factory=lambda: ["A"])
    has_demo_student: bool = True


class DemoSchoolInstitution(BaseModel):
    institution_id: str
    name: str
    type: str = "SCHOOL"
    city: str
    state: str
    board: str = "CBSE"
    classes: list[DemoSchoolClass] = Field(default_factory=list)


class DemoCollegeCourse(BaseModel):
    program_id: str
    program_name: str
    level: str = "UG"
    semesters: list[str] = Field(default_factory=list)
    department: str | None = None
    branches: list[str] = Field(default_factory=list)


class DemoCollegeInstitution(BaseModel):
    institution_id: str
    name: str
    type: str = "COLLEGE"
    city: str
    state: str
    affiliation: str = ""
    courses: list[DemoCollegeCourse] = Field(default_factory=list)


class DemoAcademicContextOut(BaseModel):
    """Available institutions, classes, and programmes for demo academic onboarding."""

    schools: list[DemoSchoolInstitution]
    colleges: list[DemoCollegeInstitution]


class RefreshRequest(BaseModel):
    """A refresh token presented to ``POST /api/auth/refresh``."""

    refresh_token: str


class LogoutRequest(BaseModel):
    """Payload presented to ``POST /api/auth/logout``."""

    refresh_token: str | None = Field(None, description="The refresh token of the session to terminate.")
    all_sessions: bool = Field(False, description="Whether to revoke all active sessions for the user.")


class LogoutResponse(BaseModel):
    """Response returned by ``POST /api/auth/logout``."""

    status: str = "success"
    message: str = "Logged out successfully."
    revoked_sessions_count: int = 1


class RegisterRequest(BaseModel):
    """Payload presented to ``POST /api/auth/register`` for self-service registration."""

    email: str = Field(..., description="Registered e-mail address.")
    password: str = Field(..., min_length=1, max_length=256, description="Account password.")
    full_name: str = Field(..., min_length=1, max_length=128, description="User full name.")
    role: str = Field("student", description="Requested role: student, parent, teacher, or institution_admin.")
    identifier: str | None = Field(None, max_length=128, description="Optional APAAR ID, roll number, or institution name.")


class RegisterResponse(BaseModel):
    """Response returned by ``POST /api/auth/register``."""

    status: str = "success"
    message: str
    user_id: str
    email: str
    role: str
    requires_approval: bool = False


class TokenPair(BaseModel):
    """The issued token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    role: str
    user_id: str
    display_name: str
    institution_id: str | None = None
    apaar_id: str | None = None


class UserOut(BaseModel):
    """A signed-in principal."""

    model_config = ConfigDict(from_attributes=True)

    user_id: str
    email: str
    full_name: str
    role: str
    institution_id: str | None = None
    apaar_id: str | None = None
    is_active: bool = True
    last_login_at: str | None = None
