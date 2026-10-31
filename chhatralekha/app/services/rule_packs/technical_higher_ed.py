"""Technical Higher Education Rule Pack (technical_higher_ed).

Executes the regulatory checks designed for technical and professional higher education:
1. APAAR syntactic check (12-digit Luhn-equivalent structure).
2. Cross-institutional multi-enrolment across colleges.
3. Same-institution duplicate enrolment.
4. Duplicate institute roll numbers.
5. Sanctioned regular intake capacity breaches.
6. Supernumerary quota caps (NRI, OCI/FN, TFW, PMSSS).
7. Documentary consistency for foreign nationals & quota contradictions.
8. Impossible calendar dates.
9. Missing mandatory fields.
10. Unsanctioned academic programmes.
"""

from __future__ import annotations

from typing import Any


class TechnicalHigherEdPack:
    """The canonical 10-layer rule pack for higher education technical institutions."""

    name = "technical_higher_ed"

    def evaluate(self, snapshot: Any) -> list[Any]:
        from app.services.anomaly_engine import AnomalyEngine

        engine = AnomalyEngine()
        # Direct call to the 10 layers on technical higher ed snapshot
        anomalies: list[Any] = []
        anomalies += engine.detect_unsanctioned_programmes(snapshot)
        anomalies += engine.detect_missing_required_fields(snapshot)
        anomalies += engine.detect_impossible_dates(snapshot)
        anomalies += engine.detect_inconsistencies(snapshot)
        anomalies += engine.detect_supernumerary_breaches(snapshot)
        anomalies += engine.detect_intake_breaches(snapshot)
        anomalies += engine.detect_duplicate_roll_numbers(snapshot)
        anomalies += engine.detect_same_institution_duplicates(snapshot)
        anomalies += engine.detect_cross_institution_duplicates(snapshot)
        anomalies += engine.detect_invalid_apaar(snapshot)
        return anomalies

