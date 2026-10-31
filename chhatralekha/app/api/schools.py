"""School-specific workflows: bulk import, grade promotion, transfer certificates, and analytics."""

from __future__ import annotations

import csv
import io
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field

from app.api.deps import (
    Principal,
    get_audit_repo,
    get_db,
    get_student_repo,
    require_any_permission,
    require_permission,
)
from app.audit import writer
from app.core.rbac import Permission
from app.models.enums import (
    CredentialType,
    Gender,
)
from app.schemas.student import StudentCreate

router = APIRouter(prefix="/schools", tags=["schools"])


class SchoolStudentRow(BaseModel):
    student_name: str = Field(..., max_length=255)
    grade_level: str = Field(..., max_length=32)
    section: str = Field("A", max_length=16)
    date_of_birth: str = Field(..., max_length=32)
    gender: str = Field("M", max_length=16)
    student_institute_roll_no: str = Field(..., max_length=64)
    guardian_name: str = Field(..., max_length=255)
    guardian_contact: str = Field(..., max_length=40)
    guardian_relationship: str = Field("PARENT", max_length=32)
    apaar_id: Optional[str] = None
    stream: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None


class SchoolBulkPreviewOut(BaseModel):
    total_rows: int
    valid_rows: int
    invalid_rows: int
    errors: list[dict[str, Any]]
    sample_preview: list[dict[str, Any]]


class SchoolBulkCommitIn(BaseModel):
    institution_id: str
    academic_year: str = "2025-26"
    students: list[SchoolStudentRow]


class PromotionRequestIn(BaseModel):
    institution_id: str
    current_academic_year: str
    target_academic_year: str
    from_grade: str
    to_grade: str
    student_ids: list[str] = []


class TransferCertificateIn(BaseModel):
    institution_id: str
    student_record_id: str
    reason: str = Field(..., max_length=255)
    conduct_remarks: str = Field("Good", max_length=255)
    destination_school: Optional[str] = None


class TransferCertificateOut(BaseModel):
    tc_number: str
    student_name: str
    grade_level: str
    institution_id: str
    issue_date: str
    verification_token: str
    verification_url: str
    seal: str


@router.get("/template")
async def get_school_csv_template():
    """Return the canonical CSV header structure for school student batch onboarding."""
    headers = [
        "student_name",
        "grade_level",
        "section",
        "date_of_birth",
        "gender",
        "student_institute_roll_no",
        "guardian_name",
        "guardian_contact",
        "guardian_relationship",
        "apaar_id",
        "stream",
        "contact_phone",
        "contact_email",
    ]
    return {
        "headers": headers,
        "sample_row": {
            "student_name": "Aarav Sharma",
            "grade_level": "Class 10",
            "section": "A",
            "date_of_birth": "2010-05-15",
            "gender": "M",
            "student_institute_roll_no": "1001",
            "guardian_name": "Rajesh Sharma",
            "guardian_contact": "+919876543210",
            "guardian_relationship": "FATHER",
            "apaar_id": "",
            "stream": "General",
            "contact_phone": "+919876543210",
            "contact_email": "",
        },
    }


@router.post("/students/bulk-preview", response_model=SchoolBulkPreviewOut)
async def preview_school_csv(
    file: UploadFile,
    principal: Principal = Depends(require_permission(Permission.IMPORT_CSV)),
):
    """Validate uploaded school student CSV, returning errors and formatted previews without saving."""
    content = await file.read()
    decoded = content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(decoded))

    total = 0
    valid = 0
    errors: list[dict[str, Any]] = []
    preview: list[dict[str, Any]] = []

    for idx, row in enumerate(reader, start=1):
        total += 1
        row_errors = []
        name = row.get("student_name", "").strip()
        grade = row.get("grade_level", "").strip()
        dob = row.get("date_of_birth", "").strip()
        roll = row.get("student_institute_roll_no", "").strip()
        guardian = row.get("guardian_name", "").strip()
        guardian_contact = row.get("guardian_contact", "").strip()

        if not name:
            row_errors.append("Missing student_name")
        if not grade:
            row_errors.append("Missing grade_level")
        if not dob:
            row_errors.append("Missing date_of_birth")
        if not roll:
            row_errors.append("Missing student_institute_roll_no")
        if not guardian or not guardian_contact:
            row_errors.append("Mandatory parent/guardian contact details missing for minor student")

        if row_errors:
            errors.append({"line": idx, "row": {k: v for k, v in row.items() if k != "date_of_birth"}, "errors": row_errors})
        else:
            valid += 1
            if len(preview) < 5:
                preview.append({
                    "student_name": name,
                    "grade_level": grade,
                    "section": row.get("section", "A"),
                    "student_institute_roll_no": roll,
                    "guardian_name": guardian,
                })

    return SchoolBulkPreviewOut(
        total_rows=total,
        valid_rows=valid,
        invalid_rows=len(errors),
        errors=errors,
        sample_preview=preview,
    )


@router.post("/students/bulk-commit")
async def commit_school_students(
    body: SchoolBulkCommitIn,
    principal: Principal = Depends(require_permission(Permission.ONBOARD_STUDENTS)),
    student_repo=Depends(get_student_repo),
    audit_repo=Depends(get_audit_repo),
    db=Depends(get_db),
):
    """Commit validated school students into the registry."""
    principal.require_scope(body.institution_id)

    committed = 0
    for row in body.students:
        apaar = row.apaar_id or f"CL-SCH-{uuid.uuid4().hex[:10].upper()}"
        gender_val = Gender.MALE if row.gender.upper().startswith("M") else (
            Gender.FEMALE if row.gender.upper().startswith("F") else Gender.OTHER
        )
        student_data = StudentCreate(
            apaar_id=apaar,
            student_name=row.student_name,
            date_of_birth=row.date_of_birth,
            gender=gender_val,
            institution_id=body.institution_id,
            program_id=f"GRADE-{row.grade_level.replace(' ', '-').upper()}",
            academic_year=body.academic_year,
            student_institute_roll_no=row.student_institute_roll_no,
            contact_email=row.contact_email,
            contact_phone=row.contact_phone or row.guardian_contact,
            grade_level=row.grade_level,
            section=row.section,
            stream=row.stream,
            guardian_name=row.guardian_name,
            guardian_relationship=row.guardian_relationship,
            guardian_contact=row.guardian_contact,
            is_minor=True,
        )

        doc = student_data.model_dump()
        doc["is_active"] = True
        doc["verification_status"] = "VERIFIED"
        doc["record_status"] = "ACTIVE"
        doc["created_at"] = datetime.now(timezone.utc)
        doc["updated_at"] = datetime.now(timezone.utc)

        await db["students"].update_one(
            {"institution_id": body.institution_id, "student_institute_roll_no": row.student_institute_roll_no, "academic_year": body.academic_year},
            {"$set": doc},
            upsert=True,
        )
        committed += 1

    await writer.log(
        audit_repo,
        actor=principal.subject,
        action="CSV_IMPORT_COMMITTED",
        subject=body.institution_id,
        details=f"Committed {committed} students for academic year {body.academic_year}",
        category="STUDENT_REGISTRY",
    )

    return {"message": f"Successfully enrolled {committed} school students.", "committed": committed}


@router.post("/promotions")
async def promote_students(
    body: PromotionRequestIn,
    principal: Principal = Depends(require_permission(Permission.ONBOARD_STUDENTS)),
    audit_repo=Depends(get_audit_repo),
    db=Depends(get_db),
):
    """Promote an entire grade or selected students to the subsequent academic year."""
    principal.require_scope(body.institution_id)

    query: dict[str, Any] = {
        "institution_id": body.institution_id,
        "academic_year": body.current_academic_year,
        "grade_level": body.from_grade,
        "is_active": True,
    }
    if body.student_ids:
        query["apaar_id"] = {"$in": body.student_ids}

    cursor = db["students"].find(query)
    students = await cursor.to_list(length=1000)

    promoted_count = 0
    for st in students:
        # Mark previous record as PROMOTED
        await db["students"].update_one(
            {"_id": st["_id"]},
            {"$set": {"record_status": "PROMOTED", "updated_at": datetime.now(timezone.utc)}},
        )

        # Insert new academic year enrolment record
        new_record = dict(st)
        new_record.pop("_id", None)
        new_record["academic_year"] = body.target_academic_year
        new_record["grade_level"] = body.to_grade
        new_record["program_id"] = f"GRADE-{body.to_grade.replace(' ', '-').upper()}"
        new_record["record_status"] = "ACTIVE"
        new_record["created_at"] = datetime.now(timezone.utc)
        new_record["updated_at"] = datetime.now(timezone.utc)

        await db["students"].insert_one(new_record)
        promoted_count += 1

    await writer.log(
        audit_repo,
        actor=principal.subject,
        action="STUDENT_PROMOTION",
        subject=body.institution_id,
        details=f"Promoted {promoted_count} students from {body.from_grade} to {body.to_grade}",
        category="STUDENT_REGISTRY",
    )

    return {
        "message": f"Promoted {promoted_count} students from {body.from_grade} to {body.to_grade}.",
        "promoted_count": promoted_count,
    }


@router.post("/transfers/issue-tc", response_model=TransferCertificateOut)
async def issue_transfer_certificate(
    body: TransferCertificateIn,
    principal: Principal = Depends(require_permission(Permission.GENERATE_CERTIFICATE)),
    audit_repo=Depends(get_audit_repo),
    db=Depends(get_db),
):
    """Issue an official school Transfer Certificate (TC) with opaque verification token and seal."""
    principal.require_scope(body.institution_id)

    st = await db["students"].find_one({
        "institution_id": body.institution_id,
        "$or": [{"_id": body.student_record_id}, {"apaar_id": body.student_record_id}],
    })
    if not st:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student record not found.")

    tc_no = f"TC-{st.get('academic_year', '2025-26')}-{uuid.uuid4().hex[:8].upper()}"
    raw_token = uuid.uuid4().hex
    import hashlib
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    # Create verification token allowlist entry
    now = datetime.now(timezone.utc)
    from datetime import timedelta
    await db["verification_tokens"].insert_one({
        "token_hash": token_hash,
        "token_type": CredentialType.TRANSFER_CERTIFICATE.value,
        "institution_id": body.institution_id,
        "student_apaar_id": st.get("apaar_id"),
        "grade_level": st.get("grade_level", ""),
        "created_at": now,
        "expires_at": now + timedelta(days=365 * 5),  # 5-year validity for school TCs
        "is_active": True,
        "metadata": {
            "tc_number": tc_no,
            "destination_school": body.destination_school,
            "conduct_remarks": body.conduct_remarks,
        },
    })

    # Update student status to TRANSFERRED
    await db["students"].update_one(
        {"_id": st["_id"]},
        {"$set": {"record_status": "TRANSFERRED", "updated_at": now}},
    )

    # Compute tamper-evident seal
    from app.services import seal
    payload = seal.CredentialPayload(
        apaar_id=st.get("apaar_id", "CL-0000"),
        institution_id=body.institution_id,
        program_id=st.get("grade_level", "SCHOOL"),
        academic_year=st.get("academic_year", "2025-26"),
        enrollment_date=st.get("enrollment_date", now.strftime("%Y-%m-%d")),
        student_name=st.get("student_name", ""),
        date_of_birth=st.get("date_of_birth", ""),
        gender=st.get("gender", "O"),
        admission_quota="REGULAR_MERIT",
        nationality=st.get("nationality", "Indian"),
        student_institute_roll_no=st.get("student_institute_roll_no", ""),
    )
    computed_seal = seal.sign(payload)

    await writer.log(
        audit_repo,
        actor=principal.subject,
        action="CERTIFICATE_GENERATED",
        subject=st.get("apaar_id", ""),
        details=f"Issued TC {tc_no} to {body.destination_school or 'Transfer'}",
        category="CREDENTIAL_ISSUANCE",
    )

    return TransferCertificateOut(
        tc_number=tc_no,
        student_name=st.get("student_name", ""),
        grade_level=st.get("grade_level", ""),
        institution_id=body.institution_id,
        issue_date=now.strftime("%Y-%m-%d"),
        verification_token=raw_token,
        verification_url=f"/verify/t/{raw_token}",
        seal=computed_seal,
    )


@router.get("/dashboard")
async def get_school_dashboard(
    institution_id: str = Query(...),
    principal: Principal = Depends(require_any_permission(Permission.VIEW_INSTITUTION_DASHBOARD, Permission.VIEW_NATIONAL_DASHBOARD)),
    db=Depends(get_db),
):
    """Retrieve school academic metrics: enrolment by grade and section, gender distribution, guardian coverage."""
    principal.require_scope(institution_id)

    students = await db["students"].find({"institution_id": institution_id, "is_active": True}).to_list(length=5000)

    total = len(students)
    grades: dict[str, int] = defaultdict(int)
    genders: dict[str, int] = defaultdict(int)
    guardian_covered = 0
    minors = 0

    for st in students:
        g = st.get("grade_level") or "Unassigned"
        grades[g] += 1
        gen = st.get("gender") or "O"
        genders[gen] += 1
        if st.get("is_minor"):
            minors += 1
        if st.get("guardian_name") and st.get("guardian_contact"):
            guardian_covered += 1

    guardian_coverage_pct = round((guardian_covered / total * 100), 1) if total > 0 else 100.0

    return {
        "total_enrolled": total,
        "enrolment_by_grade": dict(grades),
        "gender_distribution": dict(genders),
        "minors_count": minors,
        "guardian_coverage_percent": guardian_coverage_pct,
        "data_quality_score": 100.0 if guardian_coverage_pct >= 95.0 else 85.0,
    }
