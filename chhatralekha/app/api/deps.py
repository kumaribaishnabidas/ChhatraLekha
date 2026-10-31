"""Shared API dependencies: authentication, authorisation and rate limiting."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Any, Optional

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.audit import writer
from app.core import rbac
from app.core.config import get_settings
from app.core.database import mongo
from app.core.security import decode_token, hash_api_key
from app.repositories.anomalies import AnomalyRepository
from app.repositories.audit import AuditRepository
from app.repositories.consents import ConsentRepository
from app.repositories.institutions import InstitutionRepository
from app.repositories.programmes import ProgrammeRepository
from app.repositories.students import StudentRepository
from app.repositories.submissions import SubmissionRepository
from app.repositories.users import UserRepository

settings = get_settings()

bearer_scheme = HTTPBearer(auto_error=False)


# ------------------------------------------------------------- rate limiting

_hits: dict[str, deque[float]] = defaultdict(deque)


def enforce_rate_limit(request: Request) -> None:
    """A simple in-process sliding-window rate limiter."""
    if settings.rate_limit_per_minute <= 0:
        return
    client = request.client.host if request.client else "unknown"
    now = time.monotonic()
    window = _hits[client]
    while window and now - window[0] > 60:
        window.popleft()
    if len(window) >= settings.rate_limit_per_minute:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please slow down.",
        )


# --------------------------------------------------------------- collections


async def get_db() -> AsyncIOMotorDatabase:
    """The MongoDB database handle."""
    if not mongo.is_connected:
        await mongo.connect()
    return mongo.db()


def get_institution_repo(db: AsyncIOMotorDatabase = Depends(get_db)) -> InstitutionRepository:
    return InstitutionRepository(db["institutions"])


def get_programme_repo(db: AsyncIOMotorDatabase = Depends(get_db)) -> ProgrammeRepository:
    return ProgrammeRepository(db["programmes"])


def get_student_repo(db: AsyncIOMotorDatabase = Depends(get_db)) -> StudentRepository:
    return StudentRepository(db["students"])


def get_anomaly_repo(db: AsyncIOMotorDatabase = Depends(get_db)) -> AnomalyRepository:
    return AnomalyRepository(db["anomalies"])


def get_consent_repo(db: AsyncIOMotorDatabase = Depends(get_db)) -> ConsentRepository:
    return ConsentRepository(db["consents"])


def get_user_repo(db: AsyncIOMotorDatabase = Depends(get_db)) -> UserRepository:
    return UserRepository(db["users"], db["api_keys"], db["revoked_credentials"])


def get_audit_repo(db: AsyncIOMotorDatabase = Depends(get_db)) -> AuditRepository:
    return AuditRepository(db["audit_events"])


def get_submission_repo(db: AsyncIOMotorDatabase = Depends(get_db)) -> SubmissionRepository:
    return SubmissionRepository(db["submissions"])


# ------------------------------------------------------------ authentication


class Principal:
    """The authenticated caller."""

    def __init__(
        self,
        subject: str,
        role: str,
        institution_id: Optional[str] = None,
        display_name: str = "",
        email: str = "",
        user: Optional[Any] = None,
        apaar_id: Optional[str] = None,
    ) -> None:
        self.subject = subject
        self.role = role
        self.institution_id = institution_id
        self.display_name = display_name
        self.email = email
        self.user = user
        self.apaar_id = apaar_id or (user.get("apaar_id") if isinstance(user, dict) else None)
        self.state = user.get("state") if isinstance(user, dict) else None
        self.district = user.get("district") if isinstance(user, dict) else None

    def require(self, permission: rbac.Permission) -> None:
        """Raise ``403`` when the principal lacks the permission."""
        if not rbac.has_permission(self.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Role '{self.role}' is not allowed to perform this action. "
                    f"Required permission: {permission.value}."
                ),
            )

    def require_scope(self, institution_id: str) -> None:
        """Raise ``403`` when the principal may not touch that institution."""
        if self.role in {"national_admin", "aicte_admin", "platform_operator", "regulator_admin", "state_admin", "district_admin"}:
            return
        if self.institution_id and self.institution_id == institution_id:
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access another institution's records.",
        )


async def ensure_can_access_student(
    principal: Principal,
    student: dict,
    *,
    db: Optional[AsyncIOMotorDatabase] = None,
    request: Optional[Request] = None,
    detail: str = "You are not allowed to access another institution's records.",
) -> None:
    """Allow the owner student, same-institution staff, or authorized administrators.

    Rejects students accessing another student's record, cross-institution staff
    access, and roles without direct student record access (such as verifier or pending).
    Writes an audit entry on access denial.
    """
    if principal.role == "student":
        own = principal.apaar_id or (principal.user or {}).get("apaar_id")
        if not own or own != student.get("apaar_id"):
            if db is not None:
                await writer.log(
                    AuditRepository(db["audit_events"]),
                    actor=principal.subject,
                    actor_role=principal.role,
                    action="ACCESS_DENIED",
                    subject=student.get("apaar_id", ""),
                    details=f"Student attempted unauthorized access to record of {student.get('apaar_id')}.",
                    category="SECURITY",
                    ip_address=client_ip(request) if request else None,
                )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You may only access your own record.",
            )
        return

    if principal.role in {
        "national_admin",
        "aicte_admin",
        "platform_operator",
        "regulator_admin",
        "state_admin",
        "district_admin",
    }:
        return

    if principal.role in {"institution_admin", "academic_admin", "teacher"}:
        if not principal.institution_id or student.get("institution_id") != principal.institution_id:
            if db is not None:
                await writer.log(
                    AuditRepository(db["audit_events"]),
                    actor=principal.subject,
                    actor_role=principal.role,
                    action="ACCESS_DENIED",
                    subject=student.get("apaar_id", ""),
                    details=detail,
                    category="SECURITY",
                    ip_address=client_ip(request) if request else None,
                )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=detail,
            )
        return

    if principal.role == "parent":
        ward_apaar = (principal.user or {}).get("ward_apaar_id") or (principal.user or {}).get("apaar_id")
        if ward_apaar and ward_apaar == student.get("apaar_id"):
            return
        if db is not None:
            await writer.log(
                AuditRepository(db["audit_events"]),
                actor=principal.subject,
                actor_role=principal.role,
                action="ACCESS_DENIED",
                subject=student.get("apaar_id", ""),
                details=f"Parent attempted unauthorized access to record of {student.get('apaar_id')}.",
                category="SECURITY",
                ip_address=client_ip(request) if request else None,
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You may only access your linked ward's record.",
        )

    # Verifier, pending, and any other role: no direct record access
    if db is not None:
        await writer.log(
            AuditRepository(db["audit_events"]),
            actor=principal.subject,
            actor_role=principal.role,
            action="ACCESS_DENIED",
            subject=student.get("apaar_id", ""),
            details=f"Role '{principal.role}' attempted direct student record access.",
            category="SECURITY",
            ip_address=client_ip(request) if request else None,
        )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Your role may not read student records directly.",
    )


async def get_principal(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> Principal:
    """Resolve the caller from a bearer token or an ``X-API-Key`` header."""
    api_key_header = request.headers.get("X-API-Key")
    if api_key_header:
        repository = UserRepository(db["users"], db["api_keys"], db["revoked_credentials"])
        api_key = await repository.api_key_by_hash(hash_api_key(api_key_header))
        if api_key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key.",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        owner_user_id = api_key.get("user_id")
        if owner_user_id:
            user = await repository.by_user_id(owner_user_id)
            if user is None or not user.get("is_active", True):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="The API key owner account is not active.",
                    headers={"WWW-Authenticate": "ApiKey"},
                )

        principal = Principal(
            subject=api_key["key_id"],
            role=api_key.get("role", "institution_admin"),
            institution_id=api_key.get("institution_id"),
            display_name=api_key.get("label", api_key["key_id"]),
        )
        request.state.principal = principal
        return principal

    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(credentials.credentials, expected_type="access")
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    repository = UserRepository(db["users"], db["api_keys"], db["revoked_credentials"])
    user = await repository.by_user_id(payload.get("sub") or "")
    if user is None or not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="The account is not active."
        )

    principal = Principal(
        subject=user["user_id"],
        role=user["role"],
        institution_id=user.get("institution_id"),
        display_name=user.get("full_name") or user.get("email", ""),
        email=user.get("email", ""),
        user=user,
        apaar_id=user.get("apaar_id") or payload.get("apaar_id"),
    )
    request.state.principal = principal
    return principal


def require_permission(permission: rbac.Permission):
    """A dependency that enforces a single permission."""

    async def _dependency(principal: Principal = Depends(get_principal)) -> Principal:
        principal.require(permission)
        return principal

    return _dependency


def require_any_permission(*permissions: rbac.Permission):
    """A dependency that enforces at least one of several permissions."""

    async def _dependency(principal: Principal = Depends(get_principal)) -> Principal:
        if not rbac.has_any_permission(principal.role, permissions):
            names = ", ".join(permission.value for permission in permissions)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{principal.role}' is not allowed to perform this action. "
                f"Required one of: {names}.",
            )
        return principal

    return _dependency


def client_ip(request: Request) -> Optional[str]:
    """The caller's IP address.

    ``X-Forwarded-For`` is treated as untrusted unless the deployment explicitly
    enables it via ``TRUST_FORWARDED_HEADERS=true``. This prevents a client from
    spoofing its IP in audit logs or rate-limit decisions.
    """
    forwarded = request.headers.get("X-Forwarded-For") if settings.trust_forwarded_headers else None
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None
