"""Institution risk scoring (the innovation layer).

Every institution receives a 0-100 risk score derived from the severity and
the diversity of the anomalies detected against it. The score is deliberately
explainable: each contributing anomaly carries a weight, and the breakdown is
returned alongside the score so the inspector can see *why* an institution
was flagged.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from app.models.enums import AnomalySeverity

#: Weight of each anomaly severity in the risk score.
SEVERITY_WEIGHT = {
    AnomalySeverity.CRITICAL: 12.0,
    AnomalySeverity.HIGH: 6.0,
    AnomalySeverity.WARNING: 2.0,
    AnomalySeverity.INFO: 0.5,
}

#: Additional weight when several *different* anomaly families fire.
DIVERSITY_BONUS_PER_EXTRA_FAMILY = 3.0

#: The score is capped at 100.
MAX_SCORE = 100.0


@dataclass
class InstitutionRisk:
    """The risk assessment of one institution."""

    institution_id: str
    score: float = 0.0
    band: str = "LOW"
    critical_count: int = 0
    high_count: int = 0
    warning_count: int = 0
    families: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)

    @property
    def is_high_risk(self) -> bool:
        return self.band in {"HIGH", "CRITICAL"}


def _band(score: float) -> str:
    if score >= 75:
        return "CRITICAL"
    if score >= 50:
        return "HIGH"
    if score >= 25:
        return "MEDIUM"
    return "LOW"


def score_institution(institution_id: str, anomalies) -> InstitutionRisk:
    """Score one institution from its anomalies."""
    counts: dict[str, int] = defaultdict(int)
    for anomaly in anomalies:
        counts[getattr(anomaly.anomaly_type, "value", anomaly.anomaly_type)] += 1

    critical = counts.get("EXCESS_APPROVED_INTAKE", 0) + counts.get("UNSANCTIONED_PROGRAM", 0)
    high = (
        counts.get("DUPLICATE_CROSS_COLLEGE", 0)
        + counts.get("DUPLICATE_SAME_INSTITUTION", 0)
        + counts.get("DUPLICATE_ROLL_NUMBER", 0)
        + counts.get("INVALID_APAAR_FORMAT", 0)
        + counts.get("SUPERNUMERARY_BREACH", 0)
    )
    warning = counts.get("INCONSISTENT_CATEGORY", 0) + counts.get("IMPOSSIBLE_DATE", 0) + counts.get("MISSING_REQUIRED_FIELD", 0)

    raw = (
        critical * SEVERITY_WEIGHT[AnomalySeverity.CRITICAL]
        + high * SEVERITY_WEIGHT[AnomalySeverity.HIGH]
        + warning * SEVERITY_WEIGHT[AnomalySeverity.WARNING]
    )
    extra_families = max(len(counts) - 1, 0)
    raw += extra_families * DIVERSITY_BONUS_PER_EXTRA_FAMILY
    score = round(min(raw, MAX_SCORE), 1)

    reasons: list[str] = []
    if critical:
        reasons.append(f"{critical} critical regulatory breach(es).")
    if high:
        reasons.append(f"{high} high-severity integrity issue(s).")
    if warning:
        reasons.append(f"{warning} warning-level data quality issue(s).")
    if extra_families:
        reasons.append(f"{len(counts)} distinct anomaly families detected.")

    return InstitutionRisk(
        institution_id=institution_id,
        score=score,
        band=_band(score),
        critical_count=critical,
        high_count=high,
        warning_count=warning,
        families=sorted(counts),
        reasons=reasons,
    )


def score_all(anomalies) -> list[InstitutionRisk]:
    """Score every institution that carries at least one anomaly."""
    grouped: dict[str, list] = defaultdict(list)
    for anomaly in anomalies:
        grouped[anomaly.institution_id].append(anomaly)
    return [
        score_institution(institution_id, rows)
        for institution_id, rows in sorted(grouped.items())
    ]
