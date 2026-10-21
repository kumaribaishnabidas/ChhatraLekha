"""Authentication endpoints: login, refresh, logout and the current user."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import client_ip, get_principal
from app.audit import writer
from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    password_policy_violations,
    verify_password,
)
from app.models import User
from app.schemas.auth import LoginRequest, RefreshRequest, TokenPair, UserOut

router = APIRouter(prefix="/auth", tags=["authentication"])

settings = get_settings()


@router.post("/login", response_model=TokenPair, summary="Sign in and receive a JWT pair")
async def login(
    payload: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> TokenPair:
    """Exchange credentials for an access token and a refresh token."""
    identifier = payload.email.strip().lower()
    result = await session.execute(
        select(User).where(
            (User.email == identifier) | (User.user_id == payload.email.strip())
        )
    )
    user = result.scalar_one_or_none()

    if user is None or not verify_password(payload.password, user.password_hash):
        await writer.log(
            session,
            actor=payload.email.strip() or "unknown",
            action="LOGIN_FAILED",
            subject=user.user_id if user else identifier,
            details="Invalid credentials presented.",
            category="SECURITY",
            ip_address=client_ip(request),
        )
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid e-mail address or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="The account is not active."
        )

    user.last_login_at = datetime.now(timezone.utc)
    await writer.log(
        session,
        actor=user.user_id,
        actor_role=user.role,
        action="LOGIN",
        subject=user.user_id,
        details=f"{user.full_name or user.email} signed in.",
        category="SECURITY",
        ip_address=client_ip(request),
    )
    await session.commit()

    return TokenPair(
        access_token=create_access_token(
            subject=user.user_id,
            role=user.role,
            institution_id=user.institution_id,
        ),
        refresh_token=create_refresh_token(user.user_id),
        expires_in=settings.access_token_expire_minutes * 60,
        role=user.role,
        user_id=user.user_id,
        display_name=user.full_name or user.email,
        institution_id=user.institution_id,
    )


@router.post("/refresh", response_model=TokenPair, summary="Exchange a refresh token")
async def refresh(
    payload: RefreshRequest,
    session: AsyncSession = Depends(get_db),
) -> TokenPair:
    """Issue a new access token from a valid refresh token."""
    import jwt

    try:
        claims = decode_token(payload.refresh_token, expected_type="refresh")
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired refresh token: {exc}",
        ) from exc

    result = await session.execute(select(User).where(User.user_id == claims.get("sub")))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="The account is not active."
        )

    return TokenPair(
        access_token=create_access_token(
            subject=user.user_id, role=user.role, institution_id=user.institution_id
        ),
        refresh_token=create_refresh_token(user.user_id),
        expires_in=settings.access_token_expire_minutes * 60,
        role=user.role,
        user_id=user.user_id,
        display_name=user.full_name or user.email,
        institution_id=user.institution_id,
    )


@router.get("/me", response_model=UserOut, summary="The signed-in principal")
async def me(principal=Depends(get_principal)) -> UserOut:
    """Return the profile of the signed-in user."""
    user = principal.user
    return UserOut(
        user_id=principal.subject,
        email=user.email if user else "",
        full_name=principal.display_name,
        role=principal.role,
        institution_id=principal.institution_id,
        is_active=user.is_active if user else True,
        last_login_at=user.last_login_at.isoformat() if user and user.last_login_at else None,
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
