"""Authentication schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    """Credentials presented to ``POST /api/auth/login``."""

    email: str = Field(..., description="Registered e-mail address or user id.")
    password: str = Field(..., min_length=1, max_length=256)
    institution_id: str | None = None


class RefreshRequest(BaseModel):
    """A refresh token presented to ``POST /api/auth/refresh``."""

    refresh_token: str


class TokenPair(BaseModel):
    """The issued token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    role: str
    user_id: str
    display_name: str
    institution_id: str | None = None
    apaar_id: str | None = None


class UserOut(BaseModel):
    """A signed-in principal."""

    model_config = ConfigDict(from_attributes=True)

    user_id: str
    email: str
    full_name: str
    role: str
    institution_id: str | None = None
    apaar_id: str | None = None
    is_active: bool = True
    last_login_at: str | None = None
