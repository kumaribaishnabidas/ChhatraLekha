"""Verification token schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TokenIssueRequest(BaseModel):
    """The body used to issue a verification token."""

    student_record_id: str = Field(..., max_length=64)
    minutes: Optional[int] = Field(None, ge=1, le=60 * 24 * 7)
    reason: str = Field("", max_length=240)


class TokenIssueResponse(BaseModel):
    """The issued token.

    The plaintext is returned exactly once. Only its hash is stored.
    """

    token_id: str
    token: str
    token_url: str
    student_record_id: str
    issued_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    expires_in_minutes: int = 60
    notice: str = (
        "Verification against this prototype's database, not official APAAR or "
        "AICTE verification."
    )


class TokenOut(BaseModel):
    """A stored token, without the secret."""

    model_config = ConfigDict(from_attributes=True)

    token_id: str
    student_record_id: str = ""
    issued_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    revoked: bool = False
    needs_reissue: bool = False
    issued_by: str = ""
    allowed_fields: Optional[list[str]] = None


class PublicVerificationOut(BaseModel):
    """The allowlisted answer of the public verification endpoint.

    This is the only shape a stranger can obtain. It never contains the APAAR
    ID, the date of birth, contact details, notes or the underlying document.
    """

    valid: bool = False
    verdict: str = ""
    reason: str = ""
    record_status: str = ""
    institution: str = ""
    programme: str = ""
    academic_year: str = ""
    issued_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    needs_refresh: bool = False
    notice: str = (
        "Verification against this prototype's database, not official APAAR or AICTE "
        "verification."
    )
