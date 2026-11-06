"""Profile Management Module Schemas."""

from __future__ import annotations

from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class PlatformType(str, Enum):
    COMMON = "common"
    WEB = "web"
    ANDROID = "android"
    IOS = "ios"


class EmailType(str, Enum):
    PERSONAL = "PERSONAL"
    INSTITUTIONAL = "INSTITUTIONAL"


class ProfilePictures(BaseModel):
    common_url: Optional[str] = None
    web_url: Optional[str] = None
    android_url: Optional[str] = None
    ios_url: Optional[str] = None
    use_common: bool = True


class UserPreferenceOut(BaseModel):
    preferred_language: str = "en"
    theme: str = "system"
    high_contrast: bool = False
    screen_reader_optimized: bool = False
    directory_visible: bool = True


class UserPreferenceUpdate(BaseModel):
    preferred_language: Optional[str] = None
    theme: Optional[str] = None
    high_contrast: Optional[bool] = None
    screen_reader_optimized: Optional[bool] = None
    directory_visible: Optional[bool] = None


class InstitutionMembershipOut(BaseModel):
    membership_id: str
    user_id: str
    institution_id: str
    institution_name: str
    role: str
    role_label: str
    department: Optional[str] = None
    academic_year: Optional[str] = None
    is_primary: bool = False
    member_status: str = "ACTIVE"


class EmailRegisterRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=120)
    email_type: EmailType = EmailType.PERSONAL
    institution_id: Optional[str] = None


class EmailVerifyCodeRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=120)
    code: str = Field(..., min_length=6, max_length=6)


class PictureUploadRequest(BaseModel):
    platform: PlatformType = PlatformType.COMMON
    image_base64: str = Field(..., description="Base64 encoded data URI or raw base64 string")
    preset_avatar_id: Optional[str] = None


class PictureSettingsRequest(BaseModel):
    use_common: bool = True


class UserProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    display_name: Optional[str] = Field(None, min_length=2, max_length=60)
    phone: Optional[str] = Field(None, max_length=20)
    bio: Optional[str] = Field(None, max_length=300)
    preferences: Optional[UserPreferenceUpdate] = None


class UserSessionOut(BaseModel):
    session_id: str
    ip_address: str
    device: str
    last_active_at: str
    is_current: bool = False


class UserProfileOut(BaseModel):
    user_id: str
    full_name: str
    display_name: str
    phone: Optional[str] = None
    bio: Optional[str] = None
    role: str
    role_label: str
    account_status: str = "ACTIVE"
    profile_completion_percentage: int
    personal_email: Optional[str] = None
    personal_email_verified: bool = False
    institution_email: Optional[str] = None
    institution_email_verified: bool = False
    profile_pictures: ProfilePictures
    active_avatar_url: Optional[str] = None
    preferences: UserPreferenceOut
    memberships: List[InstitutionMembershipOut] = Field(default_factory=list)
    role_metadata: dict[str, Any] = Field(default_factory=dict)
    active_institution_id: Optional[str] = None
    created_at: str


class ActiveInstitutionSwitchRequest(BaseModel):
    institution_id: str
