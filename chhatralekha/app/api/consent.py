"""Consent ledger endpoints (requirement 7.7 / section 8.7)."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import (
    Principal,
    client_ip,
    ensure_can_access_student,
    get_db,
    get_principal,
    require_permission,
)
from app.audit import writer
from app.core import rbac
from app.models.documents import Doc
from app.repositories.audit import AuditRepository
from app.repositories.consents import ConsentRepository
from app.repositories.students import StudentRepository
from app.schemas.consent import ConsentDecisionOut, ConsentOut, ConsentRequest
from app.services import consent_policy

router = APIRouter(prefix="/consent", tags=["consent"])


def _consent_out(row: Doc) -> ConsentOut:
    return ConsentOut(
        consent_id=row.get("consent_id", ""),
        student_apaar_id=row.get("student_apaar_id", ""),
        purpose=row.get("purpose", "CREDENTIAL_VERIFICATION"),
        status=row.get("status", "PENDING"),
        channel=row.get("channel", "WEB_PORTAL"),
        policy_version=row.get("policy_version", "2024-01"),
        recorded_at=row.get("recorded_at") or datetime.now(timezone.utc),
        revoked_at=row.get("revoked_at"),
        expires_at=row.get("expires_at"),
        evidence=row.get("evidence"),
        granted_by=row.get("granted_by", ""),
    )


@router.get("/{apaar_id}", response_model=list[ConsentOut], summary="The consent ledger of a student")
async def list_consents(
    apaar_id: str,
    request: Request,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> list[ConsentOut]:
    """Every consent record belonging to a student."""
    students = StudentRepository(db["students"])
    student = await students.get(apaar_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such APAAR ID."
        )
    await ensure_can_access_student(
        principal,
        student,
        db=db,
        request=request,
        detail="You are not allowed to access another institution's consents.",
    )
    rows = await ConsentRepository(db["consents"]).for_apaar_id(apaar_id)
    return [_consent_out(row) for row in rows]


@router.get(
    "/{apaar_id}/decisions",
    response_model=list[ConsentDecisionOut],
    summary="The effective consent state per purpose",
)
async def consent_decisions(
    apaar_id: str,
    request: Request,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> list[ConsentDecisionOut]:
    """Evaluate the ledger against every consent purpose."""
    students = StudentRepository(db["students"])
    student = await students.get(apaar_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such APAAR ID."
        )
    await ensure_can_access_student(
        principal,
        student,
        db=db,
        request=request,
        detail="You are not allowed to access another institution's consents.",
    )
    rows = await ConsentRepository(db["consents"]).for_apaar_id(apaar_id)
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
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> ConsentOut:
    """Write a new consent record to the ledger.

    Consent is recorded per purpose, so granting credential verification
    never implies consent to share the record with an employer.
    """
    students = StudentRepository(db["students"])
    student = await students.get(payload.apaar_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such APAAR ID."
        )
    await ensure_can_access_student(
        principal,
        student,
        db=db,
        request=request,
        detail="You are not allowed to manage another institution's consents.",
    )

    now = datetime.now(timezone.utc)
    status_value = (
        payload.status.value if hasattr(payload.status, "value") else payload.status
    )
    purpose_value = payload.purpose.value if hasattr(payload.purpose, "value") else payload.purpose
    channel_value = payload.channel.value if hasattr(payload.channel, "value") else payload.channel

    entry = await ConsentRepository(db["consents"]).insert(
        {
            "consent_id": f"CNS-{now.strftime('%Y%m%d%H%M%S%f')[:16]}",
            "student_apaar_id": payload.apaar_id,
            "purpose": purpose_value,
            "status": status_value,
            "channel": channel_value,
            "policy_version": payload.policy_version,
            "recorded_at": now,
            "revoked_at": now if status_value == "REVOKED" else None,
            "expires_at": payload.expires_at,
            "evidence": payload.evidence,
            "granted_by": principal.subject,
            "ip_address": client_ip(request),
        }
    )

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="CONSENT_RECORDED",
        subject=payload.apaar_id,
        details=f"{status_value} for {purpose_value} via {channel_value}.",
        category="CONSENT",
        ip_address=client_ip(request),
    )
    return _consent_out(entry)
