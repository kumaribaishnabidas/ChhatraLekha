"""Profile Management REST Router."""

from __future__ import annotations

from typing import Any, List
from fastapi import APIRouter, Depends, Query, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import Principal, client_ip, get_db, get_principal
from app.models.documents import utcnow
from app.modules.profiles.schemas import (
    ActiveInstitutionSwitchRequest,
    EmailRegisterRequest,
    EmailVerifyCodeRequest,
    InstitutionMembershipOut,
    PictureSettingsRequest,
    PictureUploadRequest,
    PlatformType,
    ProfilePictures,
    UserProfileOut,
    UserProfileUpdateRequest,
    UserSessionOut,
)
from app.modules.profiles.service import ProfileService

router = APIRouter(prefix="/profiles", tags=["profile-management"])


@router.get("/me", response_model=UserProfileOut, summary="Fetch complete role-tailored profile")
async def get_my_profile(
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> UserProfileOut:
    service = ProfileService(db)
    return await service.get_profile(principal)


@router.put("/me", response_model=UserProfileOut, summary="Update profile details and preferences")
async def update_my_profile(
    payload: UserProfileUpdateRequest,
    request: Request,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> UserProfileOut:
    service = ProfileService(db)
    return await service.update_profile(principal, payload, client_ip(request))


@router.get("/me/memberships", response_model=List[InstitutionMembershipOut], summary="List user institution memberships")
async def get_my_memberships(
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> List[InstitutionMembershipOut]:
    service = ProfileService(db)
    user = await service.get_user_doc(principal)
    return await service.get_memberships(principal, user)


@router.post("/me/active-institution", response_model=UserProfileOut, summary="Switch active institution tenant")
async def switch_active_institution(
    payload: ActiveInstitutionSwitchRequest,
    request: Request,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> UserProfileOut:
    service = ProfileService(db)
    return await service.switch_active_institution(principal, payload, client_ip(request))


@router.post("/me/picture", response_model=ProfilePictures, summary="Upload profile avatar")
async def upload_profile_picture(
    payload: PictureUploadRequest,
    request: Request,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> ProfilePictures:
    service = ProfileService(db)
    return await service.upload_picture(principal, payload, client_ip(request))


@router.delete("/me/picture", response_model=ProfilePictures, summary="Remove platform profile avatar")
async def remove_profile_picture(
    request: Request,
    platform: PlatformType = Query(PlatformType.COMMON),
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> ProfilePictures:
    service = ProfileService(db)
    return await service.remove_picture(principal, platform, client_ip(request))


@router.put("/me/picture/settings", response_model=ProfilePictures, summary="Toggle common picture usage")
async def update_picture_settings(
    payload: PictureSettingsRequest,
    request: Request,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> ProfilePictures:
    service = ProfileService(db)
    return await service.update_picture_settings(principal, payload, client_ip(request))


@router.post("/me/email", summary="Register personal or institutional email")
async def register_email(
    payload: EmailRegisterRequest,
    request: Request,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict[str, Any]:
    service = ProfileService(db)
    return await service.register_email(principal, payload, client_ip(request))


@router.post("/me/verify-email", summary="Confirm email verification code")
async def verify_email_code(
    payload: EmailVerifyCodeRequest,
    request: Request,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict[str, Any]:
    service = ProfileService(db)
    return await service.verify_email_code(principal, payload, client_ip(request))


@router.get("/me/sessions", response_model=List[UserSessionOut], summary="List active sessions")
async def list_user_sessions(
    request: Request,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> List[UserSessionOut]:
    ip = client_ip(request)
    now_str = utcnow().isoformat()
    return [
        UserSessionOut(
            session_id=f"SESS-CURR-{principal.subject[-4:]}",
            ip_address=ip or "127.0.0.1",
            device="Active Web Browser / Primary Session",
            last_active_at=now_str,
            is_current=True,
        )
    ]

