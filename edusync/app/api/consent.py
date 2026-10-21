"""Consent ledger endpoints (requirement 8)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import Principal, client_ip, get_principal, require_permission
from app.audit import writer
from app.core import rbac
from app.core.database import get_db
from app.models import Consent, Student
from app.models.enums import ConsentStatus
from app.schemas.consent import ConsentDecisionOut, ConsentOut, ConsentRequest
from app.services import consent_policy

router = APIRouter(prefix="/consent", tags=["consent"])


@router.get("/{apaar_id}", response_model=list[ConsentOut], summary="The consent ledger of a student")
async def list_consents(
    apaar_id: str,
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db),
) -> list[ConsentOut]:
    """Every consent record belonging to a student."""
    rows = (
        await session.execute(
            select(Consent)
            .where(Consent.student_apaar_id == apaar_id)
            .order_by(Consent.recorded_at.desc())
        )
    ).scalars().all()
    return [ConsentOut.model_validate(row) for row in rows]


@router.get(
    "/{apaar_id}/decisions",
    response_model=list[ConsentDecisionOut],
    summary="The effective consent state per purpose",
)
async def consent_decisions(
    apaar_id: str,
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db),
) -> list[ConsentDecisionOut]:
    """Evaluate the ledger against every consent purpose."""
    rows = (
        await session.execute(
            select(Consent).where(Consent.student_apaar_id == apaar_id)
        )
    ).scalars().all()
    return [
        ConsentDecisionOut(
            purpose=decision.purpose,
            purpose_label=decision.purpose_label,
            status=decision.status,
            allowed=decision.allowed,
            reason=decision.reason,
            recorded_at=decision.recorded_at,
        )
        for decision in consent_policy.evaluate_all(rows)
    ]


@router.post(
    "",
    response_model=ConsentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Grant or revoke a consent",
)
async def record_consent(
    payload: ConsentRequest,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.MANAGE_CONSENT)),
    session: AsyncSession = Depends(get_db),
) -> ConsentOut:
    """Write a new consent record to the ledger."""
    student = (
        await session.execute(select(Student).where(Student.apaar_id == payload.apaar_id))
    ).scalar_one_or_none()
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such APAAR ID."
        )
    if principal.role != "aicte_admin" and principal.institution_id:
        if student.institution_id != principal.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to manage another institution's consents.",
            )

    now = datetime.now(timezone.utc)
    entry = Consent(
        consent_id=f"CNS-{uuid.uuid4().hex[:16].upper()}",
        student_apaar_id=payload.apaar_id,
        purpose=payload.purpose,
        status=payload.status,
        channel=payload.channel,
        policy_version=payload.policy_version,
        recorded_at=now,
        revoked_at=now if payload.status == ConsentStatus.REVOKED else None,
        evidence=payload.evidence,
        granted_by=principal.subject,
        ip_address=client_ip(request),
    )
    session.add(entry)
    await session.flush()

    await writer.log(
        session,
        actor=principal.subject,
        actor_role=principal.role,
        action="CONSENT_RECORDED",
        subject=payload.apaar_id,
        details=f"{payload.status.value} for {payload.purpose.value} via {payload.channel.value}.",
        category="CONSENT",
        ip_address=client_ip(request),
    )
    await session.commit()
    await session.refresh(entry)
    return ConsentOut.model_validate(entry)
