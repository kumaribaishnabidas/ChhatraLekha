"""Authentication endpoints: login, refresh, logout and the current user."""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlencode

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import (
    Principal,
    client_ip,
    client_user_agent,
    enforce_rate_limit,
    get_db,
    get_principal,
    get_session_repo,
)
from app.audit import writer
from app.core.config import get_settings
from app.core.security import (
    ROLE_INSTITUTION,
    ROLE_PENDING,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_refresh_token,
    password_policy_violations,
    verify_password,
)
from app.repositories.audit import AuditRepository
from app.repositories.sessions import SessionRepository
from app.repositories.users import UserRepository
from app.schemas.auth import (
    DemoLoginRequest,
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    TokenPair,
    UserOut,
)
from app.services import google

logger = logging.getLogger("chhatralekha.auth")

router = APIRouter(prefix="/auth", tags=["authentication"])

settings = get_settings()

SELF_SERVICE_ROLES = {"student", "parent", "teacher"}
INSTITUTION_ADMIN_ROLES = {"institution_admin", "school_admin", "college_admin"}
RESTRICTED_ROLES = {
    "national_admin",
    "platform_operator",
    "aicte_admin",
    "university_admin",
    "state_admin",
    "district_admin",
    "regulator_admin",
    "academic_admin",
    "verifier",
}


async def _issue_and_persist_refresh_token(
    sessions: SessionRepository,
    user_id: str,
    request: Optional[Request] = None,
    session_id: Optional[str] = None,
    family_id: Optional[str] = None,
) -> str:
    """Issue a signed refresh token with a unique jti and persist its cryptographic hash."""
    jti = secrets.token_urlsafe(32)
    effective_family = family_id or f"fam_{secrets.token_urlsafe(24)}"
    token = create_refresh_token(subject=user_id, jti=jti, family_id=effective_family)
    token_hash = hash_refresh_token(token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)

    await sessions.create_session(
        user_id=user_id,
        jti=jti,
        token_hash=token_hash,
        expires_at=expires_at,
        session_id=session_id,
        family_id=effective_family,
        ip_address=client_ip(request) if request else None,
        user_agent=client_user_agent(request) if request else None,
    )
    return token


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Self-service user registration",
    dependencies=[Depends(enforce_rate_limit)],
)
async def register(
    payload: RegisterRequest,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> RegisterResponse:
    """Register a new user account with secure password hashing and role validation."""
    requested_role = payload.role.strip().lower()

    if requested_role in RESTRICTED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Registration for role '{requested_role}' is restricted and requires administrator invitation.",
        )

    if requested_role not in SELF_SERVICE_ROLES and requested_role not in INSTITUTION_ADMIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid registration role '{requested_role}'. Allowed roles are student, parent, teacher, or institution_admin.",
        )

    violations = password_policy_violations(payload.password)
    if violations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=" ".join(violations),
        )

    users = UserRepository(db["users"], db["api_keys"], db["revoked_credentials"])
    audit = AuditRepository(db["audit_events"])

    normalized_email = payload.email.strip().lower()
    existing_user = await users.by_email(normalized_email)
    if existing_user is not None:
        await writer.log(
            audit,
            actor=normalized_email,
            action="REGISTER_DUPLICATE_ATTEMPT",
            subject=normalized_email,
            details="Registration attempted with existing email address.",
            category="SECURITY",
            ip_address=client_ip(request),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to complete registration. If an account already exists with this email, please sign in or reset your password.",
        )

    user_id = f"usr_{secrets.token_hex(8)}"
    hashed_pw = hash_password(payload.password)
    now = datetime.now(timezone.utc)

    is_admin_request = requested_role in INSTITUTION_ADMIN_ROLES
    effective_role = ROLE_PENDING if is_admin_request else requested_role

    user_doc = {
        "user_id": user_id,
        "email": normalized_email,
        "full_name": payload.full_name.strip(),
        "password_hash": hashed_pw,
        "role": effective_role,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
        "institution_id": None,
    }

    if payload.identifier and requested_role == "student":
        ident = payload.identifier.strip()
        if ident.isdigit() and len(ident) == 12:
            user_doc["apaar_id"] = ident

    await db["users"].insert_one(user_doc)

    if is_admin_request:
        req_id = f"req-{secrets.token_hex(6)}"
        req_doc = {
            "_id": req_id,
            "request_id": req_id,
            "user_id": user_id,
            "user_name": payload.full_name.strip(),
            "user_email": normalized_email,
            "institution_id": None,
            "institution_name": payload.identifier.strip() if payload.identifier else None,
            "requested_role": ROLE_INSTITUTION,
            "role_details": {"institution_name": payload.identifier.strip()} if payload.identifier else {},
            "status": "PENDING",
            "created_at": now,
        }
        await db["membership_requests"].insert_one(req_doc)

        await writer.log(
            audit,
            actor=user_id,
            actor_role=ROLE_PENDING,
            action="REGISTER_INSTITUTION_ADMIN_PENDING",
            subject=user_id,
            details=f"User registered with email '{normalized_email}' requesting institution admin access (pending approval).",
            category="SECURITY",
            ip_address=client_ip(request),
        )

        return RegisterResponse(
            status="success",
            message="Registration successful. Institutional administrator access requires review before administrative privileges are granted.",
            user_id=user_id,
            email=normalized_email,
            role=ROLE_PENDING,
            requires_approval=True,
        )

    await writer.log(
        audit,
        actor=user_id,
        actor_role=effective_role,
        action="REGISTER",
        subject=user_id,
        details=f"User registered with email '{normalized_email}' as '{effective_role}'.",
        category="SECURITY",
        ip_address=client_ip(request),
    )

    return RegisterResponse(
        status="success",
        message="Account created successfully! You may now sign in.",
        user_id=user_id,
        email=normalized_email,
        role=effective_role,
        requires_approval=False,
    )


@router.post("/login", response_model=TokenPair, summary="Sign in and receive a JWT pair")
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db),
    sessions: SessionRepository = Depends(get_session_repo),
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

    refresh_token = await _issue_and_persist_refresh_token(
        sessions, user["user_id"], request=request
    )
    extra = {"apaar_id": user["apaar_id"]} if user.get("apaar_id") else None
    return TokenPair(
        access_token=create_access_token(
            subject=user["user_id"],
            role=user["role"],
            institution_id=user.get("institution_id"),
            extra_claims=extra,
        ),
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
        role=user["role"],
        user_id=user["user_id"],
        display_name=user.get("full_name") or user.get("email", ""),
        institution_id=user.get("institution_id"),
        apaar_id=user.get("apaar_id"),
    )


@router.post("/refresh", response_model=TokenPair, summary="Exchange a refresh token")
async def refresh(
    payload: RefreshRequest,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db),
    sessions: SessionRepository = Depends(get_session_repo),
) -> TokenPair:
    """Issue a new access token and rotated refresh token from a valid refresh token."""
    try:
        claims = decode_token(payload.refresh_token, expected_type="refresh")
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired refresh token: {exc}",
        ) from exc

    presented_hash = hash_refresh_token(payload.refresh_token)
    session = await sessions.by_token_hash(presented_hash)
    if session is None and claims.get("jti"):
        session = await sessions.by_jti(claims["jti"])

    users = UserRepository(db["users"], db["api_keys"], db["revoked_credentials"])
    audit = AuditRepository(db["audit_events"])

    # If session not found in database:
    if session is None:
        if claims.get("jti") is None:
            # Safe compatibility path for pre-existing legacy tokens without a jti
            user = await users.by_user_id(claims.get("sub") or "")
            if user is None or not user.get("is_active", True):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="The account is not active."
                )
            new_refresh = await _issue_and_persist_refresh_token(
                sessions, user["user_id"], request=request
            )
            extra = {"apaar_id": user["apaar_id"]} if user.get("apaar_id") else None
            return TokenPair(
                access_token=create_access_token(
                    subject=user["user_id"],
                    role=user["role"],
                    institution_id=user.get("institution_id"),
                    extra_claims=extra,
                ),
                refresh_token=new_refresh,
                expires_in=settings.access_token_expire_minutes * 60,
                role=user["role"],
                user_id=user["user_id"],
                display_name=user.get("full_name") or user.get("email", ""),
                institution_id=user.get("institution_id"),
                apaar_id=user.get("apaar_id"),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or unknown refresh token identifier.",
            )

    # 1. Expiration validation
    now = datetime.now(timezone.utc)
    exp = session.get("expires_at")
    if exp:
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp <= now:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired.",
            )

    # 2. Revocation validation
    if session.get("is_revoked"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked.",
        )

    # 3. Reuse detection: if rotated_at is already set, this token was previously rotated!
    if session.get("rotated_at") is not None:
        family_id = session.get("family_id")
        if family_id:
            await sessions.revoke_family(family_id, reason="TOKEN_REUSE_DETECTED")
        await writer.log(
            audit,
            actor=session.get("user_id", "unknown"),
            action="REFRESH_TOKEN_REUSE_DETECTED",
            subject=session.get("user_id", "unknown"),
            details=f"Replay of rotated refresh token detected for jti '{session.get('jti')}'. Revoked token family '{family_id}'.",
            category="SECURITY",
            ip_address=client_ip(request),
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token reuse detected. Session has been revoked.",
        )

    # 4. User account status validation
    user = await users.by_user_id(session.get("user_id") or "")
    if user is None or not user.get("is_active", True):
        if session.get("family_id"):
            await sessions.revoke_family(session["family_id"], reason="USER_INACTIVE")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="The account is not active."
        )

    # 5. Atomic token rotation
    new_jti = secrets.token_urlsafe(32)
    new_refresh_token = create_refresh_token(
        subject=user["user_id"],
        jti=new_jti,
        family_id=session.get("family_id"),
    )
    new_token_hash = hash_refresh_token(new_refresh_token)
    new_expires_at = now + timedelta(days=settings.refresh_token_expire_days)

    rotated_ok, _ = await sessions.rotate_session(
        old_jti=session["jti"],
        new_jti=new_jti,
        new_token_hash=new_token_hash,
        new_expires_at=new_expires_at,
        ip_address=client_ip(request),
        user_agent=client_user_agent(request),
    )
    if not rotated_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token rotation conflict or concurrent refresh detected.",
        )

    extra = {"apaar_id": user["apaar_id"]} if user.get("apaar_id") else None
    return TokenPair(
        access_token=create_access_token(
            subject=user["user_id"],
            role=user["role"],
            institution_id=user.get("institution_id"),
            extra_claims=extra,
        ),
        refresh_token=new_refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
        role=user["role"],
        user_id=user["user_id"],
        display_name=user.get("full_name") or user.get("email", ""),
        institution_id=user.get("institution_id"),
        apaar_id=user.get("apaar_id"),
    )


@router.post("/logout", response_model=LogoutResponse, summary="Revoke active authentication session")
async def logout(
    request: Request,
    payload: Optional[LogoutRequest] = None,
    principal: Principal = Depends(get_principal),
    sessions: SessionRepository = Depends(get_session_repo),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> LogoutResponse:
    """Revoke the current session or all active sessions for the authenticated user.

    Repeated calls are safe and idempotent. Never logs token values.
    """
    revoked_count = 0
    if payload and payload.refresh_token:
        try:
            claims = decode_token(payload.refresh_token, expected_type="refresh")
            token_sub = claims.get("sub")
            if token_sub and token_sub != principal.subject:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You cannot revoke another user's session.",
                )
            token_hash = hash_refresh_token(payload.refresh_token)
            session = await sessions.by_token_hash(token_hash)
            if session:
                if session.get("user_id") != principal.subject:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You cannot revoke another user's session.",
                    )
                revoked_count = await sessions.revoke_session(session["session_id"], reason="LOGOUT")
            else:
                revoked_count = 0
        except jwt.PyJWTError:
            # Token was already expired or malformed; repeated logout remains safe
            revoked_count = 0
    elif payload and payload.all_sessions:
        revoked_count = await sessions.revoke_all_user_sessions(principal.subject, reason="ALL_SESSIONS_LOGOUT")
    else:
        # Default: revoke user's sessions / current device session
        revoked_count = await sessions.revoke_all_user_sessions(principal.subject, reason="LOGOUT")

    audit = AuditRepository(db["audit_events"])
    await writer.log(
        audit,
        actor=principal.subject,
        actor_role=principal.role,
        action="LOGOUT",
        subject=principal.subject,
        details=f"User {principal.subject} signed out.",
        category="SECURITY",
        ip_address=client_ip(request),
    )

    return LogoutResponse(
        status="success",
        message="Logged out successfully.",
        revoked_sessions_count=revoked_count,
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


DISALLOWED_DEMO_ROLES = {
    "national_admin",
    "platform_operator",
    "state_admin",
    "district_admin",
    "regulator_admin",
}


@router.post("/demo-login", response_model=TokenPair, summary="One-click demo persona session")
async def demo_login(
    payload: DemoLoginRequest,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db),
    sessions: SessionRepository = Depends(get_session_repo),
) -> TokenPair:
    """Create a temporary restricted demo session for the selected persona.

    Disabled in production environments to fail closed and prevent unauthorized
    administrative access.
    """
    runtime_settings = get_settings()
    if runtime_settings.is_production:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo login is disabled in production environments.",
        )

    key = payload.role.strip().lower()
    if key in DISALLOWED_DEMO_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role escalation to administrative role '{key}' is forbidden.",
        )

    persona = DEMO_PERSONA_CATALOG.get(key)
    if not persona:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid demo role '{payload.role}'. Allowed demo personas: {', '.join(sorted(DEMO_PERSONA_CATALOG.keys()))}.",
        )

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

    # Ensure demo student has their own linked record in students collection
    if persona.get("apaar_id") and persona.get("role") == "student":
        existing_student = await db["students"].find_one({"apaar_id": persona["apaar_id"]})
        if not existing_student:
            await db["students"].insert_one({
                "apaar_id": persona["apaar_id"],
                "student_name": persona["full_name"],
                "institution_id": persona.get("institution_id", "INST-0421"),
                "student_institute_roll_no": "D-2024-001",
                "academic_year": "2024-25",
                "current_semester": "Semester 5",
                "attendance_percentage": 92.4,
                "cumulative_cgpa": 8.75,
                "guardian_name": "Sunita Sharma",
                "guardian_relationship": "Mother / Legal Guardian",
                "guardian_phone_masked": "+91 98**** **12",
                "verified_credentials_count": 3,
                "achievements": [
                    "First Class with Distinction (Semesters 1-4)",
                    "Dean's Honour Roll - Academic Year 2023-24",
                    "Winner, State Inter-College Hackathon 2024",
                ],
                "is_demo": True,
            })

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
    refresh_token = await _issue_and_persist_refresh_token(
        sessions, user["user_id"], request=request
    )
    return TokenPair(
        access_token=create_access_token(
            subject=user["user_id"],
            role=user["role"],
            institution_id=user.get("institution_id"),
            extra_claims=extra,
        ),
        refresh_token=refresh_token,
        expires_in=runtime_settings.access_token_expire_minutes * 60,
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
    sessions = SessionRepository(db["refresh_sessions"])
    refresh = await _issue_and_persist_refresh_token(
        sessions, account["user_id"], request=request
    )

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
