"""Pydantic request/response schemas."""

from app.schemas.anomaly import AnomalyOut, AnomalySummary
from app.schemas.auth import LoginRequest, RefreshRequest, TokenPair, UserOut
from app.schemas.consent import ConsentDecisionOut, ConsentOut, ConsentRequest
from app.schemas.dashboard import (
    AuditEntryOut,
    ComplianceRow,
    IntakeRow,
    NationalKpis,
    QuotaDistributionRow,
    RiskScoreOut,
)
from app.schemas.student import (
    BatchUploadResult,
    InstitutionOut,
    ProgrammeIntakeIn,
    ProgrammeIntakeOut,
    StudentCreate,
    StudentIn,
    StudentOut,
    StudentUpdate,
    VerificationResult,
)

__all__ = [
    "AnomalyOut",
    "AnomalySummary",
    "AuditEntryOut",
    "BatchUploadResult",
    "ComplianceRow",
    "ConsentDecisionOut",
    "ConsentOut",
    "ConsentRequest",
    "InstitutionOut",
    "IntakeRow",
    "LoginRequest",
    "NationalKpis",
    "ProgrammeIntakeIn",
    "ProgrammeIntakeOut",
    "QuotaDistributionRow",
    "RefreshRequest",
    "RiskScoreOut",
    "StudentCreate",
    "StudentIn",
    "StudentOut",
    "StudentUpdate",
    "TokenPair",
    "UserOut",
    "VerificationResult",
]
