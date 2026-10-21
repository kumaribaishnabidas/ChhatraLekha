"""Anomaly inspector endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import Principal, client_ip, require_permission
from app.audit import writer
from app.core import rbac
from app.core.database import get_db
from app.models import Anomaly
from app.models.enums import AnomalySeverity, AnomalyType
from app.schemas.anomaly import AnomalyOut, AnomalySummary

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


@router.get("", response_model=list[AnomalyOut], summary="List detected anomalies")
async def list_anomalies(
    institution_id: Optional[str] = Query(None),
    severity: Optional[AnomalySeverity] = Query(None),
    anomaly_type: Optional[AnomalyType] = Query(None),
    apaar_id: Optional[str] = Query(None),
    resolved: Optional[bool] = Query(None),
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    principal: Principal = Depends(require_permission(rbac.Permission.REVIEW_ANOMALIES)),
    session: AsyncSession = Depends(get_db),
) -> list[AnomalyOut]:
    """List the anomaly register, filtered by the caller's scope."""
    statement = select(Anomaly)
    if principal.role != "aicte_admin" and principal.institution_id:
        statement = statement.where(Anomaly.institution_id == principal.institution_id)
    if institution_id:
        statement = statement.where(Anomaly.institution_id == institution_id)
    if severity:
        statement = statement.where(Anomaly.severity == severity)
    if anomaly_type:
        statement = statement.where(Anomaly.anomaly_type == anomaly_type)
    if apaar_id:
        statement = statement.where(Anomaly.student_apaar_id == apaar_id)
    if resolved is not None:
        statement = statement.where(Anomaly.resolved.is_(resolved))

    statement = statement.order_by(Anomaly.detected_at.desc()).limit(limit).offset(offset)
    rows = (await session.execute(statement)).scalars().all()
    return [AnomalyOut.model_validate(row) for row in rows]


@router.get("/summary", response_model=AnomalySummary, summary="Anomaly roll-up")
async def anomaly_summary(
    institution_id: Optional[str] = Query(None),
    principal: Principal = Depends(require_permission(rbac.Permission.REVIEW_ANOMALIES)),
    session: AsyncSession = Depends(get_db),
) -> AnomalySummary:
    """A severity and type roll-up of the anomaly register."""
    statement = select(Anomaly)
    if principal.role != "aicte_admin" and principal.institution_id:
        statement = statement.where(Anomaly.institution_id == principal.institution_id)
    if institution_id:
        statement = statement.where(Anomaly.institution_id == institution_id)

    rows = (await session.execute(statement)).scalars().all()
    by_type: dict[str, int] = {}
    by_institution: dict[str, int] = {}
    counts = {"CRITICAL": 0, "HIGH": 0, "WARNING": 0, "INFO": 0}
    for row in rows:
        by_type[row.anomaly_type.value] = by_type.get(row.anomaly_type.value, 0) + 1
        by_institution[row.institution_id] = by_institution.get(row.institution_id, 0) + 1
        counts[row.severity.value] = counts.get(row.severity.value, 0) + 1
    return AnomalySummary(
        total=len(rows),
        critical=counts["CRITICAL"],
        high=counts["HIGH"],
        warning=counts["WARNING"],
        info=counts["INFO"],
        by_type=by_type,
        by_institution=by_institution,
    )


@router.post(
    "/{anomaly_id}/resolve",
    response_model=AnomalyOut,
    summary="Mark an anomaly as resolved",
)
async def resolve_anomaly(
    anomaly_id: int,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.REVIEW_ANOMALIES)),
    session: AsyncSession = Depends(get_db),
) -> AnomalyOut:
    """Mark an anomaly as reviewed and resolved."""
    row = (
        await session.execute(select(Anomaly).where(Anomaly.anomaly_id == anomaly_id))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such anomaly."
        )
    if principal.role != "aicte_admin" and principal.institution_id:
        if row.institution_id != principal.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to resolve another institution's anomalies.",
            )
    row.resolved = True
    await writer.log(
        session,
        actor=principal.subject,
        actor_role=principal.role,
        action="RESOLVE_ANOMALY",
        subject=row.student_apaar_id,
        details=f"Marked {row.anomaly_type.value} as resolved.",
        category="ANOMALY_REVIEW",
        ip_address=client_ip(request),
    )
    await session.commit()
    await session.refresh(row)
    return AnomalyOut.model_validate(row)
