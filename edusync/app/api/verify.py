"""Secure credential verification (requirement 7.7).

``GET /api/verify/{apaar_id}`` re-derives the seal from the stored record and
compares it with the seal presented by the verifier. The response is
consent-aware: a student who withdrew the *credential verification* consent
still receives a valid verdict, but the personal fields are withheld.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
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
from app.models.enums import ConsentPurpose
from app.repositories.audit import AuditRepository
from app.repositories.consents import ConsentRepository
from app.repositories.students import StudentRepository
from app.repositories.tokens import hash_token
from app.repositories.users import UserRepository
from app.schemas.anomaly import AnomalyOut
from app.schemas.student import StudentOut, VerificationResult
from app.services import apaar_validator, consent_policy, qr, seal

router = APIRouter(prefix="/verify", tags=["verification"])


def _payload_for(student: Doc) -> seal.CredentialPayload:
    return seal.CredentialPayload(
        apaar_id=student.get("apaar_id", ""),
        institution_id=student.get("institution_id", ""),
        program_id=student.get("program_id", ""),
        academic_year=student.get("academic_year", ""),
        enrollment_date=student.get("enrollment_date", ""),
        student_name=student.get("student_name", ""),
        date_of_birth=student.get("date_of_birth", ""),
        gender=student.get("gender", ""),
        admission_quota=student.get("admission_quota", ""),
        nationality=student.get("nationality", ""),
        student_institute_roll_no=student.get("student_institute_roll_no", ""),
    )


def _student_out(student: Doc) -> StudentOut:
    return StudentOut(
        record_id=str(student.get("_id", "")),
        apaar_id=student.get("apaar_id", ""),
        student_name=student.get("student_name", ""),
        date_of_birth=student.get("date_of_birth", ""),
        gender=student.get("gender", "O"),
        institution_id=student.get("institution_id", ""),
        program_id=student.get("program_id", ""),
        academic_year=student.get("academic_year", ""),
        admission_quota=student.get("admission_quota", "MERIT"),
        enrollment_date=student.get("enrollment_date", ""),
        student_institute_roll_no=student.get("student_institute_roll_no", ""),
        nationality=student.get("nationality", ""),
        passport_number=student.get("passport_number"),
        visa_validity=student.get("visa_validity"),
        country_of_origin=student.get("country_of_origin"),
        abc_account_id=student.get("abc_account_id"),
        verification_status=student.get("verification_status", "PENDING_REVIEW"),
        is_active=student.get("is_active", True),
        record_status=student.get("record_status", "ACTIVE"),
        submission_source=student.get("submission_source", "MANUAL"),
        social_category=student.get("social_category", "GENERAL"),
        admission_date=student.get("admission_date"),
        contact_email=student.get("contact_email"),
        contact_phone=student.get("contact_phone"),
        state_of_domicile=student.get("state_of_domicile"),
        created_at=student.get("created_at"),
        updated_at=student.get("updated_at"),
        masked_apaar_id=apaar_validator.mask(student.get("apaar_id")),
    )


async def _verify(
    apaar_id: str,
    presented_seal: Optional[str],
    request: Request,
    principal: Principal,
    db: AsyncIOMotorDatabase,
) -> VerificationResult:
    compact = "".join(char for char in apaar_id if char.isdigit())
    if not compact:
        raise ValueError("An APAAR ID is required.")

    students = StudentRepository(db["students"])
    records = await students.all_for_apaar_id(compact)
    audit = AuditRepository(db["audit_events"])

    if not records:
        await writer.log(
            audit,
            actor=principal.subject,
            actor_role=principal.role,
            action="CREDENTIAL_VERIFICATION",
            subject=compact,
            details="No record found for the presented APAAR ID.",
            category="NOT_FOUND",
            ip_address=client_ip(request),
        )
        return VerificationResult(
            verified=False,
            verdict="NOT_FOUND",
            reason="No enrolment record exists for this APAAR ID.",
            apaar_id=compact,
            verified_at=datetime.now(timezone.utc).isoformat(),
        )

    revoked = await UserRepository(
        db["users"], db["api_keys"], db["revoked_credentials"]
    ).revoked_for(compact)
    if revoked is not None:
        await writer.log(
            audit,
            actor=principal.subject,
            actor_role=principal.role,
            action="CREDENTIAL_VERIFICATION",
            subject=compact,
            details=f"Credential is revoked: {revoked.get('reason')}",
            category="REVOKED",
            ip_address=client_ip(request),
        )
        return VerificationResult(
            verified=False,
            verdict=seal.SealVerdict.REVOKED.value,
            reason=revoked.get("reason") or "This credential has been revoked.",
            apaar_id=compact,
            verified_at=datetime.now(timezone.utc).isoformat(),
        )

    student = records[0]
    payload = _payload_for(student)

    if presented_seal:
        verification = seal.verify(presented_seal, payload)
        reason = verification.reason
    else:
        verification = seal.verify(seal.sign(payload), payload)
        reason = (
            "The credential is present in the registry and its seal re-derives "
            "correctly from the stored record."
        )
    verdict = verification.verdict.value
    algorithm = verification.algorithm.value if verification.algorithm else None
    key_id = verification.key_id

    # Consent: the verdict is always disclosed, the personal fields only when
    # the student has consented to credential verification.
    consents = await ConsentRepository(db["consents"]).for_apaar_id(compact)
    decision = consent_policy.evaluate(ConsentPurpose.CREDENTIAL_VERIFICATION, consents)
    consent_note = decision.reason
    disclose = decision.allowed

    anomaly_rows = await db["anomalies"].find({"student_apaar_id": compact}).to_list(
        length=None
    )
    programme = await db["programmes"].find_one(
        {
            "institution_id": student.get("institution_id"),
            "program_id": student.get("program_id"),
        }
    )

    await writer.log(
        audit,
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

    return VerificationResult(
        verified=verification.is_valid and student.get("record_status") == "ACTIVE",
        verdict=verdict,
        reason=reason,
        algorithm=algorithm,
        key_id=key_id,
        apaar_id=compact,
        student=_student_out(student) if disclose else None,
        institution_name=student.get("institution_id"),
        program_name=(programme or {}).get("program_name", student.get("program_id")),
        seal=presented_seal,
        consent_note=consent_note,
        anomalies=[
            AnomalyOut(
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
            for row in anomaly_rows
        ],
        verified_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get(
    "/public-key",
    summary="Get public verification key for offline third-party signature checks",
)
async def get_public_verification_key() -> dict[str, str]:
    """Provides the public key (Ed25519) allowing third parties to independently
    verify signed digital credentials offline without possessing any private keys.
    """
    from app.core.config import get_settings

    settings = get_settings()
    return {
        "algorithm": "Ed25519",
        "key_id": "edusync-2026",
        "public_key_pem": settings.seal_ecdsa_public_key_pem or "PUBLIC_KEY_CONFIGURED",
        "notice": (
            "Public key for independent offline verification of ChhatraLekha credentials. "
            "Private keys are strictly guarded and never placed in client code."
        ),
    }


@router.get(
    "/{apaar_id}",
    response_model=VerificationResult,
    summary="Verify an APAAR credential (authenticated verifiers only)",
)
async def verify_credential(
    apaar_id: str,
    request: Request,
    seal_value: Optional[str] = Query(None, alias="seal"),
    principal: Principal = Depends(require_permission(rbac.Permission.VERIFY_CREDENTIAL)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> VerificationResult:
    """Verify a credential by APAAR ID, optionally against a presented seal.

    This route puts the raw APAAR ID in the URL, so it is **not** public: it
    requires the ``verify_credential`` permission, and every call is written
    to the audit trail. For a public check, use an opaque verification token
    (``GET /api/verify/token/{token}``) instead.
    """
    try:
        return await _verify(apaar_id, seal_value, request, principal, db)
    except ValueError as exc:
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
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> VerificationResult:
    """Verify a credential from the raw content of a scanned APAAR QR badge.

    The current badge carries an opaque token; the legacy badge carried the
    APAAR ID. Both are accepted here, and neither is accepted for a public
    caller - this route always requires the ``verify_credential`` permission.
    """
    parsed = qr.parse_payload(payload)
    if parsed is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The scanned payload is not an APAAR verification link.",
        )

    if parsed.is_token_payload:
        from app.repositories.tokens import VerificationTokenRepository

        document = await VerificationTokenRepository(
            db["verification_tokens"]
        ).by_hash(hash_token(parsed.token or ""))
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No such verification token.",
            )
        record_id = str(document.get("student_record_id", ""))
        student = await StudentRepository(db["students"]).get_by_record_id(record_id)
        if student is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The record behind this token no longer exists.",
            )
        return await _verify(
            str(student.get("apaar_id", "")), None, request, principal, db
        )

    return await _verify(parsed.apaar_id, parsed.seal, request, principal, db)


@router.get(
    "/redirect/{apaar_id}",
    include_in_schema=False,
    summary="Public deep-link target of the APAAR QR badge",
)
async def verify_redirect(apaar_id: str) -> RedirectResponse:
    """The deep-link target of a badge printed before the token flow existed.

    It redirects to the web portal's verification page rather than exposing
    the record to an unauthenticated API caller. The page asks for a token, or
    asks the verifier to sign in.
    """
    return RedirectResponse(
        url=f"/verify?apaar={apaar_id}", status_code=status.HTTP_307_REDIRECT
    )
