"""Consent schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import ConsentChannel, ConsentPurpose, ConsentStatus


class ConsentRequest(BaseModel):
    """The body used to grant or revoke a consent."""

    apaar_id: str
    purpose: ConsentPurpose
    status: ConsentStatus = ConsentStatus.GRANTED
    channel: ConsentChannel = ConsentChannel.WEB_PORTAL
    policy_version: str = "2024-01"
    evidence: str | None = None


class ConsentOut(BaseModel):
    """One consent record."""

    model_config = ConfigDict(from_attributes=True)

    consent_id: str
    student_apaar_id: str
    purpose: ConsentPurpose
    status: ConsentStatus
    channel: ConsentChannel
    policy_version: str
    recorded_at: datetime
    revoked_at: datetime | None = None
    evidence: str | None = None
    granted_by: str = ""


class ConsentDecisionOut(BaseModel):
    """The effective consent state for one purpose."""

    purpose: ConsentPurpose
    purpose_label: str
    status: ConsentStatus
    allowed: bool
    reason: str
    recorded_at: datetime | None = None
