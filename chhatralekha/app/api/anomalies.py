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
from app.schemas.anomaly import (
    AnomalyAssignIn,
    AnomalyNoteIn,
    AnomalyOut,
    AnomalyReviewDecisionIn,
    AnomalySummary,
)

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
        assigned_to=row.get("assigned_to"),
        assigned_reviewer_name=row.get("assigned_reviewer_name"),
        case_notes=row.get("case_notes", []),
        dismissal_reason=row.get("dismissal_reason"),
        ruleset_version=row.get("ruleset_version", "2026.1"),
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
    decision_body: Optional[AnomalyReviewDecisionIn] = None,
    review_status: str = Query("RESOLVED", pattern="^(PENDING|IN_REVIEW|RESOLVED|DISMISSED)$"),
    principal: Principal = Depends(require_permission(rbac.Permission.REVIEW_ANOMALIES)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> AnomalyOut:
    """Record a review decision on one finding."""
    status_target = decision_body.review_status if decision_body else review_status
    reason = decision_body.reason if decision_body else None
    explanation = decision_body.explanation if decision_body else None

    repository = AnomalyRepository(db["anomalies"])
    existing = await repository.get(anomaly_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such anomaly."
        )

    # STRICT OBJECT-LEVEL AUTHORIZATION CHECK BEFORE MUTATING
    if principal.role != "aicte_admin" and principal.institution_id:
        if existing.get("institution_id") != principal.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to review another institution's anomalies.",
            )

    row = await repository.set_review_status(
        anomaly_id,
        status_target,
        dismissal_reason=reason,
        explanation=explanation,
        reviewed_by=principal.subject,
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such anomaly."
        )

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="REVIEW_ANOMALY",
        subject=row.get("student_apaar_id", ""),
        details=f"Marked {row.get('anomaly_type')} as {status_target}. Reason: {reason or 'N/A'}",
        category="ANOMALY_REVIEW",
        ip_address=client_ip(request),
    )
    return _anomaly_out(row)


@router.post(
    "/{anomaly_id}/assign",
    response_model=AnomalyOut,
    summary="Assign a reviewer to an anomaly case",
)
async def assign_anomaly_reviewer(
    anomaly_id: str,
    payload: AnomalyAssignIn,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.REVIEW_ANOMALIES)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> AnomalyOut:
    """Assign an anomaly case to a specific reviewer."""
    repository = AnomalyRepository(db["anomalies"])
    existing = await repository.get(anomaly_id)
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such anomaly.")

    if principal.role != "aicte_admin" and principal.institution_id:
        if existing.get("institution_id") != principal.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to assign another institution's anomalies.",
            )

    row = await repository.assign_reviewer(
        anomaly_id, payload.assignee_id, payload.assignee_name, principal.subject
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Failed to assign anomaly.")

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="ASSIGN_ANOMALY_REVIEWER",
        subject=existing.get("student_apaar_id", ""),
        details=f"Assigned anomaly {anomaly_id} to {payload.assignee_name} ({payload.assignee_id}).",
        category="ANOMALY_REVIEW",
        ip_address=client_ip(request),
    )
    return _anomaly_out(row)


@router.post(
    "/{anomaly_id}/notes",
    response_model=AnomalyOut,
    summary="Append a case note to an anomaly",
)
async def append_anomaly_case_note(
    anomaly_id: str,
    payload: AnomalyNoteIn,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.REVIEW_ANOMALIES)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> AnomalyOut:
    """Add an internal case note with author attribution."""
    repository = AnomalyRepository(db["anomalies"])
    existing = await repository.get(anomaly_id)
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such anomaly.")

    if principal.role != "aicte_admin" and principal.institution_id:
        if existing.get("institution_id") != principal.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to update another institution's anomalies.",
            )

    row = await repository.append_case_note(
        anomaly_id,
        payload.note_text,
        principal.subject,
        principal.display_name or principal.subject,
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Failed to append note.")

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="ADD_ANOMALY_CASE_NOTE",
        subject=existing.get("student_apaar_id", ""),
        details=f"Added internal case note to anomaly {anomaly_id}.",
        category="ANOMALY_REVIEW",
        ip_address=client_ip(request),
    )
    return _anomaly_out(row)
