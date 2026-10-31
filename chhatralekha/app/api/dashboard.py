"""Real-time dashboard endpoints (requirement 7.10)."""

from __future__ import annotations

from collections import Counter
from typing import Optional

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import Principal, get_db, get_principal
from app.models.enums import AdmissionQuota
from app.schemas.dashboard import (
    ComplianceRow,
    IntakeRow,
    NationalKpis,
    QuotaDistributionRow,
    RiskScoreOut,
)
from app.services.anomaly_engine import engine
from app.services.registry import build_snapshot, risk_scores

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/national", response_model=NationalKpis, summary="Pan-India headline numbers")
async def national_kpis(
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> NationalKpis:
    """The live headline numbers of the AICTE Directorate dashboard."""
    institutions = await db["institutions"].count_documents({})
    programmes = await db["programmes"].count_documents({})
    enrolled = await db["students"].count_documents({"record_status": "ACTIVE"})
    anomalies = await db["anomalies"].count_documents({})
    critical = await db["anomalies"].count_documents({"severity": "CRITICAL"})

    approved_rows = await db["programmes"].find({}, {"approved_intake": 1}).to_list(
        length=None
    )
    approved = sum(row.get("approved_intake", 0) for row in approved_rows)

    supernumerary = await db["students"].count_documents(
        {
            "record_status": "ACTIVE",
            "admission_quota": {
                "$in": [
                    AdmissionQuota.NRI.value,
                    AdmissionQuota.OCI.value,
                    AdmissionQuota.FN.value,
                    AdmissionQuota.TFW.value,
                ]
            },
        }
    )

    return NationalKpis(
        institution_count=institutions,
        programme_count=programmes,
        total_approved_intake=approved,
        total_enrolled=enrolled,
        flagged_anomalies=anomalies,
        critical_anomalies=critical,
        supernumerary_enrolled=supernumerary,
        utilisation_percent=round(enrolled / approved * 100, 1) if approved else 0.0,
    )


@router.get("/intake", response_model=list[IntakeRow], summary="Live intake utilisation")
async def intake_matrix(
    institution_id: Optional[str] = Query(None),
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> list[IntakeRow]:
    """The live utilisation of every sanctioned programme."""
    snapshot = await build_snapshot(db)
    institutions = {
        row["institution_id"]: row
        for row in await db["institutions"].find({}).to_list(length=None)
    }

    rows: list[IntakeRow] = []
    for item in engine.build_snapshots(snapshot):
        program = item.program
        if institution_id and program.get("institution_id") != institution_id:
            continue
        institution = institutions.get(program.get("institution_id"), {})
        rows.append(
            IntakeRow(
                institution_id=program.get("institution_id", ""),
                institution_name=institution.get("name", ""),
                program_id=program.get("program_id", ""),
                program_name=program.get("program_name", ""),
                program_level=program.get("program_level", "UG"),
                approved_intake=program.get("approved_intake", 0),
                regular_enrolled=item.regular_enrolled,
                supernumerary_enrolled=item.supernumerary_enrolled,
                total_enrolled=item.total_enrolled,
                total_sanctioned=program.get("total_sanctioned", 0),
                nri_enrolled=item.nri_enrolled,
                oci_fn_enrolled=item.oci_fn_enrolled,
                tfw_enrolled=item.tfw_enrolled,
                pmsss_enrolled=item.pmsss_enrolled,
                utilisation_percent=round(item.overall_utilisation * 100, 1),
                has_breach=item.has_breach,
            )
        )
    return rows


@router.get("/quota", response_model=list[QuotaDistributionRow], summary="Quota distribution")
async def quota_distribution(
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> list[QuotaDistributionRow]:
    """How the national enrolment splits across the quota buckets."""
    enrolled = Counter()
    async for row in db["students"].aggregate(
        [
            {"$match": {"record_status": "ACTIVE"}},
            {"$group": {"_id": "$admission_quota", "count": {"$sum": 1}}},
        ]
    ):
        enrolled[row["_id"]] = row["count"]

    sanctioned = Counter()
    async for row in db["programmes"].aggregate(
        [
            {
                "$group": {
                    "_id": None,
                    "merit": {"$sum": "$approved_intake"},
                    "nri": {"$sum": "$max_supernumerary_nri"},
                    "oci_fn": {"$sum": "$max_supernumerary_fn_oci"},
                    "tfw": {"$sum": "$max_supernumerary_tfw"},
                    "pmsss": {"$sum": "$max_pmsss"},
                }
            }
        ]
    ):
        sanctioned[AdmissionQuota.MERIT] = row.get("merit", 0)
        sanctioned[AdmissionQuota.NRI] = row.get("nri", 0)
        sanctioned[AdmissionQuota.OCI] = row.get("oci_fn", 0)
        sanctioned[AdmissionQuota.TFW] = row.get("tfw", 0)
        sanctioned[AdmissionQuota.PMSSS] = row.get("pmsss", 0)

    rows: list[QuotaDistributionRow] = []
    for quota in AdmissionQuota:
        count = enrolled.get(quota.value, 0)
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
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> list[ComplianceRow]:
    """Every institution scored against its sanctioned intake."""
    institutions = await db["institutions"].find({}).to_list(length=None)
    risks = {risk["institution_id"]: risk for risk in await risk_scores(db)}

    breaches = Counter()
    async for row in db["anomalies"].aggregate(
        [{"$group": {"_id": "$institution_id", "count": {"$sum": 1}}}]
    ):
        breaches[row["_id"]] = row["count"]

    approved_by_institution = Counter()
    async for row in db["programmes"].aggregate(
        [{"$group": {"_id": "$institution_id", "total": {"$sum": "$approved_intake"}}}]
    ):
        approved_by_institution[row["_id"]] = row["total"]

    enrolled_by_institution = Counter()
    async for row in db["students"].aggregate(
        [
            {"$match": {"record_status": "ACTIVE"}},
            {"$group": {"_id": "$institution_id", "total": {"$sum": 1}}},
        ]
    ):
        enrolled_by_institution[row["_id"]] = row["total"]

    rows: list[ComplianceRow] = []
    for institution in institutions:
        approved = approved_by_institution.get(institution["institution_id"], 0)
        enrolled = enrolled_by_institution.get(institution["institution_id"], 0)
        risk = risks.get(institution["institution_id"])
        rows.append(
            ComplianceRow(
                institution_id=institution["institution_id"],
                institution_name=institution.get("name", ""),
                state=institution.get("state", ""),
                total_approved=approved,
                total_enrolled=enrolled,
                utilisation=round(enrolled / approved, 3) if approved else 0.0,
                breaches=breaches.get(institution["institution_id"], 0),
                risk_band=risk["band"] if risk else "LOW",
                risk_score=risk["score"] if risk else 0.0,
            )
        )
    rows.sort(key=lambda row: row.risk_score, reverse=True)
    return rows


@router.get("/risk", response_model=list[RiskScoreOut], summary="Institution risk scores")
async def risk_score_list(
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> list[RiskScoreOut]:
    """The explainable risk score of every institution that carries anomalies."""
    return [RiskScoreOut(**risk) for risk in await risk_scores(db)]
