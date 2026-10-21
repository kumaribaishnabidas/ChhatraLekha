"""Student registry endpoints: CRUD, bulk CSV ingestion, QR badges, certificates."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
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
from app.core.config import get_settings
from app.models.documents import Doc
from app.models.enums import Gender, SocialCategory
from app.repositories.audit import AuditRepository
from app.repositories.programmes import ProgrammeRepository
from app.repositories.students import StudentRepository
from app.repositories.submissions import SubmissionRepository
from app.schemas.student import BatchUploadResult, StudentCreate, StudentOut, StudentUpdate
from app.services import apaar_validator, csv_ingestion, pdf, qr, seal
from app.services.registry import recompute_anomalies

router = APIRouter(prefix="/students", tags=["students"])

settings = get_settings()


# ------------------------------------------------------------------ helpers


def _to_out(student: Doc) -> StudentOut:
    """Build the response model from a stored document."""
    return StudentOut(
        record_id=str(student.get("_id", "")),
        apaar_id=student.get("apaar_id", ""),
        student_name=student.get("student_name", ""),
        date_of_birth=student.get("date_of_birth", ""),
        gender=Gender.from_code(student.get("gender")) or Gender.OTHER,
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


def _today() -> str:
    return date.today().isoformat()


def _payload_for(student: Doc) -> seal.CredentialPayload:
    """The credential payload the seal commits to."""
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


async def _validation_context(
    db: AsyncIOMotorDatabase, institution_id: str
) -> csv_ingestion.CsvValidationContext:
    """Assemble the batch-validation context from the live registry."""
    programmes = ProgrammeRepository(db["programmes"])
    students = StudentRepository(db["students"])

    program_docs = await programmes.for_institution(institution_id)
    existing_ids = await students.existing_apaar_ids(institution_id)
    counts = await students.seat_counts(institution_id)

    regular: dict[str, int] = {}
    supernumerary: dict[str, int] = {}
    nri: dict[str, int] = {}
    oci_fn: dict[str, int] = {}
    tfw: dict[str, int] = {}
    pmsss: dict[str, int] = {}

    for program_id, buckets in counts.items():
        for quota, count in buckets.items():
            if quota in {"MERIT", "MANAGEMENT", "PMSSS"}:
                regular[program_id] = regular.get(program_id, 0) + count
            else:
                supernumerary[program_id] = supernumerary.get(program_id, 0) + count
            if quota == "NRI":
                nri[program_id] = nri.get(program_id, 0) + count
            if quota in {"OCI", "FN"}:
                oci_fn[program_id] = oci_fn.get(program_id, 0) + count
            if quota == "TFW":
                tfw[program_id] = tfw.get(program_id, 0) + count
            if quota == "PMSSS":
                pmsss[program_id] = pmsss.get(program_id, 0) + count

    return csv_ingestion.CsvValidationContext(
        programs=program_docs,
        existing_apaar_ids=existing_ids,
        existing_regular_counts=regular,
        existing_supernumerary_counts=supernumerary,
        existing_nri_counts=nri,
        existing_oci_fn_counts=oci_fn,
        existing_tfw_counts=tfw,
        existing_pmsss_counts=pmsss,
    )


# ------------------------------------------------------------------- routes


@router.get("", response_model=list[StudentOut], summary="List the student register")
async def list_students(
    institution_id: Optional[str] = Query(None),
    program_id: Optional[str] = Query(None),
    quota: Optional[str] = Query(None),
    record_status: Optional[str] = Query(None),
    search: Optional[str] = Query(None, max_length=120),
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> list[StudentOut]:
    """List enrolments, scoped to the caller's institution unless they are AICTE."""
    students = StudentRepository(db["students"])

    if principal.role != "aicte_admin" and principal.institution_id:
        institution_id = principal.institution_id

    # The working register shows the active records; a withdrawn enrolment
    # stays in the registry and is reachable through the explicit filter.
    if record_status and record_status.upper() != "ALL":
        record_status = record_status.upper()

    rows = await students.all(
        institution_id=institution_id,
        program_id=program_id,
        quota=quota,
        record_status=None if record_status == "ALL" else (record_status or "ACTIVE"),
        search=search,
        limit=limit,
        offset=offset,
    )
    return [_to_out(row) for row in rows]


@router.get(
    "/{apaar_id}",
    response_model=StudentOut,
    summary="Fetch one enrolment record",
)
async def get_student(
    apaar_id: str,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> StudentOut:
    """Fetch a single enrolment record by APAAR ID."""
    students = StudentRepository(db["students"])
    student = await students.get(apaar_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such APAAR ID."
        )
    if principal.role != "aicte_admin" and principal.institution_id:
        if student.get("institution_id") != principal.institution_id:
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
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> StudentOut:
    """Create one enrolment record and re-run the detection engine."""
    principal.require_scope(payload.institution_id)

    validation = apaar_validator.validate(payload.apaar_id)
    if not validation.is_structurally_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=validation.errors,
        )

    students = StudentRepository(db["students"])
    existing = await students.get(payload.apaar_id)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This APAAR ID is already on the register.",
        )

    document = {
        "apaar_id": payload.apaar_id,
        "student_name": payload.student_name,
        "date_of_birth": payload.date_of_birth,
        "gender": payload.gender.value,
        "institution_id": payload.institution_id,
        "program_id": payload.program_id,
        "academic_year": payload.academic_year,
        "admission_quota": payload.admission_quota.value,
        "enrollment_date": payload.enrollment_date or _today(),
        "student_institute_roll_no": payload.student_institute_roll_no
        or f"AUTO-{payload.apaar_id[-4:]}",
        "nationality": payload.nationality or "Indian",
        "passport_number": payload.passport_number,
        "visa_validity": payload.visa_validity,
        "country_of_origin": payload.country_of_origin,
        "abc_account_id": payload.abc_account_id,
        "verification_status": "PENDING_REVIEW",
        "is_active": True,
        "record_status": "ACTIVE",
        "submission_source": "MANUAL",
        "social_category": payload.social_category.value,
        "admission_date": payload.admission_date,
        "contact_email": payload.contact_email,
        "contact_phone": payload.contact_phone,
        "state_of_domicile": payload.state_of_domicile,
    }
    stored = await students.insert(document)
    await recompute_anomalies(db)

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="MANUAL_ADMISSION",
        subject=stored.get("apaar_id", ""),
        details=(
            f"Onboarded {stored.get('student_name')} into {stored.get('program_id')} "
            f"at {stored.get('institution_id')}."
        ),
        category="ADMISSIONS",
        ip_address=client_ip(request),
    )
    return _to_out(stored)


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
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> StudentOut:
    """Update an enrolment record and re-run the detection engine."""
    students = StudentRepository(db["students"])
    student = await students.get(apaar_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such APAAR ID."
        )
    principal.require_scope(student.get("institution_id", ""))

    changes = payload.model_dump(exclude_unset=True)
    for field, value in list(changes.items()):
        if hasattr(value, "value"):
            changes[field] = value.value

    updated = await students.update(apaar_id, changes)
    await recompute_anomalies(db)

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="UPDATE_ADMISSION",
        subject=apaar_id,
        details=f"Updated {', '.join(sorted(changes)) or 'no fields'}.",
        category="ADMISSIONS",
        ip_address=client_ip(request),
    )
    return _to_out(updated)


@router.delete(
    "/{apaar_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate an enrolment record",
)
async def deactivate_student(
    apaar_id: str,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.ONBOARD_STUDENTS)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> Response:
    """Deactivate (never delete) an enrolment record."""
    students = StudentRepository(db["students"])
    student = await students.get(apaar_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such APAAR ID."
        )
    principal.require_scope(student.get("institution_id", ""))
    await students.set_record_status(apaar_id, "WITHDRAWN")
    await recompute_anomalies(db)
    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="DEACTIVATE_ADMISSION",
        subject=apaar_id,
        details=f"Withdrew the enrolment of {student.get('student_name')}.",
        category="ADMISSIONS",
        ip_address=client_ip(request),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ----------------------------------------------------------------- bulk CSV


@router.post("/bulk/preview", summary="Validate a batch CSV without committing it")
async def preview_bulk(
    request: Request,
    file: UploadFile = File(...),
    institution_id: str = Query(...),
    academic_year: str = Query("2024-25"),
    principal: Principal = Depends(require_permission(rbac.Permission.IMPORT_CSV)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    """Validate an uploaded CSV and report every row-level issue.

    The preview never writes: it tells the institution exactly which rows
    would be accepted, quarantined or rejected, and what the batch would do
    to the programme's seat count.
    """
    principal.require_scope(institution_id)
    raw = (await file.read()).decode("utf-8", errors="replace")
    context = await _validation_context(db, institution_id)
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
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> BatchUploadResult:
    """Commit the accepted rows of an uploaded CSV to the registry.

    Rows that failed validation are **quarantined**, not silently dropped:
    the count of every outcome is reported and the batch is recorded in the
    submissions history.
    """
    principal.require_scope(institution_id)
    raw = (await file.read()).decode("utf-8", errors="replace")
    context = await _validation_context(db, institution_id)
    report = csv_ingestion.validate_csv(raw, context)

    if report.header_errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=report.header_errors
        )

    students = StudentRepository(db["students"])
    documents: list[dict[str, Any]] = []
    for row in report.committable_rows:
        quota = row.quota
        documents.append(
            {
                "apaar_id": row.apaar_id,
                "student_name": row.full_name,
                "date_of_birth": row.dob,
                "gender": _gender_or_other(row.gender),
                "institution_id": institution_id,
                "program_id": row.program_code,
                "academic_year": row.academic_year or academic_year,
                "admission_quota": quota.value if quota else "MERIT",
                "enrollment_date": _today(),
                "student_institute_roll_no": row.roll_no
                or f"AUTO-{row.apaar_id[-4:]}",
                "nationality": row.nationality or "Indian",
                "passport_number": row.doc_number or None,
                "verification_status": "PENDING_REVIEW",
                "is_active": True,
                "record_status": "ACTIVE",
                "submission_source": "CSV_UPLOAD",
                "social_category": _social_or_general(row.social_category),
                "admission_date": row.admission_date or None,
                "contact_email": row.contact_email or None,
                "contact_phone": row.contact_phone or None,
                "state_of_domicile": row.state_of_domicile or None,
            }
        )
    inserted = await students.insert_many(documents)
    anomalies = await recompute_anomalies(db)

    submissions = SubmissionRepository(db["submissions"])
    await submissions.insert(
        {
            "submission_id": f"SUB-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            "institution_id": institution_id,
            "submitted_by": principal.subject,
            "filename": file.filename or "batch.csv",
            "total_rows": report.total_rows,
            "accepted_rows": len(inserted),
            "quarantined_rows": report.critical_rows,
            "rejected_rows": 0,
            "warning_rows": report.warning_rows,
            "anomalies_detected": len(anomalies),
            "status": "COMMITTED",
        }
    )

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="BATCH_COMMIT",
        subject=institution_id,
        details=(
            f"Committed {len(inserted)} of {report.total_rows} CSV rows; "
            f"{report.critical_rows} row(s) quarantined."
        ),
        category="ADMISSIONS",
        ip_address=client_ip(request),
    )

    return BatchUploadResult(
        total_rows=report.total_rows,
        committed=len(inserted),
        skipped=report.total_rows - len(inserted),
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


def _gender_or_other(raw: str) -> str:
    gender = Gender.from_code(raw)
    return (gender or Gender.OTHER).value


def _social_or_general(raw: str) -> str:
    social = SocialCategory.from_code(raw)
    return (social or SocialCategory.GENERAL).value


# ------------------------------------------------------------------- badges


@router.get("/{apaar_id}/qr", summary="The APAAR QR badge of a student")
async def student_qr(
    apaar_id: str,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> StreamingResponse:
    """Render the APAAR QR badge of a student as a PNG image."""
    students = StudentRepository(db["students"])
    student = await students.get(apaar_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such APAAR ID."
        )
    if principal.role != "aicte_admin" and principal.institution_id:
        if student.get("institution_id") != principal.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to access another institution's records.",
            )

    payload = _payload_for(student)
    signed = seal.sign(payload)
    link = qr.build_payload(
        apaar_id=student.get("apaar_id", ""),
        institution_id=student.get("institution_id", ""),
        program_id=student.get("program_id", ""),
        seal=signed,
        timestamp=int(datetime.now(timezone.utc).timestamp()),
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
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> Response:
    """Issue a certificate that carries the APAAR ID, the student id and the QR badge."""
    students = StudentRepository(db["students"])
    student = await students.get(apaar_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such APAAR ID."
        )
    if principal.role != "aicte_admin" and principal.institution_id:
        if student.get("institution_id") != principal.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to issue a certificate for another institution.",
            )

    institutions = await db["institutions"].find_one(
        {"institution_id": student.get("institution_id")}
    )
    programme = await db["programmes"].find_one(
        {
            "institution_id": student.get("institution_id"),
            "program_id": student.get("program_id"),
        }
    )

    payload = _payload_for(student)
    signed = seal.sign(payload)
    link = qr.build_payload(
        apaar_id=student.get("apaar_id", ""),
        institution_id=student.get("institution_id", ""),
        program_id=student.get("program_id", ""),
        seal=signed,
        timestamp=int(datetime.now(timezone.utc).timestamp()),
    )
    png = qr.render_png(link)

    body = pdf.build_certificate_pdf(
        student=student,
        institution_name=(institutions or {}).get("name", student.get("institution_id", "")),
        program_name=(programme or {}).get("program_name", student.get("program_id", "")),
        academic_year=student.get("academic_year", ""),
        apaar_id=student.get("apaar_id", ""),
        qr_png=png,
        seal_text=signed,
        certificate_type=certificate_type,
    )

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="ISSUE_CERTIFICATE",
        subject=student.get("apaar_id", ""),
        details=f"Issued '{certificate_type}' for {student.get('student_name')}.",
        category="CREDENTIAL",
        ip_address=client_ip(request),
    )

    filename = f"edusync-certificate-{student.get('apaar_id')}.pdf"
    return Response(
        content=body,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
