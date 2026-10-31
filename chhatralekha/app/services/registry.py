"""The registry service: reads the whole MongoDB registry and runs the rules.

This is the bridge between the storage layer and the storage-agnostic rules in
``app.services``. It is deliberately the only place that knows how a MongoDB
document becomes an object the anomaly engine can reason about.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.documents import Doc, docs, student_docs
from app.repositories.anomalies import AnomalyRepository
from app.repositories.students import StudentRepository
from app.services.anomaly_engine import (
    AnomalyType,
    RegistrySnapshot,
    engine,
)
from app.services.risk_scoring import score_all

# ------------------------------------------------------------- snapshot


async def build_snapshot(db: AsyncIOMotorDatabase) -> RegistrySnapshot:
    """Read the whole registry into a snapshot the rules can work on.

    The documents are wrapped with the enum converters the rules expect, so
    the validator, the anomaly engine and the seal signer see the same values
    whether they are fed by MongoDB, by the seed script or by a test fixture.
    """
    institutions = docs(await db["institutions"].find({}).to_list(length=None))
    programmes = docs(await db["programmes"].find({}).to_list(length=None))
    students = student_docs(await db["students"].find({}).to_list(length=None))
    return RegistrySnapshot(
        institutions=institutions,
        programs=programmes,
        students=students,
    )


# ------------------------------------------------------------ recompute


#: The recommended next step for every anomaly family.
RECOMMENDED_ACTIONS: dict[str, str] = {
    AnomalyType.INVALID_APAAR_FORMAT.value: (
        "Ask the institution to re-check the identifier against the APAAR card "
        "and resubmit the row."
    ),
    AnomalyType.DUPLICATE_CROSS_COLLEGE.value: (
        "Refer to the AICTE duplicate-records desk: confirm with both "
        "institutions which admission is genuine before any record is cancelled."
    ),
    AnomalyType.DUPLICATE_SAME_INSTITUTION.value: (
        "Ask the institution to confirm which row is the authoritative "
        "admission and withdraw the other."
    ),
    AnomalyType.DUPLICATE_ROLL_NUMBER.value: (
        "Ask the institution to re-issue a unique institute roll number."
    ),
    AnomalyType.EXCESS_APPROVED_INTAKE.value: (
        "Refer to the regional office: the excess seats need AICTE approval "
        "before they can be regularised."
    ),
    AnomalyType.SUPERNUMERARY_BREACH.value: (
        "Check the supernumerary ceiling for the academic year and ask the "
        "institution to justify or withdraw the excess admissions."
    ),
    AnomalyType.INCONSISTENT_CATEGORY.value: (
        "Ask the institution to correct the quota bucket or attach the "
        "missing foreign-national documentation."
    ),
    AnomalyType.IMPOSSIBLE_DATE.value: (
        "Ask the institution to re-check the date against the student's "
        "official records."
    ),
    AnomalyType.MISSING_REQUIRED_FIELD.value: (
        "Ask the institution to complete the mandatory field; the seat "
        "cannot be counted until it is."
    ),
    AnomalyType.UNSANCTIONED_PROGRAM.value: (
        "Ask the institution to enrol the student in an approved programme, "
        "or to obtain approval for the course code."
    ),
}


async def recompute_anomalies(
    db: AsyncIOMotorDatabase,
) -> list[Doc]:
    """Re-run the detection engine and persist the findings.

    Every finding is written with a rule code, a severity, an explanation and
    a recommended next step, so the review queue is actionable rather than a
    list of raw complaints.
    """
    snapshot = await build_snapshot(db)
    detected = engine.evaluate(snapshot)

    repository = AnomalyRepository(db["anomalies"])
    findings: list[dict[str, Any]] = []
    for finding in detected:
        findings.append(
            {
                "student_apaar_id": finding.student_apaar_id,
                "institution_id": finding.institution_id,
                "program_id": finding.program_id,
                "anomaly_type": finding.anomaly_type.value,
                "severity": finding.severity.value,
                "details": finding.details,
                "recommended_action": RECOMMENDED_ACTIONS.get(
                    finding.anomaly_type.value,
                    "Review the record with the institution.",
                ),
                "detected_at": datetime.now(timezone.utc),
                "review_status": "PENDING",
                "resolved": False,
            }
        )
    await repository.replace_all(findings)

    # Reflect the detection result on the student register.
    students = StudentRepository(db["students"])
    flagged = {
        finding.student_apaar_id
        for finding in detected
        if finding.severity.name in {"CRITICAL", "HIGH"}
    }
    pending = {
        student["apaar_id"]
        for student in snapshot.students
        if student.get("verification_status") == "PENDING_REVIEW"
    }
    await students.set_verification_status(flagged, "FLAGGED_ANOMALY")
    await students.set_verification_status(pending - flagged, "VERIFIED")

    return docs(findings)


# --------------------------------------------------------------- risk


async def risk_scores(db: AsyncIOMotorDatabase) -> list[dict[str, Any]]:
    """The explainable risk score of every institution that carries anomalies."""
    findings = await db["anomalies"].find({}).to_list(length=None)
    return [
        {
            "institution_id": risk.institution_id,
            "score": risk.score,
            "band": risk.band,
            "critical_count": risk.critical_count,
            "high_count": risk.high_count,
            "warning_count": risk.warning_count,
            "families": risk.families,
            "reasons": risk.reasons,
        }
        for risk in score_all(findings)
    ]
