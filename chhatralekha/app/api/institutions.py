"""Institution and programme-capacity endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import (
    Principal,
    client_ip,
    get_db,
    get_principal,
    require_permission,
)
from app.audit import writer
from app.core import rbac
from app.core.security import hash_password
from app.models.documents import Doc
from app.models.enums import InstitutionCategory, InstitutionVerificationStatus
from app.repositories.audit import AuditRepository
from app.repositories.institutions import InstitutionRepository
from app.repositories.programmes import ProgrammeRepository
from app.repositories.students import StudentRepository
from app.schemas.campus import InstitutionRegisterIn, InstitutionReviewIn
from app.schemas.student import InstitutionOut, ProgrammeIntakeIn, ProgrammeIntakeOut

router = APIRouter(prefix="/institutions", tags=["institutions"])


def _institution_out(row: Doc) -> InstitutionOut:
    return InstitutionOut(
        institution_id=row.get("institution_id", ""),
        name=row.get("name", ""),
        institution_type=row.get("institution_type", "ENGINEERING"),
        state=row.get("state", ""),
        city=row.get("city", ""),
        affiliation_university=row.get("affiliation_university", ""),
        approval_year=row.get("approval_year", 0),
        naac_grade=row.get("naac_grade", ""),
        email=row.get("email"),
        phone=row.get("phone"),
        is_active=row.get("is_active", True),
    )


def _programme_out(row: Doc) -> ProgrammeIntakeOut:
    return ProgrammeIntakeOut(
        id=str(row.get("_id", "")),
        program_id=row.get("program_id", ""),
        institution_id=row.get("institution_id", ""),
        program_name=row.get("program_name", ""),
        program_level=row.get("program_level", "UG"),
        academic_year=row.get("academic_year", "2024-25"),
        policy_version=row.get("policy_version", "aph-2024-01"),
        approved_intake=row.get("approved_intake", 0),
        max_supernumerary_nri=row.get("max_supernumerary_nri", 0),
        max_supernumerary_fn_oci=row.get("max_supernumerary_fn_oci", 0),
        max_supernumerary_tfw=row.get("max_supernumerary_tfw", 0),
        max_pmsss=row.get("max_pmsss", 0),
        total_sanctioned=row.get("total_sanctioned", 0),
    )


@router.get("", response_model=list[InstitutionOut], summary="List institutions")
async def list_institutions(
    state: Optional[str] = None,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> list[InstitutionOut]:
    """List the AICTE-approved institutions."""
    repository = InstitutionRepository(db["institutions"])
    rows = await repository.all(state=state)
    return [_institution_out(row) for row in rows]


@router.get(
    "/{institution_id}",
    response_model=InstitutionOut,
    summary="Fetch one institution",
)
async def get_institution(
    institution_id: str,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> InstitutionOut:
    """Fetch a single institution."""
    repository = InstitutionRepository(db["institutions"])
    row = await repository.get(institution_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such institution."
        )
    return _institution_out(row)


@router.get(
    "/{institution_id}/programmes",
    response_model=list[ProgrammeIntakeOut],
    summary="List the sanctioned programmes of an institution",
)
async def list_programmes(
    institution_id: str,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> list[ProgrammeIntakeOut]:
    """List the AICTE-sanctioned capacity of every programme of an institution."""
    repository = ProgrammeRepository(db["programmes"])
    rows = await repository.for_institution(institution_id)
    return [_programme_out(row) for row in rows]


@router.post(
    "/programmes",
    response_model=ProgrammeIntakeOut,
    status_code=status.HTTP_201_CREATED,
    summary="Declare the sanctioned capacity of a programme",
)
async def upsert_programme(
    payload: ProgrammeIntakeIn,
    request: Request,
    principal: Principal = Depends(
        require_permission(rbac.Permission.VIEW_COMPLIANCE_MATRIX)
    ),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> ProgrammeIntakeOut:
    """Create or update a programme's sanctioned capacity."""
    principal.require_scope(payload.institution_id)
    institutions = InstitutionRepository(db["institutions"])
    if await institutions.get(payload.institution_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The institution does not exist in the registry.",
        )

    repository = ProgrammeRepository(db["programmes"])
    stored = await repository.upsert(payload.model_dump())

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="UPSERT_PROGRAMME_CAPACITY",
        subject=f"{payload.institution_id}/{payload.program_id}",
        details=(
            f"Sanctioned intake {payload.approved_intake}, supernumerary "
            f"NRI {payload.max_supernumerary_nri}, OCI/FN {payload.max_supernumerary_fn_oci}, "
            f"TFW {payload.max_supernumerary_tfw}, PMSSS {payload.max_pmsss} "
            f"for {payload.academic_year} (policy {payload.policy_version})."
        ),
        category="INTAKE",
        ip_address=client_ip(request),
    )
    return _programme_out(stored)


@router.get(
    "/{institution_id}/summary",
    summary="An institution's own dashboard summary",
)
async def institution_summary(
    institution_id: str,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    """A compact summary used by the institution portal."""
    principal.require_scope(institution_id)
    programmes = await ProgrammeRepository(db["programmes"]).for_institution(institution_id)
    students = await StudentRepository(db["students"]).all(
        institution_id=institution_id, limit=100000
    )
    active = [row for row in students if row.get("record_status") == "ACTIVE"]
    return {
        "institution_id": institution_id,
        "programmes": len(programmes),
        "students": len(students),
        "active_students": len(active),
        "approved_intake": sum(row.get("approved_intake", 0) for row in programmes),
        "total_sanctioned": sum(row.get("total_sanctioned", 0) for row in programmes),
        "flagged": sum(
            1 for row in active if row.get("verification_status") == "FLAGGED_ANOMALY"
        ),
    }


@router.post(
    "/register",
    summary="Register a school or college on ChhatraLekha",
    status_code=status.HTTP_201_CREATED,
)
async def register_institution(
    payload: InstitutionRegisterIn,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    """Submit an institution registration request (School or College)."""
    import secrets
    from datetime import datetime, timezone

    prefix = "SCH" if payload.category == InstitutionCategory.SCHOOL else "COL"
    clean_city = payload.city.strip()[:3].upper()
    institution_id = f"{prefix}-{clean_city}-{secrets.token_hex(4).upper()}"
    now = datetime.now(timezone.utc)

    # 1. Store institution record with PENDING_REVIEW status
    inst_doc = {
        "_id": institution_id,
        "institution_id": institution_id,
        "name": payload.name,
        "category": payload.category.value,
        "institution_type": payload.institution_type.upper(),
        "state": payload.state,
        "city": payload.city,
        "address": payload.address,
        "affiliation_university": payload.affiliation,
        "email": payload.contact_email,
        "phone": payload.contact_phone,
        "verification_status": InstitutionVerificationStatus.PENDING_REVIEW.value,
        "is_active": False,
        "created_at": now,
    }
    await db["institutions"].insert_one(inst_doc)

    # 2. Provision initial institution admin account
    user_id = f"USR-{secrets.token_hex(6)}"
    pw_hash = hash_password(payload.admin_password)
    admin_user = {
        "_id": user_id,
        "user_id": user_id,
        "email": payload.contact_email,
        "full_name": payload.admin_name,
        "role": "institution_admin",
        "institution_id": institution_id,
        "password_hash": pw_hash,
        "is_active": True,
        "created_at": now,
    }
    await db["users"].insert_one(admin_user)

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=user_id,
        actor_role="institution_admin",
        action="REGISTER_INSTITUTION",
        subject=institution_id,
        details=f"Registered {payload.category.value} '{payload.name}' in {payload.city}, {payload.state}.",
        category="ONBOARDING",
        ip_address=client_ip(request),
    )

    return {
        "message": "Institution registration submitted. Awaiting verification review.",
        "institution_id": institution_id,
        "name": payload.name,
        "category": payload.category.value,
        "verification_status": InstitutionVerificationStatus.PENDING_REVIEW.value,
        "admin_email": payload.contact_email,
    }


@router.post(
    "/{institution_id}/review",
    summary="Platform operator reviews and approves institution onboarding",
)
async def review_institution_onboarding(
    institution_id: str,
    payload: InstitutionReviewIn,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.REVIEW_ANOMALIES)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    """Platform operator verifies and activates or suspends an institution."""
    inst = await db["institutions"].find_one({"institution_id": institution_id})
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found.")

    is_active = (payload.decision == InstitutionVerificationStatus.VERIFIED)
    await db["institutions"].update_one(
        {"institution_id": institution_id},
        {"$set": {
            "verification_status": payload.decision.value,
            "is_active": is_active,
            "reviewed_by": principal.subject,
            "review_notes": payload.notes,
        }},
    )

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="REVIEW_INSTITUTION_ONBOARDING",
        subject=institution_id,
        details=f"Institution {institution_id} review decision: {payload.decision.value}. Notes: {payload.notes}",
        category="ONBOARDING",
        ip_address=client_ip(request),
    )

    return {
        "institution_id": institution_id,
        "verification_status": payload.decision.value,
        "is_active": is_active,
        "notes": payload.notes,
    }
