"""Shared API dependencies: authentication, authorisation and rate limiting."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import rbac
from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import decode_token, hash_api_key
from app.models import ApiKey, User

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
    window.append(now)


# ------------------------------------------------------------ authentication


class Principal:
    """The authenticated caller."""

    def __init__(
        self,
        subject: str,
        role: str,
        institution_id: Optional[str] = None,
        display_name: str = "",
        user: Optional[User] = None,
    ) -> None:
        self.subject = subject
        self.role = role
        self.institution_id = institution_id
        self.display_name = display_name
        self.user = user

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
        if self.role == "aicte_admin":
            return
        if self.institution_id and self.institution_id == institution_id:
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access another institution's records.",
        )


async def _principal_from_api_key(
    raw_key: str, session: AsyncSession
) -> Optional[Principal]:
    digest = hash_api_key(raw_key)
    result = await session.execute(
        select(ApiKey).where(ApiKey.key_hash == digest, ApiKey.is_active.is_(True))
    )
    api_key = result.scalar_one_or_none()
    if api_key is None:
        return None
    return Principal(
        subject=api_key.key_id,
        role=api_key.role,
        institution_id=api_key.institution_id,
        display_name=api_key.label or api_key.key_id,
    )


async def get_principal(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db),
) -> Principal:
    """Resolve the caller from a bearer token or an ``X-API-Key`` header."""
    api_key_header = request.headers.get("X-API-Key")
    if api_key_header:
        principal = await _principal_from_api_key(api_key_header, session)
        if principal is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key.",
                headers={"WWW-Authenticate": "ApiKey"},
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

    subject = payload.get("sub") or ""
    result = await session.execute(select(User).where(User.user_id == subject))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="The account is not active."
        )

    principal = Principal(
        subject=user.user_id,
        role=user.role,
        institution_id=user.institution_id,
        display_name=user.full_name or user.email,
        user=user,
    )
    request.state.principal = principal
    return principal


def require_permission(permission: rbac.Permission):
    """A dependency that enforces a single permission."""

    async def _dependency(
        principal: Principal = Depends(get_principal),
    ) -> Principal:
        principal.require(permission)
        return principal

    return _dependency


def require_any_permission(*permissions: rbac.Permission):
    """A dependency that enforces at least one of several permissions."""

    async def _dependency(
        principal: Principal = Depends(get_principal),
    ) -> Principal:
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
    """The caller's IP address, honouring a reverse proxy header."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None
