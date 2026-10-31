"""Anomaly schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

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


class AnomalySummary(BaseModel):
    """A severity roll-up of the anomaly register."""

    total: int = 0
    critical: int = 0
    high: int = 0
    warning: int = 0
    info: int = 0
    by_type: dict[str, int] = {}
    by_institution: dict[str, int] = {}
