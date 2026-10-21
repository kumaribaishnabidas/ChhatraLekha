"""Authentication endpoints: login, refresh, logout and the current user."""

from __future__ import annotations

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import client_ip, get_db, get_principal
from app.audit import writer
from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    password_policy_violations,
    verify_password,
)
from app.repositories.audit import AuditRepository
from app.repositories.users import UserRepository
from app.schemas.auth import LoginRequest, RefreshRequest, TokenPair, UserOut

router = APIRouter(prefix="/auth", tags=["authentication"])

settings = get_settings()


@router.post("/login", response_model=TokenPair, summary="Sign in and receive a JWT pair")
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> TokenPair:
    """Exchange credentials for an access token and a refresh token."""
    users = UserRepository(db["users"], db["api_keys"], db["revoked_credentials"])
    audit = AuditRepository(db["audit_events"])

    identifier = payload.email.strip().lower()
    user = await users.by_email(identifier)
    if user is None:
        user = await users.by_user_id(payload.email.strip())

    if user is None or not verify_password(payload.password, user.get("password_hash", "")):
        await writer.log(
            audit,
            actor=identifier or "unknown",
            action="LOGIN_FAILED",
            subject=user["user_id"] if user else identifier,
            details="Invalid credentials presented.",
            category="SECURITY",
            ip_address=client_ip(request),
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid e-mail address or password.",
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="The account is not active."
        )

    await users.set_last_login(user["user_id"])
    await writer.log(
        audit,
        actor=user["user_id"],
        actor_role=user["role"],
        action="LOGIN",
        subject=user["user_id"],
        details=f"{user.get('full_name') or user.get('email')} signed in.",
        category="SECURITY",
        ip_address=client_ip(request),
    )

    return TokenPair(
        access_token=create_access_token(
            subject=user["user_id"],
            role=user["role"],
            institution_id=user.get("institution_id"),
        ),
        refresh_token=create_refresh_token(user["user_id"]),
        expires_in=settings.access_token_expire_minutes * 60,
        role=user["role"],
        user_id=user["user_id"],
        display_name=user.get("full_name") or user.get("email", ""),
        institution_id=user.get("institution_id"),
    )


@router.post("/refresh", response_model=TokenPair, summary="Exchange a refresh token")
async def refresh(
    payload: RefreshRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> TokenPair:
    """Issue a new access token from a valid refresh token."""
    try:
        claims = decode_token(payload.refresh_token, expected_type="refresh")
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired refresh token: {exc}",
        ) from exc

    users = UserRepository(db["users"], db["api_keys"], db["revoked_credentials"])
    user = await users.by_user_id(claims.get("sub") or "")
    if user is None or not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="The account is not active."
        )

    return TokenPair(
        access_token=create_access_token(
            subject=user["user_id"], role=user["role"], institution_id=user.get("institution_id")
        ),
        refresh_token=create_refresh_token(user["user_id"]),
        expires_in=settings.access_token_expire_minutes * 60,
        role=user["role"],
        user_id=user["user_id"],
        display_name=user.get("full_name") or user.get("email", ""),
        institution_id=user.get("institution_id"),
    )


@router.get("/me", response_model=UserOut, summary="The signed-in principal")
async def me(principal=Depends(get_principal)) -> UserOut:
    """Return the profile of the signed-in user."""
    user = principal.user or {}
    last_login = user.get("last_login_at")
    return UserOut(
        user_id=principal.subject,
        email=user.get("email", principal.email),
        full_name=principal.display_name,
        role=principal.role,
        institution_id=principal.institution_id,
        is_active=user.get("is_active", True),
        last_login_at=last_login.isoformat() if last_login else None,
    )


@router.get("/password-policy", summary="The password policy in force")
async def password_policy() -> dict:
    """Describe the password policy so the portal can validate live."""
    return {
        "min_length": 8,
        "requires_digit": True,
        "requires_letter": True,
        "description": "At least 8 characters, containing a letter and a digit.",
    }


@router.post("/check-password", summary="Check a candidate password")
async def check_password(password: str) -> dict:
    """Return the list of policy violations for a candidate password."""
    violations = password_policy_violations(password)
    return {"valid": not violations, "violations": violations}
