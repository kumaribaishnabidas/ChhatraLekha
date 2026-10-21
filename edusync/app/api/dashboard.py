"""Real-time dashboard endpoints (requirement 4)."""

from __future__ import annotations

from collections import Counter
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import Principal, get_principal
from app.core.database import get_db
from app.models import Anomaly, Institution, ProgramIntake, Student
from app.models.enums import AdmissionQuota
from app.schemas.dashboard import (
    ComplianceRow,
    IntakeRow,
    NationalKpis,
    QuotaDistributionRow,
    RiskScoreOut,
)
from app.services import risk_scoring
from app.services.anomaly_engine import RegistrySnapshot, engine

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/national", response_model=NationalKpis, summary="Pan-India headline numbers")
async def national_kpis(
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db),
) -> NationalKpis:
    """The live headline numbers of the AICTE Directorate dashboard."""
    institutions = (await session.execute(select(Institution))).scalars().all()
    programs = (await session.execute(select(ProgramIntake))).scalars().all()
    students = (await session.execute(select(Student))).scalars().all()
    anomalies = (await session.execute(select(Anomaly))).scalars().all()

    active = [student for student in students if student.is_active]
    approved = sum(program.approved_intake for program in programs)
    enrolled = len(active)
    critical = sum(1 for row in anomalies if row.severity.name == "CRITICAL")
    supernumerary = sum(
        1 for student in active if student.admission_quota.is_supernumerary
    )
    return NationalKpis(
        institution_count=len(institutions),
        programme_count=len(programs),
        total_approved_intake=approved,
        total_enrolled=enrolled,
        flagged_anomalies=len(anomalies),
        critical_anomalies=critical,
        supernumerary_enrolled=supernumerary,
        utilisation_percent=round(enrolled / approved * 100, 1) if approved else 0.0,
    )


@router.get("/intake", response_model=list[IntakeRow], summary="Live intake utilisation")
async def intake_matrix(
    institution_id: Optional[str] = Query(None),
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db),
) -> list[IntakeRow]:
    """The live utilisation of every sanctioned programme."""
    programs = (await session.execute(select(ProgramIntake))).scalars().all()
    students = (await session.execute(select(Student))).scalars().all()
    institutions = {
        row.institution_id: row for row in (await session.execute(select(Institution))).scalars().all()
    }

    snapshots = engine.build_snapshots(
        RegistrySnapshot(programs=programs, students=students)
    )

    rows: list[IntakeRow] = []
    for snapshot in snapshots:
        if institution_id and snapshot.program.institution_id != institution_id:
            continue
        program = snapshot.program
        institution = institutions.get(program.institution_id)
        rows.append(
            IntakeRow(
                institution_id=program.institution_id,
                institution_name=institution.name if institution else "",
                program_id=program.program_id,
                program_name=program.program_name,
                program_level=program.program_level,
                approved_intake=program.approved_intake,
                regular_enrolled=snapshot.regular_enrolled,
                supernumerary_enrolled=snapshot.supernumerary_enrolled,
                total_enrolled=snapshot.total_enrolled,
                total_sanctioned=program.total_sanctioned,
                nri_enrolled=snapshot.nri_enrolled,
                oci_fn_enrolled=snapshot.oci_fn_enrolled,
                tfw_enrolled=snapshot.tfw_enrolled,
                pmsss_enrolled=snapshot.pmsss_enrolled,
                utilisation_percent=round(snapshot.overall_utilisation * 100, 1),
                has_breach=snapshot.has_breach,
            )
        )
    return rows


@router.get("/quota", response_model=list[QuotaDistributionRow], summary="Quota distribution")
async def quota_distribution(
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db),
) -> list[QuotaDistributionRow]:
    """How the national enrolment splits across the quota buckets."""
    programs = (await session.execute(select(ProgramIntake))).scalars().all()
    students = (await session.execute(select(Student))).scalars().all()

    enrolled: Counter = Counter()
    for student in students:
        if student.is_active:
            enrolled[student.admission_quota] += 1

    sanctioned: Counter = Counter()
    for program in programs:
        sanctioned[AdmissionQuota.MERIT] += program.approved_intake
        sanctioned[AdmissionQuota.NRI] += program.max_supernumerary_nri
        sanctioned[AdmissionQuota.OCI] += program.max_supernumerary_fn_oci
        sanctioned[AdmissionQuota.TFW] += program.max_supernumerary_tfw
        sanctioned[AdmissionQuota.PMSSS] += program.max_pmsss

    rows: list[QuotaDistributionRow] = []
    for quota in AdmissionQuota:
        count = enrolled.get(quota, 0)
        cap = sanctioned.get(quota, 0)
        rows.append(
            QuotaDistributionRow(
                label=quota.label,
                quota=quota,
                enrolled=count,
                sanctioned=cap,
                utilisation=round(min(count / cap, 1.35), 3) if cap else 0.0,
            )
        )
    return rows


@router.get("/compliance", response_model=list[ComplianceRow], summary="Institution compliance matrix")
async def compliance_matrix(
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db),
) -> list[ComplianceRow]:
    """Every institution scored against its sanctioned intake."""
    institutions = (await session.execute(select(Institution))).scalars().all()
    programs = (await session.execute(select(ProgramIntake))).scalars().all()
    students = (await session.execute(select(Student))).scalars().all()
    anomalies = (await session.execute(select(Anomaly))).scalars().all()

    risks = {risk.institution_id: risk for risk in risk_scoring.score_all(anomalies)}
    breaches = Counter(row.institution_id for row in anomalies)

    rows: list[ComplianceRow] = []
    for institution in institutions:
        approved = sum(
            program.approved_intake
            for program in programs
            if program.institution_id == institution.institution_id
        )
        enrolled = sum(
            1
            for student in students
            if student.institution_id == institution.institution_id and student.is_active
        )
        risk = risks.get(institution.institution_id)
        rows.append(
            ComplianceRow(
                institution_id=institution.institution_id,
                institution_name=institution.name,
                state=institution.state,
                total_approved=approved,
                total_enrolled=enrolled,
                utilisation=round(enrolled / approved, 3) if approved else 0.0,
                breaches=breaches.get(institution.institution_id, 0),
                risk_band=risk.band if risk else "LOW",
                risk_score=risk.score if risk else 0.0,
            )
        )
    rows.sort(key=lambda row: row.risk_score, reverse=True)
    return rows


@router.get("/risk", response_model=list[RiskScoreOut], summary="Institution risk scores")
async def risk_scores(
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db),
) -> list[RiskScoreOut]:
    """The explainable risk score of every institution that carries anomalies."""
    anomalies = (await session.execute(select(Anomaly))).scalars().all()
    return [
        RiskScoreOut(
            institution_id=risk.institution_id,
            score=risk.score,
            band=risk.band,
            critical_count=risk.critical_count,
            high_count=risk.high_count,
            warning_count=risk.warning_count,
            families=risk.families,
            reasons=risk.reasons,
        )
        for risk in risk_scoring.score_all(anomalies)
    ]
