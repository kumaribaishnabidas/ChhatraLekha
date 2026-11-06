"""Profiles Module Export."""

from app.modules.profiles.router import router
from app.modules.profiles.schemas import (
    ActiveInstitutionSwitchRequest,
    EmailRegisterRequest,
    EmailType,
    EmailVerifyCodeRequest,
    InstitutionMembershipOut,
    PictureSettingsRequest,
    PictureUploadRequest,
    PlatformType,
    ProfilePictures,
    UserPreferenceOut,
    UserPreferenceUpdate,
    UserProfileOut,
    UserProfileUpdateRequest,
    UserSessionOut,
)
from app.modules.profiles.service import ProfileService

__all__ = [
    "router",
    "ProfileService",
    "PlatformType",
    "EmailType",
    "ProfilePictures",
    "UserPreferenceOut",
    "UserPreferenceUpdate",
    "InstitutionMembershipOut",
    "EmailRegisterRequest",
    "EmailVerifyCodeRequest",
    "PictureUploadRequest",
    "PictureSettingsRequest",
    "UserProfileUpdateRequest",
    "UserSessionOut",
    "UserProfileOut",
    "ActiveInstitutionSwitchRequest",
]
