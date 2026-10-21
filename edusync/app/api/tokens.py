"""Opaque verification tokens.

A token replaces putting the raw APAAR ID in a URL. The token is a
high-entropy, expiring, revocable handle; only its hash is stored, so a dump
of the collection cannot be replayed. The public answer contains an
allowlist of fields and nothing else.

**This verifies against this prototype's database. It is not official APAAR or
AICTE verification.**
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import (
    Principal,
    client_ip,
    get_db,
    require_any_permission,
    require_permission,
)
from app.audit import writer
from app.core import rbac
from app.core.config import get_settings
from app.models.documents import Doc, as_utc
from app.repositories.audit import AuditRepository
from app.repositories.students import StudentRepository
from app.repositories.tokens import VerificationTokenRepository, hash_token
from app.schemas.tokens import (
    PublicVerificationOut,
    TokenIssueRequest,
    TokenIssueResponse,
    TokenOut,
)

router = APIRouter(tags=["verification tokens"])

settings = get_settings()

NOTICE = (
    "Verification against this prototype's database, not official APAAR or AICTE "
    "verification."
)


def _token_out(row: Doc) -> TokenOut:
    return TokenOut(
        token_id=row.get("token_id", ""),
        student_record_id=row.get("student_record_id", ""),
        issued_at=row.get("issued_at"),
        expires_at=row.get("expires_at"),
        revoked=bool(row.get("revoked")),
        needs_reissue=bool(row.get("needs_reissue")),
        issued_by=row.get("issued_by", ""),
    )


@router.post(
    "/verification-tokens",
    response_model=TokenIssueResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Issue an opaque verification token",
)
async def issue_token(
    payload: TokenIssueRequest,
    request: Request,
    principal: Principal = Depends(
        require_any_permission(
            rbac.Permission.VERIFY_CREDENTIAL,
            rbac.Permission.GENERATE_CERTIFICATE,
            rbac.Permission.ONBOARD_STUDENTS,
        )
    ),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> TokenIssueResponse:
    """Issue a token for a record.

    The plaintext is returned exactly once. Only its SHA-256 hash is stored,
    and it is never written to a log.
    """
    students = StudentRepository(db["students"])
    student = await students.get_by_record_id(payload.student_record_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such student record."
        )
    if principal.role != "aicte_admin" and principal.institution_id:
        if student.get("institution_id") != principal.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to issue a token for this record.",
            )

    minutes = payload.minutes or settings.verification_token_minutes
    claims = {
        "institution_id": student.get("institution_id", ""),
        "program_id": student.get("program_id", ""),
        "academic_year": student.get("academic_year", ""),
        "record_status": student.get("record_status", "ACTIVE"),
        "issued_at": int(datetime.now(timezone.utc).timestamp()),
    }
    document, raw = await VerificationTokenRepository(
        db["verification_tokens"]
    ).issue(
        str(student.get("_id", "")),
        claims,
        issued_by=principal.subject,
        minutes=minutes,
    )

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="ISSUE_VERIFICATION_TOKEN",
        subject=str(student.get("apaar_id", "")),
        details=(
            f"Issued a verification token for {minutes} minute(s). "
            f"Reason: {payload.reason or '-'}."
        ),
        category="CREDENTIAL",
        ip_address=client_ip(request),
    )

    return TokenIssueResponse(
        token_id=document.get("token_id", ""),
        token=raw,
        token_url=f"{settings.frontend_origin.rstrip('/')}/verify?token={raw}",
        student_record_id=str(student.get("_id", "")),
        issued_at=document.get("issued_at"),
        expires_at=document.get("expires_at"),
        expires_in_minutes=minutes,
        notice=NOTICE,
    )


@router.get(
    "/verification-tokens",
    response_model=list[TokenOut],
    summary="The tokens issued for a record",
)
async def list_tokens(
    student_record_id: Optional[str] = Query(None),
    principal: Principal = Depends(
        require_permission(rbac.Permission.VERIFY_CREDENTIAL)
    ),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> list[TokenOut]:
    """The tokens issued against one record."""
    if not student_record_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Name the student record whose tokens you want to see.",
        )
    rows = await VerificationTokenRepository(db["verification_tokens"]).for_record(
        student_record_id
    )
    return [_token_out(row) for row in rows]


@router.post(
    "/verification-tokens/{token_id}/revoke",
    response_model=TokenOut,
    summary="Revoke a verification token",
)
async def revoke_token(
    token_id: str,
    request: Request,
    principal: Principal = Depends(
        require_any_permission(
            rbac.Permission.VERIFY_CREDENTIAL,
            rbac.Permission.GENERATE_CERTIFICATE,
            rbac.Permission.ONBOARD_STUDENTS,
        )
    ),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> TokenOut:
    """Revoke a token, so that it stops verifying anything."""
    repository = VerificationTokenRepository(db["verification_tokens"])
    updated = await repository.revoke(token_id)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such token."
        )
    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="REVOKE_VERIFICATION_TOKEN",
        subject=updated.get("student_record_id", ""),
        details=f"Revoked the verification token {token_id}.",
        category="CREDENTIAL",
        ip_address=client_ip(request),
    )
    return _token_out(updated)


@router.get(
    "/verify/token/{token}",
    response_model=PublicVerificationOut,
    summary="Verify a credential with an opaque token (public)",
)
async def verify_token(
    token: str,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> PublicVerificationOut:
    """Verify a credential from an opaque token.

    This endpoint is public, so its answer is an **allowlist**: the record
    status, the institution, the programme, the academic year, the issue
    date and the verdict. It never contains the APAAR ID, the date of birth,
    contact details, notes or the underlying document.

    Every answer is written to the audit trail, and the token itself is never
    logged.
    """
    from app.models.enums import ConsentPurpose
    from app.services import consent_policy

    repository = VerificationTokenRepository(db["verification_tokens"])
    document = await repository.by_hash(hash_token(token))

    async def _answer(valid: bool, verdict: str, reason: str, **extra: Any) -> PublicVerificationOut:
        await writer.log(
            AuditRepository(db["audit_events"]),
            actor="public",
            actor_role="public",
            action="CREDENTIAL_VERIFICATION",
            subject=(document or {}).get("student_record_id", "")[:8],
            details=f"Token verification returned {verdict}.",
            category=verdict,
            ip_address=client_ip(request),
        )
        return PublicVerificationOut(
            valid=valid, verdict=verdict, reason=reason, notice=NOTICE, **extra
        )

    if document is None:
        return await _answer(False, "NOT_FOUND", "No such verification token.")

    if document.get("revoked"):
        return await _answer(
            False, "REVOKED", "This verification token has been revoked."
        )

    expires_at = as_utc(document.get("expires_at"))
    now = datetime.now(timezone.utc)
    if expires_at is not None and expires_at < now:
        return await _answer(
            False, "EXPIRED", "This verification token has expired."
        )

    if document.get("needs_reissue"):
        return await _answer(
            False,
            "NEEDS_REFRESH",
            "The record behind this token was corrected, so the token has to be "
            "reissued.",
            needs_refresh=True,
        )

    record_id = str(document.get("student_record_id", ""))
    student = await StudentRepository(db["students"]).get_by_record_id(record_id)
    if student is None:
        return await _answer(
            False, "NOT_FOUND", "The record behind this token no longer exists."
        )

    if student.get("record_status", "ACTIVE") != "ACTIVE":
        return await _answer(
            False,
            "INACTIVE",
            f"The enrolment record is '{student.get('record_status')}'.",
            record_status=str(student.get("record_status", "")),
        )

    # The consent policy still applies: the verdict is always issued, and the
    # personal fields are withheld when consent is missing or withdrawn. The
    # allowlist itself holds no personal field, so it is unaffected.
    consents = await db["consents"].find(
        {"student_apaar_id": student.get("apaar_id", "")}
    ).to_list(length=None)
    decision = consent_policy.evaluate(
        ConsentPurpose.CREDENTIAL_VERIFICATION, consents
    )

    return await _answer(
        True,
        "VALID",
        "The credential is present in this prototype's registry and is active."
        + (f" Consent: {decision.reason}" if not decision.allowed else ""),
        record_status=str(student.get("record_status", "ACTIVE")),
        institution=str(student.get("institution_id", "")),
        programme=str(student.get("program_id", "")),
        academic_year=str(student.get("academic_year", "")),
        issued_at=document.get("issued_at"),
        expires_at=document.get("expires_at"),
    )
