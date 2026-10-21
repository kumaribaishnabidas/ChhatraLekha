"""Institution and programme-capacity endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import Principal, client_ip, get_principal, require_permission
from app.audit import writer
from app.core import rbac
from app.core.database import get_db
from app.models import Institution, ProgramIntake, Student
from app.schemas.student import InstitutionOut, ProgrammeIntakeIn, ProgrammeIntakeOut

router = APIRouter(prefix="/institutions", tags=["institutions"])


@router.get("", response_model=list[InstitutionOut], summary="List institutions")
async def list_institutions(
    state: Optional[str] = None,
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db),
) -> list[InstitutionOut]:
    """List the AICTE-approved institutions."""
    statement = select(Institution).order_by(Institution.name)
    if state:
        statement = statement.where(Institution.state == state)
    rows = (await session.execute(statement)).scalars().all()
    return [
        InstitutionOut(
            institution_id=row.institution_id,
            name=row.name,
            institution_type=row.institution_type.value,
            state=row.state,
            city=row.city,
            affiliation_university=row.affiliation_university,
            approval_year=row.approval_year,
            naac_grade=row.naac_grade,
            email=row.email,
            phone=row.phone,
            is_active=row.is_active,
        )
        for row in rows
    ]


@router.get(
    "/{institution_id}",
    response_model=InstitutionOut,
    summary="Fetch one institution",
)
async def get_institution(
    institution_id: str,
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db),
) -> InstitutionOut:
    """Fetch a single institution."""
    row = (
        await session.execute(
            select(Institution).where(Institution.institution_id == institution_id)
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such institution."
        )
    return InstitutionOut(
        institution_id=row.institution_id,
        name=row.name,
        institution_type=row.institution_type.value,
        state=row.state,
        city=row.city,
        affiliation_university=row.affiliation_university,
        approval_year=row.approval_year,
        naac_grade=row.naac_grade,
        email=row.email,
        phone=row.phone,
        is_active=row.is_active,
    )


@router.get(
    "/{institution_id}/programmes",
    response_model=list[ProgrammeIntakeOut],
    summary="List the sanctioned programmes of an institution",
)
async def list_programmes(
    institution_id: str,
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db),
) -> list[ProgrammeIntakeOut]:
    """List the AICTE-sanctioned capacity of every programme of an institution."""
    rows = (
        await session.execute(
            select(ProgramIntake)
            .where(ProgramIntake.institution_id == institution_id)
            .order_by(ProgramIntake.program_name)
        )
    ).scalars().all()
    return [ProgrammeIntakeOut.model_validate(row) for row in rows]


@router.post(
    "/programmes",
    response_model=ProgrammeIntakeOut,
    status_code=status.HTTP_201_CREATED,
    summary="Declare the sanctioned capacity of a programme",
)
async def upsert_programme(
    payload: ProgrammeIntakeIn,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.VIEW_COMPLIANCE_MATRIX)),
    session: AsyncSession = Depends(get_db),
) -> ProgrammeIntakeOut:
    """Create or update a programme's sanctioned capacity."""
    principal.require_scope(payload.institution_id)
    institution = (
        await session.execute(
            select(Institution).where(Institution.institution_id == payload.institution_id)
        )
    ).scalar_one_or_none()
    if institution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The institution does not exist in the registry.",
        )

    existing = (
        await session.execute(
            select(ProgramIntake).where(
                ProgramIntake.institution_id == payload.institution_id,
                ProgramIntake.program_id == payload.program_id,
            )
        )
    ).scalar_one_or_none()

    if existing is None:
        existing = ProgramIntake(
            institution_id=payload.institution_id, program_id=payload.program_id
        )
        session.add(existing)

    existing.program_name = payload.program_name
    existing.program_level = payload.program_level
    existing.approved_intake = payload.approved_intake
    existing.max_supernumerary_nri = payload.max_supernumerary_nri
    existing.max_supernumerary_fn_oci = payload.max_supernumerary_fn_oci
    existing.max_supernumerary_tfw = payload.max_supernumerary_tfw
    existing.max_pmsss = payload.max_pmsss
    await session.flush()

    await writer.log(
        session,
        actor=principal.subject,
        actor_role=principal.role,
        action="UPSERT_PROGRAMME_CAPACITY",
        subject=f"{payload.institution_id}/{payload.program_id}",
        details=(
            f"Sanctioned intake {payload.approved_intake}, supernumerary "
            f"NRI {payload.max_supernumerary_nri}, OCI/FN {payload.max_supernumerary_fn_oci}, "
            f"TFW {payload.max_supernumerary_tfw}, PMSSS {payload.max_pmsss}."
        ),
        category="INTAKE",
        ip_address=client_ip(request),
    )
    await session.commit()
    await session.refresh(existing)
    return ProgrammeIntakeOut.model_validate(existing)


@router.get(
    "/{institution_id}/summary",
    summary="An institution's own dashboard summary",
)
async def institution_summary(
    institution_id: str,
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db),
) -> dict:
    """A compact summary used by the institution portal."""
    principal.require_scope(institution_id)
    students = (
        await session.execute(
            select(Student).where(Student.institution_id == institution_id)
        )
    ).scalars().all()
    programs = (
        await session.execute(
            select(ProgramIntake).where(ProgramIntake.institution_id == institution_id)
        )
    ).scalars().all()
    active = [student for student in students if student.is_active]
    return {
        "institution_id": institution_id,
        "programmes": len(programs),
        "students": len(students),
        "active_students": len(active),
        "approved_intake": sum(program.approved_intake for program in programs),
        "total_sanctioned": sum(program.total_sanctioned for program in programs),
        "flagged": sum(
            1
            for student in active
            if student.verification_status.value == "FLAGGED_ANOMALY"
        ),
    }
