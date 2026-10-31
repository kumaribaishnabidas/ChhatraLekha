"""Dashboard and reporting schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AdmissionQuota


class NationalKpis(BaseModel):
    """Pan-India headline numbers."""

    institution_count: int = 0
    programme_count: int = 0
    total_approved_intake: int = 0
    total_enrolled: int = 0
    flagged_anomalies: int = 0
    critical_anomalies: int = 0
    supernumerary_enrolled: int = 0
    utilisation_percent: float = 0.0


class IntakeRow(BaseModel):
    """One row of the live intake-utilisation matrix."""

    institution_id: str
    institution_name: str = ""
    program_id: str
    program_name: str
    program_level: str = "UG"
    approved_intake: int = 0
    regular_enrolled: int = 0
    supernumerary_enrolled: int = 0
    total_enrolled: int = 0
    total_sanctioned: int = 0
    nri_enrolled: int = 0
    oci_fn_enrolled: int = 0
    tfw_enrolled: int = 0
    pmsss_enrolled: int = 0
    utilisation_percent: float = 0.0
    has_breach: bool = False


class QuotaDistributionRow(BaseModel):
    """Aggregate quota distribution across the country."""

    label: str
    quota: AdmissionQuota | None = None
    enrolled: int = 0
    sanctioned: int = 0
    utilisation: float = 0.0


class RiskScoreOut(BaseModel):
    """The risk assessment of one institution."""

    institution_id: str
    score: float
    band: str
    critical_count: int
    high_count: int
    warning_count: int
    families: list[str] = []
    reasons: list[str] = []


class ComplianceRow(BaseModel):
    """One institution's compliance status."""

    institution_id: str
    institution_name: str = ""
    state: str = ""
    total_approved: int = 0
    total_enrolled: int = 0
    utilisation: float = 0.0
    breaches: int = 0
    risk_band: str = "LOW"
    risk_score: float = 0.0


class AuditEntryOut(BaseModel):
    """One audit-trail entry."""

    model_config = ConfigDict(from_attributes=True)

    log_id: int
    timestamp: datetime
    actor: str
    actor_role: str = ""
    action: str
    subject: str = ""
    details: str = ""
    category: str = "SYSTEM"
    prev_hash: str = ""
    hash: str = ""
