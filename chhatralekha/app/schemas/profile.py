"""Profile schemas for ChhatraLekha."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProfilePictures(BaseModel):
    """Platform-specific and common profile picture URLs."""

    common_url: str | None = None
    web_url: str | None = None
    android_url: str | None = None
    ios_url: str | None = None
    use_common: bool = True


class EmailUpdateRequest(BaseModel):
    """Request to associate or update an email address."""

    email_type: str = Field(..., pattern="^(personal|institution)$")
    email: str = Field(..., min_length=5, max_length=120)


class EmailVerifyRequest(BaseModel):
    """Request to verify an email address with a 6-digit code."""

    email_type: str = Field(..., pattern="^(personal|institution)$")
    code: str = Field(..., min_length=4, max_length=10)


class ProfileUpdateRequest(BaseModel):
    """Permitted editable fields on the user profile."""

    full_name: str | None = Field(None, min_length=2, max_length=100)
    mobile: str | None = Field(None, max_length=20)
    preferred_language: str | None = Field(None, max_length=10)


class PictureUploadRequest(BaseModel):
    """Payload to update an avatar for a specific platform or all platforms."""

    platform: str = Field("common", pattern="^(common|web|android|ios)$")
    image_url: str = Field(..., min_length=1, description="Data URL or image URI")


class PictureSettingsRequest(BaseModel):
    """Toggle between common avatar and platform-specific avatars."""

    use_common: bool


class UserSessionOut(BaseModel):
    """Active user session description."""

    session_id: str
    ip_address: str
    device: str
    last_active_at: str
    is_current: bool = True


class CompleteProfileOut(BaseModel):
    """Comprehensive role-aware user profile output."""

    user_id: str
    full_name: str
    role: str
    role_label: str
    email: str
    personal_email: str | None = None
    personal_email_verified: bool = False
    institution_email: str | None = None
    institution_email_verified: bool = False
    mobile: str | None = None
    preferred_language: str = "en"
    institution_id: str | None = None
    institution_name: str | None = None
    account_status: str = "ACTIVE"
    created_at: str
    profile_completion_percentage: int
    profile_pictures: ProfilePictures
    active_avatar_url: str | None = None

    # Role-specific metadata blocks
    student_details: dict[str, Any] | None = None
    teacher_details: dict[str, Any] | None = None
    admin_details: dict[str, Any] | None = None
    parent_details: dict[str, Any] | None = None

