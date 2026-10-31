"""Anomaly schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AnomalySeverity, AnomalyType


class AnomalyOut(BaseModel):
    """A detected regulatory anomaly."""

    model_config = ConfigDict(from_attributes=True)

    anomaly_id: str = ""
    student_apaar_id: str
    institution_id: str
    program_id: str | None = None
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    details: str
    recommended_action: str = ""
    detected_at: datetime | None = None
    review_status: str = "PENDING"
    resolved: bool = False
    assigned_to: Optional[str] = None
    assigned_reviewer_name: Optional[str] = None
    case_notes: list[dict[str, Any]] = []
    dismissal_reason: Optional[str] = None
    ruleset_version: str = "2026.1"


class AnomalyAssignIn(BaseModel):
    """Payload to assign a reviewer to an anomaly case."""

    assignee_id: str = Field(..., min_length=1, max_length=64)
    assignee_name: str = Field(..., min_length=1, max_length=120)


class AnomalyNoteIn(BaseModel):
    """Payload to append a case note to an anomaly."""

    note_text: str = Field(..., min_length=1, max_length=1000)


class AnomalyReviewDecisionIn(BaseModel):
    """Payload to record a formal review or dismissal decision."""

    review_status: str = Field(..., pattern="^(PENDING|IN_REVIEW|RESOLVED|DISMISSED)$")
    reason: Optional[str] = Field(None, max_length=120)
    explanation: Optional[str] = Field(None, max_length=1000)


class AnomalySummary(BaseModel):
    """A severity roll-up of the anomaly register."""

    total: int = 0
    critical: int = 0
    high: int = 0
    warning: int = 0
    info: int = 0
    by_type: dict[str, int] = {}
    by_institution: dict[str, int] = {}
