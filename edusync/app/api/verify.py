"""Secure credential verification (requirement 5).

``GET /api/verify/{apaar_id}`` re-derives the seal from the stored record and
compares it with the seal presented by the verifier. The response is
consent-aware: a student who withdrew the *credential verification* consent
still receives a valid verdict, but the personal fields are withheld.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import Principal, client_ip, require_permission
from app.audit import writer
from app.core import rbac
from app.core.database import get_db
from app.models import Anomaly, Consent, ProgramIntake, RevokedCredential, Student
from app.models.enums import ConsentPurpose
from app.schemas.anomaly import AnomalyOut
from app.schemas.student import VerificationResult
from app.services import apaar_validator, consent_policy, qr, seal

router = APIRouter(prefix="/verify", tags=["verification"])


def _payload_for(student: Student) -> seal.CredentialPayload:
    return seal.CredentialPayload(
        apaar_id=student.apaar_id,
        institution_id=student.institution_id,
        program_id=student.program_id,
        academic_year=student.academic_year,
        enrollment_date=student.enrollment_date,
        student_name=student.student_name,
        date_of_birth=student.date_of_birth,
        gender=student.gender.value,
        admission_quota=student.admission_quota.value,
        nationality=student.nationality,
        student_institute_roll_no=student.student_institute_roll_no,
    )


async def _verify(
    apaar_id: str,
    presented_seal: Optional[str],
    request: Request,
    principal: Principal,
    session: AsyncSession,
) -> VerificationResult:
    compact = "".join(char for char in apaar_id if char.isdigit())
    if not compact:
        raise ValueError("An APAAR ID is required.")

    students = (
        await session.execute(select(Student).where(Student.apaar_id == compact))
    ).scalars().all()

    if not students:
        await writer.log(
            session,
            actor=principal.subject,
            actor_role=principal.role,
            action="CREDENTIAL_VERIFICATION",
            subject=compact,
            details="No record found for the presented APAAR ID.",
            category="NOT_FOUND",
            ip_address=client_ip(request),
        )
        await session.commit()
        return VerificationResult(
            verified=False,
            verdict="NOT_FOUND",
            reason="No enrolment record exists for this APAAR ID.",
            apaar_id=compact,
            verified_at=datetime.now(timezone.utc).isoformat(),
        )

    revoked = (
        await session.execute(
            select(RevokedCredential).where(RevokedCredential.apaar_id == compact)
        )
    ).scalars().first()
    if revoked is not None:
        await writer.log(
            session,
            actor=principal.subject,
            actor_role=principal.role,
            action="CREDENTIAL_VERIFICATION",
            subject=compact,
            details=f"Credential is revoked: {revoked.reason}",
            category="REVOKED",
            ip_address=client_ip(request),
        )
        await session.commit()
        return VerificationResult(
            verified=False,
            verdict=seal.SealVerdict.REVOKED.value,
            reason=revoked.reason or "This credential has been revoked.",
            apaar_id=compact,
            verified_at=datetime.now(timezone.utc).isoformat(),
        )

    student = students[0]
    payload = _payload_for(student)

    if presented_seal:
        verification = seal.verify(presented_seal, payload)
        verdict = verification.verdict.value
        reason = verification.reason
        algorithm = verification.algorithm.value if verification.algorithm else None
        key_id = verification.key_id
    else:
        verification = seal.verify(seal.sign(payload), payload)
        verdict = verification.verdict.value
        reason = (
            "The credential is present in the registry and its seal re-derives "
            "correctly from the stored record."
        )
        algorithm = verification.algorithm.value if verification.algorithm else None
        key_id = verification.key_id

    # Consent: the verdict is always disclosed, the personal fields only when
    # the student has consented to credential verification.
    consents = (
        await session.execute(
            select(Consent).where(Consent.student_apaar_id == compact)
        )
    ).scalars().all()
    decision = consent_policy.evaluate(
        ConsentPurpose.CREDENTIAL_VERIFICATION, consents
    )
    consent_note = decision.reason
    disclose = decision.allowed

    anomalies = (
        await session.execute(
            select(Anomaly).where(Anomaly.student_apaar_id == compact)
        )
    ).scalars().all()

    program = (
        await session.execute(
            select(ProgramIntake).where(
                ProgramIntake.institution_id == student.institution_id,
                ProgramIntake.program_id == student.program_id,
            )
        )
    ).scalar_one_or_none()

    student_payload = None
    if disclose:
        from app.schemas.student import StudentOut

        student_payload = StudentOut.model_validate(student)
        student_payload.masked_apaar_id = apaar_validator.mask(student.apaar_id)
    else:
        student_payload = None

    await writer.log(
        session,
        actor=principal.subject,
        actor_role=principal.role,
        action="CREDENTIAL_VERIFICATION",
        subject=compact,
        details=(
            f"Verdict {verdict}; consent {'disclosed' if disclose else 'withheld'} "
            f"({decision.status.value})."
        ),
        category=verdict,
        ip_address=client_ip(request),
    )
    await session.commit()

    return VerificationResult(
        verified=verification.is_valid and student.is_active,
        verdict=verdict,
        reason=reason,
        algorithm=algorithm,
        key_id=key_id,
        apaar_id=compact,
        student=student_payload,
        institution_name=student.institution_id,
        program_name=program.program_name if program else student.program_id,
        seal=presented_seal,
        consent_note=consent_note,
        anomalies=[AnomalyOut.model_validate(row) for row in anomalies],
        verified_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get(
    "/{apaar_id}",
    response_model=VerificationResult,
    summary="Verify an APAAR credential",
)
async def verify_credential(
    apaar_id: str,
    request: Request,
    seal_value: Optional[str] = Query(None, alias="seal"),
    principal: Principal = Depends(require_permission(rbac.Permission.VERIFY_CREDENTIAL)),
    session: AsyncSession = Depends(get_db),
) -> VerificationResult:
    """Verify a credential by APAAR ID, optionally against a presented seal."""
    try:
        return await _verify(apaar_id, seal_value, request, principal, session)
    except ValueError as exc:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


@router.post(
    "/scan",
    response_model=VerificationResult,
    summary="Verify a credential from a scanned QR payload",
)
async def verify_scanned(
    payload: str,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.VERIFY_CREDENTIAL)),
    session: AsyncSession = Depends(get_db),
) -> VerificationResult:
    """Verify a credential from the raw content of a scanned APAAR QR badge."""
    parsed = qr.parse_payload(payload)
    if parsed is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The scanned payload is not an APAAR verification link.",
        )
    return await _verify(
        parsed.apaar_id, parsed.seal, request, principal, session
    )


@router.get(
    "/redirect/{apaar_id}",
    include_in_schema=False,
    summary="Public deep-link target of the APAAR QR badge",
)
async def verify_redirect(
    apaar_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """The public landing target of a scanned badge.

    It renders the verification page in the web portal rather than exposing
    the record to an unauthenticated API caller.
    """
    return RedirectResponse(url=f"/verify?apaar={apaar_id}", status_code=status.HTTP_307_REDIRECT)
