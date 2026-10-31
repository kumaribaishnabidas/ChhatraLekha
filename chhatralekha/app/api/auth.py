"""Authentication endpoints: login, refresh, logout and the current user."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlencode

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
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
from app.schemas.auth import DemoLoginRequest, LoginRequest, RefreshRequest, TokenPair, UserOut
from app.services import google

logger = logging.getLogger("chhatralekha.auth")

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

    extra = {"apaar_id": user["apaar_id"]} if user.get("apaar_id") else None
    return TokenPair(
        access_token=create_access_token(
            subject=user["user_id"],
            role=user["role"],
            institution_id=user.get("institution_id"),
            extra_claims=extra,
        ),
        refresh_token=create_refresh_token(user["user_id"]),
        expires_in=settings.access_token_expire_minutes * 60,
        role=user["role"],
        user_id=user["user_id"],
        display_name=user.get("full_name") or user.get("email", ""),
        institution_id=user.get("institution_id"),
        apaar_id=user.get("apaar_id"),
    )


DEMO_PERSONA_CATALOG = {
    "student": {
        "email": "student.demo@example.com",
        "full_name": "Aarav Sharma (Student)",
        "role": "student",
        "apaar_id": "992100000001",
        "institution_id": "INST-0421",
    },
    "parent": {
        "email": "parent.demo@example.com",
        "full_name": "Sunita Sharma (Parent/Guardian)",
        "role": "parent",
        "apaar_id": "992100000001",
        "institution_id": "INST-0421",
    },
    "teacher": {
        "email": "teacher.demo@example.com",
        "full_name": "Prof. Rajesh Kumar (Faculty)",
        "role": "teacher",
        "institution_id": "INST-0421",
    },
    "school_admin": {
        "email": "schooladmin.demo@example.com",
        "full_name": "Principal Meera Nair (School Administrator)",
        "role": "institution_admin",
        "institution_id": "SCH-DEL-001",
    },
    "college_admin": {
        "email": "collegeadmin.demo@example.com",
        "full_name": "Director Ramesh Kulkarni (College Administrator)",
        "role": "institution_admin",
        "institution_id": "INST-0421",
    },
    "university_admin": {
        "email": "universityadmin.demo@example.com",
        "full_name": "Dr. Ananya Iyer (University Administrator)",
        "role": "aicte_admin",
        "institution_id": None,
    },
}


@router.post("/demo-login", response_model=TokenPair, summary="One-click demo persona session")
async def demo_login(
    payload: DemoLoginRequest,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> TokenPair:
    """Create a temporary restricted demo session for the selected persona."""
    key = payload.role.strip().lower()
    persona = DEMO_PERSONA_CATALOG.get(key)
    if not persona:
        # Fallback to student persona if unknown
        persona = DEMO_PERSONA_CATALOG["student"]

    users = UserRepository(db["users"], db["api_keys"], db["revoked_credentials"])
    audit = AuditRepository(db["audit_events"])

    user = await users.by_email(persona["email"])
    if user is None:
        # Create ephemeral demo user if not yet seeded
        demo_user_id = f"DEMO-{key.upper()}-01"
        user_doc = {
            "user_id": demo_user_id,
            "email": persona["email"],
            "full_name": persona["full_name"],
            "role": persona["role"],
            "institution_id": persona.get("institution_id"),
            "apaar_id": persona.get("apaar_id"),
            "is_active": True,
            "is_demo": True,
        }
        await db["users"].replace_one({"user_id": demo_user_id}, user_doc, upsert=True)
        user = user_doc

    await writer.log(
        audit,
        actor=user["user_id"],
        actor_role=user["role"],
        action="DEMO_LOGIN",
        subject=user["user_id"],
        details=f"Demo visitor selected persona '{key}' ({persona['full_name']}).",
        category="DEMO",
        ip_address=client_ip(request),
    )

    extra = {
        "is_demo": True,
        "apaar_id": user.get("apaar_id"),
    }
    return TokenPair(
        access_token=create_access_token(
            subject=user["user_id"],
            role=user["role"],
            institution_id=user.get("institution_id"),
            extra_claims=extra,
        ),
        refresh_token=create_refresh_token(user["user_id"]),
        expires_in=settings.access_token_expire_minutes * 60,
        role=user["role"],
        user_id=user["user_id"],
        display_name=user.get("full_name") or persona["full_name"],
        institution_id=user.get("institution_id"),
        apaar_id=user.get("apaar_id"),
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

    extra = {"apaar_id": user["apaar_id"]} if user.get("apaar_id") else None
    return TokenPair(
        access_token=create_access_token(
            subject=user["user_id"],
            role=user["role"],
            institution_id=user.get("institution_id"),
            extra_claims=extra,
        ),
        refresh_token=create_refresh_token(user["user_id"]),
        expires_in=settings.access_token_expire_minutes * 60,
        role=user["role"],
        user_id=user["user_id"],
        display_name=user.get("full_name") or user.get("email", ""),
        institution_id=user.get("institution_id"),
        apaar_id=user.get("apaar_id"),
    )


DEMO_PERSONA_CATALOG = {
    "student": {
        "email": "student.demo@example.com",
        "full_name": "Aarav Sharma (Student)",
        "role": "student",
        "apaar_id": "992100000001",
        "institution_id": "INST-0421",
    },
    "parent": {
        "email": "parent.demo@example.com",
        "full_name": "Sunita Sharma (Parent/Guardian)",
        "role": "parent",
        "apaar_id": "992100000001",
        "institution_id": "INST-0421",
    },
    "teacher": {
        "email": "teacher.demo@example.com",
        "full_name": "Prof. Rajesh Kumar (Faculty)",
        "role": "teacher",
        "institution_id": "INST-0421",
    },
    "school_admin": {
        "email": "schooladmin.demo@example.com",
        "full_name": "Principal Meera Nair (School Administrator)",
        "role": "institution_admin",
        "institution_id": "SCH-DEL-001",
    },
    "college_admin": {
        "email": "collegeadmin.demo@example.com",
        "full_name": "Director Ramesh Kulkarni (College Administrator)",
        "role": "institution_admin",
        "institution_id": "INST-0421",
    },
    "university_admin": {
        "email": "universityadmin.demo@example.com",
        "full_name": "Dr. Ananya Iyer (University Administrator)",
        "role": "aicte_admin",
        "institution_id": None,
    },
}


@router.post("/demo-login", response_model=TokenPair, summary="One-click demo persona session")
async def demo_login(
    payload: DemoLoginRequest,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> TokenPair:
    """Create a temporary restricted demo session for the selected persona."""
    key = payload.role.strip().lower()
    persona = DEMO_PERSONA_CATALOG.get(key)
    if not persona:
        # Fallback to student persona if unknown
        persona = DEMO_PERSONA_CATALOG["student"]

    users = UserRepository(db["users"], db["api_keys"], db["revoked_credentials"])
    audit = AuditRepository(db["audit_events"])

    user = await users.by_email(persona["email"])
    if user is None:
        # Create ephemeral demo user if not yet seeded
        demo_user_id = f"DEMO-{key.upper()}-01"
        user_doc = {
            "user_id": demo_user_id,
            "email": persona["email"],
            "full_name": persona["full_name"],
            "role": persona["role"],
            "institution_id": persona.get("institution_id"),
            "apaar_id": persona.get("apaar_id"),
            "is_active": True,
            "is_demo": True,
        }
        await db["users"].replace_one({"user_id": demo_user_id}, user_doc, upsert=True)
        user = user_doc

    await writer.log(
        audit,
        actor=user["user_id"],
        actor_role=user["role"],
        action="DEMO_LOGIN",
        subject=user["user_id"],
        details=f"Demo visitor selected persona '{key}' ({persona['full_name']}).",
        category="DEMO",
        ip_address=client_ip(request),
    )

    extra = {
        "is_demo": True,
        "apaar_id": user.get("apaar_id"),
    }
    return TokenPair(
        access_token=create_access_token(
            subject=user["user_id"],
            role=user["role"],
            institution_id=user.get("institution_id"),
            extra_claims=extra,
        ),
        refresh_token=create_refresh_token(user["user_id"]),
        expires_in=settings.access_token_expire_minutes * 60,
        role=user["role"],
        user_id=user["user_id"],
        display_name=user.get("full_name") or persona["full_name"],
        institution_id=user.get("institution_id"),
        apaar_id=user.get("apaar_id"),
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
        apaar_id=principal.apaar_id or user.get("apaar_id"),
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


# --------------------------------------------------------- Google sign-in


@router.get("/google/config", summary="Whether Google sign-in is available")
async def google_config() -> dict:
    """Tell the portal whether the Google button should be shown."""
    return {
        "enabled": settings.google_enabled,
        "login_url": f"{settings.api_prefix}/auth/google",
        "default_role": settings.google_default_role,
    }


@router.get("/google", summary="Start the Google sign-in")
async def google_start(request: Request):
    """Redirect the browser to Google's consent screen.

    A random ``state`` is put in a short-lived, HttpOnly cookie and compared
    with the one that comes back, so a third party cannot feed the callback a
    code of their own.
    """
    if not settings.google_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Google sign-in is not configured. Set GOOGLE_CLIENT_ID and "
                "GOOGLE_CLIENT_SECRET."
            ),
        )

    state = google.new_state()
    redirect_uri = _google_redirect_uri(request)
    url = google.authorisation_url(redirect_uri=redirect_uri, state=state)
    response = RedirectResponse(url=url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    response.set_cookie(
        google.STATE_COOKIE,
        state,
        max_age=google.STATE_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
        path="/",
    )
    return response


@router.get("/google/callback", summary="Finish the Google sign-in")
async def google_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Exchange the code, issue the tokens and return the browser to the portal."""
    if error:
        return _google_failure(request, f"Google refused the sign-in: {error}")
    if not code:
        return _google_failure(request, "Google did not return an authorisation code.")

    expected_state = request.cookies.get(google.STATE_COOKIE)
    if not expected_state or not state or state != expected_state:
        return _google_failure(
            request, "The sign-in could not be verified. Please try again."
        )

    redirect_uri = _google_redirect_uri(request)
    try:
        tokens = await google.exchange_code(code, redirect_uri=redirect_uri)
        access_token = tokens.get("access_token", "")
        if not access_token:
            raise google.GoogleAuthError("Google did not return an access token.")
        profile = await google.fetch_profile(access_token)
        account, created = await google.resolve_account(db, profile)
    except google.GoogleAuthError as exc:
        return _google_failure(request, str(exc))

    if not account.get("is_active", True):
        return _google_failure(request, "That account is not active.")

    await users_repo_set_last_login(db, account["user_id"])

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=account["user_id"],
        actor_role=account.get("role", ""),
        action="GOOGLE_LOGIN",
        subject=account["user_id"],
        details=(
            f"Signed in with Google ({'new account' if created else 'linked account'})."
        ),
        category="SECURITY",
        ip_address=client_ip(request),
    )

    access = create_access_token(
        subject=account["user_id"],
        role=account.get("role", "pending"),
        institution_id=account.get("institution_id"),
    )
    refresh = create_refresh_token(account["user_id"])

    fragment = urlencode(
        {"access_token": access, "refresh_token": refresh, "role": account.get("role", "")}
    )
    response = RedirectResponse(
        url=f"{settings.frontend_origin.rstrip('/')}/auth/callback#{fragment}",
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )
    response.set_cookie(
        google.STATE_COOKIE,
        "",
        max_age=0,
        expires=0,
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
        path="/",
    )
    return response


def _google_redirect_uri(request: Request) -> str:
    """The redirect URI registered with Google."""
    if settings.google_redirect_uri.strip():
        return settings.google_redirect_uri.strip()
    return f"{str(request.base_url).rstrip('/')}{settings.api_prefix}/auth/google/callback"


def _google_failure(request: Request, message: str) -> RedirectResponse:
    """Return the browser to the portal with an explanation."""
    logger.warning("Google sign-in failed: %s", message)
    fragment = urlencode({"error": message})
    response = RedirectResponse(
        url=f"{settings.frontend_origin.rstrip('/')}/login#{fragment}",
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )
    response.set_cookie(
        google.STATE_COOKIE,
        "",
        max_age=0,
        expires=0,
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
        path="/",
    )
    return response


async def users_repo_set_last_login(db, user_id: str) -> None:
    """Record the sign-in time."""
    await db["users"].update_one(
        {"user_id": user_id}, {"$set": {"last_login_at": datetime.now(timezone.utc)}}
    )
