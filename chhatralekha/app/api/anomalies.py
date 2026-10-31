"""Anomaly inspector endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import (
    Principal,
    client_ip,
    get_db,
    require_permission,
)
from app.audit import writer
from app.core import rbac
from app.models.documents import Doc
from app.repositories.anomalies import AnomalyRepository
from app.repositories.audit import AuditRepository
from app.schemas.anomaly import AnomalyOut, AnomalySummary

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


def _anomaly_out(row: Doc) -> AnomalyOut:
    return AnomalyOut(
        anomaly_id=str(row.get("_id", "")),
        student_apaar_id=row.get("student_apaar_id", ""),
        institution_id=row.get("institution_id", ""),
        program_id=row.get("program_id"),
        anomaly_type=row.get("anomaly_type", "INCONSISTENT_CATEGORY"),
        severity=row.get("severity", "WARNING"),
        details=row.get("details", ""),
        recommended_action=row.get("recommended_action", ""),
        detected_at=row.get("detected_at"),
        review_status=row.get("review_status", "PENDING"),
        resolved=row.get("resolved", False),
    )


@router.get("", response_model=list[AnomalyOut], summary="List detected anomalies")
async def list_anomalies(
    institution_id: Optional[str] = None,
    severity: Optional[str] = Query(None),
    anomaly_type: Optional[str] = Query(None),
    apaar_id: Optional[str] = Query(None),
    review_status: Optional[str] = Query(None),
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    principal: Principal = Depends(require_permission(rbac.Permission.REVIEW_ANOMALIES)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> list[AnomalyOut]:
    """List the anomaly register, filtered by the caller's scope."""
    if principal.role != "aicte_admin" and principal.institution_id:
        institution_id = principal.institution_id

    repository = AnomalyRepository(db["anomalies"])
    rows = await repository.all(
        institution_id=institution_id,
        severity=severity,
        anomaly_type=anomaly_type,
        apaar_id=apaar_id,
        review_status=review_status,
        limit=limit,
        offset=offset,
    )
    return [_anomaly_out(row) for row in rows]


@router.get("/summary", response_model=AnomalySummary, summary="Anomaly roll-up")
async def anomaly_summary(
    institution_id: Optional[str] = None,
    principal: Principal = Depends(require_permission(rbac.Permission.REVIEW_ANOMALIES)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> AnomalySummary:
    """A severity and type roll-up of the anomaly register."""
    if principal.role != "aicte_admin" and principal.institution_id:
        institution_id = principal.institution_id
    summary = await AnomalyRepository(db["anomalies"]).summary(institution_id)
    return AnomalySummary(**summary)


@router.post(
    "/{anomaly_id}/review",
    response_model=AnomalyOut,
    summary="Move an anomaly into review",
)
async def review_anomaly(
    anomaly_id: str,
    request: Request,
    review_status: str = Query("RESOLVED", pattern="^(PENDING|IN_REVIEW|RESOLVED|DISMISSED)$"),
    principal: Principal = Depends(require_permission(rbac.Permission.REVIEW_ANOMALIES)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> AnomalyOut:
    """Record a review decision on one finding."""
    repository = AnomalyRepository(db["anomalies"])
    row = await repository.set_review_status(anomaly_id, review_status)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such anomaly."
        )
    if principal.role != "aicte_admin" and principal.institution_id:
        if row.get("institution_id") != principal.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to review another institution's anomalies.",
            )

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="REVIEW_ANOMALY",
        subject=row.get("student_apaar_id", ""),
        details=f"Marked {row.get('anomaly_type')} as {review_status}.",
        category="ANOMALY_REVIEW",
        ip_address=client_ip(request),
    )
    return _anomaly_out(row)
