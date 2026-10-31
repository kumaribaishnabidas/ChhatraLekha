"""Transfer workflow schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TransferRequestIn(BaseModel):
    """Payload to initiate a student transfer between institutions."""

    apaar_id: str = Field(..., min_length=1, max_length=32)
    to_institution_id: str = Field(..., min_length=1, max_length=32)
    to_program_id: str = Field(..., min_length=1, max_length=64)
    reason: str = Field(..., min_length=3, max_length=500)
    transfer_notes: Optional[str] = Field(None, max_length=1000)


class TransferReviewIn(BaseModel):
    """Payload to approve or reject a pending student transfer."""

    decision: str = Field(..., pattern="^(APPROVED|REJECTED)$")
    notes: str = Field("", max_length=500)


class TransferOut(BaseModel):
    """Transfer request representation."""

    transfer_id: str
    apaar_id: str
    student_name: str
    from_institution_id: str
    to_institution_id: str
    from_program_id: str
    to_program_id: str
    status: str
    reason: str
    review_notes: Optional[str] = None
    requested_at: Optional[datetime] = None
    requested_by: str
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None

