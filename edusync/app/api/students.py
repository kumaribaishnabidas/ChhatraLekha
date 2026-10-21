"""Student registry endpoints: CRUD, bulk CSV ingestion and QR badges."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import Principal, client_ip, get_principal, require_permission
from app.audit import writer
from app.core import rbac
from app.core.database import get_db
from app.models import (
    Anomaly,
    Institution,
    ProgramIntake,
    Student,
    VerificationStatus,
)
from app.models.enums import AdmissionQuota
from app.schemas.student import BatchUploadResult, StudentCreate, StudentOut, StudentUpdate
from app.services import apaar_validator, csv_ingestion, pdf, qr, seal
from app.services.anomaly_engine import RegistrySnapshot, engine

router = APIRouter(prefix="/students", tags=["students"])


# ------------------------------------------------------------------ helpers


def _masked(apaar_id: str) -> str:
    return apaar_validator.mask(apaar_id)


def _to_out(student: Student) -> StudentOut:
    out = StudentOut.model_validate(student)
    out.masked_apaar_id = _masked(student.apaar_id)
    return out


def _today() -> str:
    return date.today().isoformat()


async def _load_context(session: AsyncSession) -> RegistrySnapshot:
    institutions = (await session.execute(select(Institution))).scalars().all()
    programs = (await session.execute(select(ProgramIntake))).scalars().all()
    students = (await session.execute(select(Student))).scalars().all()
    return RegistrySnapshot(
        institutions=institutions, programs=programs, students=students
    )


async def _recompute_anomalies(session: AsyncSession) -> list[Anomaly]:
    """Re-run the detection engine and persist the findings."""
    snapshot = await _load_context(session)
    detected = engine.evaluate(snapshot)
    now = datetime.now(timezone.utc)

    for existing in (await session.execute(select(Anomaly))).scalars().all():
        await session.delete(existing)
    await session.flush()

    for finding in detected:
        session.add(
            Anomaly(
                student_apaar_id=finding.student_apaar_id,
                institution_id=finding.institution_id,
                program_id=finding.program_id,
                anomaly_type=finding.anomaly_type,
                severity=finding.severity,
                details=finding.details,
                detected_at=now,
            )
        )

    flagged = {
        finding.student_apaar_id
        for finding in detected
        if finding.severity.name in {"CRITICAL", "HIGH"}
    }
    for student in snapshot.students:
        if student.apaar_id in flagged:
            student.verification_status = VerificationStatus.FLAGGED_ANOMALY
        elif student.verification_status == VerificationStatus.PENDING_REVIEW:
            student.verification_status = VerificationStatus.VERIFIED
    await session.flush()
    return detected


# ------------------------------------------------------------------- routes


@router.get("", response_model=list[StudentOut], summary="List the student register")
async def list_students(
    institution_id: Optional[str] = Query(None),
    program_id: Optional[str] = Query(None),
    quota: Optional[AdmissionQuota] = Query(None),
    flagged_only: bool = Query(False),
    search: Optional[str] = Query(None, max_length=120),
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db),
) -> list[StudentOut]:
    """List enrolments, scoped to the caller's institution unless they are AICTE."""
    statement = select(Student)
    if principal.role == "institution_admin":
        if not principal.institution_id:
            return []
        statement = statement.where(Student.institution_id == principal.institution_id)
    elif principal.institution_id:
        statement = statement.where(Student.institution_id == principal.institution_id)

    if institution_id:
        statement = statement.where(Student.institution_id == institution_id)
    if program_id:
        statement = statement.where(Student.program_id == program_id)
    if quota:
        statement = statement.where(Student.admission_quota == quota)
    if flagged_only:
        statement = statement.where(Student.verification_status == VerificationStatus.FLAGGED_ANOMALY)
    if search:
        pattern = f"%{search.strip()}%"
        statement = statement.where(
            Student.student_name.ilike(pattern) | Student.apaar_id.ilike(pattern)
        )

    statement = statement.order_by(Student.student_name).limit(limit).offset(offset)
    rows = (await session.execute(statement)).scalars().all()
    return [_to_out(row) for row in rows]


@router.get(
    "/{apaar_id}",
    response_model=StudentOut,
    summary="Fetch one enrolment record",
)
async def get_student(
    apaar_id: str,
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db),
) -> StudentOut:
    """Fetch a single enrolment record by APAAR ID."""
    result = await session.execute(select(Student).where(Student.apaar_id == apaar_id))
    student = result.scalars().first()
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such APAAR ID."
        )
    if principal.role != "aicte_admin" and principal.institution_id:
        if student.institution_id != principal.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to access another institution's records.",
            )
    return _to_out(student)


@router.post(
    "",
    response_model=StudentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Onboard a single student",
)
async def create_student(
    payload: StudentCreate,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.ONBOARD_STUDENTS)),
    session: AsyncSession = Depends(get_db),
) -> StudentOut:
    """Create one enrolment record and re-run the detection engine."""
    principal.require_scope(payload.institution_id)

    validation = apaar_validator.validate(payload.apaar_id)
    if not validation.is_structurally_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=validation.errors,
        )

    existing = (
        await session.execute(select(Student).where(Student.apaar_id == payload.apaar_id))
    ).scalars().first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This APAAR ID is already on the register.",
        )

    student = Student(
        apaar_id=payload.apaar_id,
        student_name=payload.student_name,
        date_of_birth=payload.date_of_birth,
        gender=payload.gender,
        institution_id=payload.institution_id,
        program_id=payload.program_id,
        academic_year=payload.academic_year,
        admission_quota=payload.admission_quota,
        enrollment_date=payload.enrollment_date or _today(),
        student_institute_roll_no=payload.student_institute_roll_no
        or f"AUTO-{payload.apaar_id[-4:]}",
        nationality=payload.nationality or "Indian",
        passport_number=payload.passport_number,
        visa_validity=payload.visa_validity,
        country_of_origin=payload.country_of_origin,
        abc_account_id=payload.abc_account_id,
        verification_status=VerificationStatus.PENDING_REVIEW,
        is_active=True,
        social_category=payload.social_category,
        admission_date=payload.admission_date,
        contact_email=payload.contact_email,
        contact_phone=payload.contact_phone,
        state_of_domicile=payload.state_of_domicile,
    )
    session.add(student)
    await session.flush()

    anomalies = await _recompute_anomalies(session)
    await writer.log(
        session,
        actor=principal.subject,
        actor_role=principal.role,
        action="MANUAL_ADMISSION",
        subject=student.apaar_id,
        details=(
            f"Onboarded {student.student_name} into {student.program_id} at "
            f"{student.institution_id}. {len(anomalies)} anomaly record(s) in force."
        ),
        category="ADMISSIONS",
        ip_address=client_ip(request),
    )
    await session.commit()
    await session.refresh(student)
    return _to_out(student)


@router.put(
    "/{apaar_id}",
    response_model=StudentOut,
    summary="Update an enrolment record",
)
async def update_student(
    apaar_id: str,
    payload: StudentUpdate,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.ONBOARD_STUDENTS)),
    session: AsyncSession = Depends(get_db),
) -> StudentOut:
    """Update an enrolment record and re-run the detection engine."""
    result = await session.execute(select(Student).where(Student.apaar_id == apaar_id))
    student = result.scalars().first()
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such APAAR ID."
        )
    principal.require_scope(student.institution_id)

    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(student, field, value)

    await session.flush()
    anomalies = await _recompute_anomalies(session)
    await writer.log(
        session,
        actor=principal.subject,
        actor_role=principal.role,
        action="UPDATE_ADMISSION",
        subject=student.apaar_id,
        details=(
            f"Updated {', '.join(sorted(changes)) or 'no fields'}; "
            f"{len(anomalies)} anomaly record(s) in force."
        ),
        category="ADMISSIONS",
        ip_address=client_ip(request),
    )
    await session.commit()
    await session.refresh(student)
    return _to_out(student)


@router.delete(
    "/{apaar_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate an enrolment record",
)
async def deactivate_student(
    apaar_id: str,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.ONBOARD_STUDENTS)),
    session: AsyncSession = Depends(get_db),
) -> Response:
    """Deactivate (never delete) an enrolment record."""
    result = await session.execute(select(Student).where(Student.apaar_id == apaar_id))
    student = result.scalars().first()
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such APAAR ID."
        )
    principal.require_scope(student.institution_id)
    student.is_active = False
    await session.flush()
    await _recompute_anomalies(session)
    await writer.log(
        session,
        actor=principal.subject,
        actor_role=principal.role,
        action="DEACTIVATE_ADMISSION",
        subject=student.apaar_id,
        details=f"Deactivated {student.student_name}.",
        category="ADMISSIONS",
        ip_address=client_ip(request),
    )
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ----------------------------------------------------------------- bulk CSV


async def _build_context(
    session: AsyncSession, institution_id: str
) -> csv_ingestion.CsvValidationContext:
    """Assemble the validation context from the live registry."""
    programs = (
        await session.execute(
            select(ProgramIntake).where(ProgramIntake.institution_id == institution_id)
        )
    ).scalars().all()
    students = (
        await session.execute(
            select(Student).where(Student.institution_id == institution_id)
        )
    ).scalars().all()

    existing_ids = {student.apaar_id for student in students}
    regular: dict[str, int] = {}
    supernumerary: dict[str, int] = {}
    nri: dict[str, int] = {}
    oci_fn: dict[str, int] = {}
    tfw: dict[str, int] = {}
    pmsss: dict[str, int] = {}
    for student in students:
        key = student.program_id
        if student.admission_quota.is_regular:
            regular[key] = regular.get(key, 0) + 1
        else:
            supernumerary[key] = supernumerary.get(key, 0) + 1
        if student.admission_quota == AdmissionQuota.NRI:
            nri[key] = nri.get(key, 0) + 1
        if student.admission_quota in (AdmissionQuota.OCI, AdmissionQuota.FN):
            oci_fn[key] = oci_fn.get(key, 0) + 1
        if student.admission_quota == AdmissionQuota.TFW:
            tfw[key] = tfw.get(key, 0) + 1
        if student.admission_quota == AdmissionQuota.PMSSS:
            pmsss[key] = pmsss.get(key, 0) + 1

    return csv_ingestion.CsvValidationContext(
        programs=programs,
        existing_apaar_ids=existing_ids,
        existing_regular_counts=regular,
        existing_supernumerary_counts=supernumerary,
        existing_nri_counts=nri,
        existing_oci_fn_counts=oci_fn,
        existing_tfw_counts=tfw,
        existing_pmsss_counts=pmsss,
    )


@router.post(
    "/bulk/preview",
    summary="Validate a batch CSV without committing it",
)
async def preview_bulk(
    request: Request,
    file: UploadFile = File(...),
    institution_id: str = Query(...),
    academic_year: str = Query("2024-25"),
    principal: Principal = Depends(require_permission(rbac.Permission.IMPORT_CSV)),
    session: AsyncSession = Depends(get_db),
) -> dict:
    """Validate an uploaded CSV and report every row-level issue."""
    principal.require_scope(institution_id)
    raw = (await file.read()).decode("utf-8", errors="replace")
    context = await _build_context(session, institution_id)
    report = csv_ingestion.validate_csv(raw, context)
    return {
        "header_errors": report.header_errors,
        "total_rows": report.total_rows,
        "valid_rows": report.valid_rows,
        "critical_rows": report.critical_rows,
        "warning_rows": report.warning_rows,
        "duplicate_rows": report.duplicate_rows,
        "unknown_programs": report.unknown_programs,
        "program_impacts": [
            {
                "program_code": impact.program_code,
                "program_name": impact.program_name,
                "approved_intake": impact.approved_intake,
                "existing_regular": impact.existing_regular,
                "incoming_regular": impact.incoming_regular,
                "existing_supernumerary": impact.existing_supernumerary,
                "incoming_supernumerary": impact.incoming_supernumerary,
                "projected_regular": impact.projected_regular,
                "projected_total": impact.projected_total,
                "regular_overflow": impact.regular_overflow,
                "cap_messages": impact.cap_messages,
            }
            for impact in report.program_impacts
        ],
        "rows": [
            {
                "line_number": row.line_number,
                "apaar_id": row.apaar_id,
                "full_name": row.full_name,
                "program_code": row.program_code,
                "category": row.category,
                "issues": [
                    {
                        "code": issue.code,
                        "severity": issue.severity.value,
                        "message": issue.message,
                    }
                    for issue in row.issues
                ],
            }
            for row in report.rows
        ],
    }


@router.post(
    "/bulk/commit",
    response_model=BatchUploadResult,
    summary="Commit a validated batch CSV",
)
async def commit_bulk(
    request: Request,
    file: UploadFile = File(...),
    institution_id: str = Query(...),
    academic_year: str = Query("2024-25"),
    principal: Principal = Depends(require_permission(rbac.Permission.IMPORT_CSV)),
    session: AsyncSession = Depends(get_db),
) -> BatchUploadResult:
    """Commit the committable rows of an uploaded CSV to the registry."""
    principal.require_scope(institution_id)
    raw = (await file.read()).decode("utf-8", errors="replace")
    context = await _build_context(session, institution_id)
    report = csv_ingestion.validate_csv(raw, context)

    if report.header_errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=report.header_errors
        )

    committable = report.committable_rows
    committed = 0
    for row in committable:
        quota = row.quota or AdmissionQuota.MERIT
        session.add(
            Student(
                apaar_id=row.apaar_id,
                student_name=row.full_name,
                date_of_birth=row.dob,
                gender=_gender_or_other(row.gender),
                institution_id=institution_id,
                program_id=row.program_code,
                academic_year=row.academic_year or academic_year,
                admission_quota=quota,
                enrollment_date=_today(),
                student_institute_roll_no=row.roll_no
                or f"AUTO-{row.apaar_id[-4:]}",
                nationality=row.nationality or "Indian",
                passport_number=row.doc_number or None,
                verification_status=VerificationStatus.PENDING_REVIEW,
                is_active=True,
                social_category=_social_or_general(row.social_category),
                admission_date=row.admission_date or None,
                contact_email=row.contact_email or None,
                contact_phone=row.contact_phone or None,
                state_of_domicile=row.state_of_domicile or None,
            )
        )
        committed += 1
    await session.flush()

    anomalies = await _recompute_anomalies(session)
    await writer.log(
        session,
        actor=principal.subject,
        actor_role=principal.role,
        action="BATCH_COMMIT",
        subject=institution_id,
        details=(
            f"Committed {committed} of {report.total_rows} CSV rows; "
            f"{len(anomalies)} anomaly record(s) in force."
        ),
        category="ADMISSIONS",
        ip_address=client_ip(request),
    )
    await session.commit()

    return BatchUploadResult(
        total_rows=report.total_rows,
        committed=committed,
        skipped=report.total_rows - committed,
        critical_rows=report.critical_rows,
        warning_rows=report.warning_rows,
        duplicate_rows=report.duplicate_rows,
        unknown_programs=report.unknown_programs,
        anomalies_detected=len(anomalies),
        program_impacts=[
            {
                "program_code": impact.program_code,
                "projected_regular": impact.projected_regular,
                "cap_messages": impact.cap_messages,
            }
            for impact in report.program_impacts
        ],
    )


def _gender_or_other(raw: str):
    from app.models.enums import Gender

    return Gender.from_code(raw) or Gender.OTHER


def _social_or_general(raw: str):
    from app.models.enums import SocialCategory

    return SocialCategory.from_code(raw) or SocialCategory.GENERAL


# ------------------------------------------------------------------- badges


@router.get("/{apaar_id}/qr", summary="The APAAR QR badge of a student")
async def student_qr(
    apaar_id: str,
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Render the APAAR QR badge of a student as a PNG image."""
    result = await session.execute(select(Student).where(Student.apaar_id == apaar_id))
    student = result.scalars().first()
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such APAAR ID."
        )
    if principal.role != "aicte_admin" and principal.institution_id:
        if student.institution_id != principal.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to access another institution's records.",
            )

    payload = seal.CredentialPayload(
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
        issued_at=int(datetime.now(timezone.utc).timestamp()),
    )
    signed = seal.sign(payload)
    link = qr.build_payload(
        apaar_id=student.apaar_id,
        institution_id=student.institution_id,
        program_id=student.program_id,
        seal=signed,
        timestamp=payload.issued_at,
    )
    png = qr.render_png(link)
    return StreamingResponse(
        iter([png]), media_type="image/png", headers={"Content-Disposition": "inline"}
    )


@router.get(
    "/{apaar_id}/certificate.pdf",
    summary="The APAAR certificate of a student",
)
async def student_certificate(
    apaar_id: str,
    request: Request,
    certificate_type: str = Query("Bonafide Certificate", max_length=80),
    principal: Principal = Depends(require_permission(rbac.Permission.GENERATE_CERTIFICATE)),
    session: AsyncSession = Depends(get_db),
) -> Response:
    """Issue a certificate that carries the APAAR ID, the student id and the QR badge."""
    result = await session.execute(select(Student).where(Student.apaar_id == apaar_id))
    student = result.scalars().first()
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such APAAR ID."
        )
    if principal.role != "aicte_admin" and principal.institution_id:
        if student.institution_id != principal.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to issue a certificate for another institution.",
            )

    institution = (
        await session.execute(
            select(Institution).where(Institution.institution_id == student.institution_id)
        )
    ).scalar_one_or_none()
    program = (
        await session.execute(
            select(ProgramIntake).where(
                ProgramIntake.institution_id == student.institution_id,
                ProgramIntake.program_id == student.program_id,
            )
        )
    ).scalar_one_or_none()

    payload = seal.CredentialPayload(
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
    signed = seal.sign(payload)
    link = qr.build_payload(
        apaar_id=student.apaar_id,
        institution_id=student.institution_id,
        program_id=student.program_id,
        seal=signed,
        timestamp=int(datetime.now(timezone.utc).timestamp()),
    )
    png = qr.render_png(link)

    body = pdf.build_certificate_pdf(
        student=student,
        institution_name=institution.name if institution else student.institution_id,
        program_name=program.program_name if program else student.program_id,
        academic_year=student.academic_year,
        apaar_id=student.apaar_id,
        qr_png=png,
        seal_text=signed,
        certificate_type=certificate_type,
    )

    await writer.log(
        session,
        actor=principal.subject,
        actor_role=principal.role,
        action="ISSUE_CERTIFICATE",
        subject=student.apaar_id,
        details=f"Issued '{certificate_type}' for {student.student_name}.",
        category="CREDENTIAL",
        ip_address=client_ip(request),
    )
    await session.commit()

    filename = f"edusync-certificate-{student.apaar_id}.pdf"
    return Response(
        content=body,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
