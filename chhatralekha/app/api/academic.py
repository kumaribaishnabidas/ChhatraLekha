"""Academic structure management for Schools and Colleges."""

from __future__ import annotations

import secrets
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Request
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
from app.repositories.audit import AuditRepository
from app.schemas.campus import (
    AcademicYearIn,
    AcademicYearOut,
    ClassSectionIn,
    ClassSectionOut,
    SubjectIn,
    SubjectOut,
    TeacherAssignmentIn,
    TeacherAssignmentOut,
)

router = APIRouter(prefix="/academic", tags=["academic-setup"])


# ------------------------------------------------------------- Academic Years
@router.post("/years", response_model=AcademicYearOut, summary="Create an academic year")
async def create_academic_year(
    payload: AcademicYearIn,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.MANAGE_ACADEMIC_SETUP)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> AcademicYearOut:
    """Create or activate an academic year for the institution."""
    inst_id = principal.institution_id or "INST-DEFAULT"
    year_id = f"AY-{inst_id}-{payload.year_label.replace('/', '-')}"

    doc = {
        "_id": year_id,
        "institution_id": inst_id,
        "year_label": payload.year_label,
        "start_date": payload.start_date,
        "end_date": payload.end_date,
        "is_current": payload.is_current,
        "terms": payload.terms,
    }

    if payload.is_current:
        await db["academic_years"].update_many(
            {"institution_id": inst_id},
            {"$set": {"is_current": False}},
        )

    await db["academic_years"].update_one(
        {"_id": year_id},
        {"$set": doc},
        upsert=True,
    )

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="CREATE_ACADEMIC_YEAR",
        subject=year_id,
        details=f"Academic year {payload.year_label} created for {inst_id}.",
        category="ACADEMIC_SETUP",
        ip_address=client_ip(request),
    )

    return AcademicYearOut(
        id=year_id,
        institution_id=inst_id,
        year_label=payload.year_label,
        start_date=payload.start_date,
        end_date=payload.end_date,
        is_current=payload.is_current,
        terms=payload.terms,
    )


@router.get("/years", response_model=List[AcademicYearOut], summary="List academic years")
async def list_academic_years(
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> List[AcademicYearOut]:
    """List configured academic years for the caller's institution."""
    query: dict[str, Any] = {}
    if principal.role not in {"aicte_admin", "platform_operator"} and principal.institution_id:
        query["institution_id"] = principal.institution_id

    rows = await db["academic_years"].find(query).sort("year_label", -1).to_list(100)
    return [
        AcademicYearOut(
            id=str(r["_id"]),
            institution_id=r.get("institution_id", ""),
            year_label=r.get("year_label", ""),
            start_date=r.get("start_date", ""),
            end_date=r.get("end_date", ""),
            is_current=r.get("is_current", False),
            terms=r.get("terms", []),
        )
        for r in rows
    ]


# ------------------------------------------------------------- Classes & Sections (School)
@router.post("/classes", response_model=ClassSectionOut, summary="Define class grade and section")
async def create_class_section(
    payload: ClassSectionIn,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.MANAGE_ACADEMIC_SETUP)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> ClassSectionOut:
    """Create a school class grade and section."""
    inst_id = principal.institution_id or "INST-DEFAULT"
    clean_grade = payload.grade_level.replace(" ", "_").upper()
    class_id = f"CLS-{inst_id}-{clean_grade}-{payload.section.upper()}-{payload.academic_year.replace('/', '-')}"

    doc = {
        "_id": class_id,
        "class_id": class_id,
        "institution_id": inst_id,
        "grade_level": payload.grade_level,
        "section": payload.section.upper(),
        "academic_year": payload.academic_year,
        "room_number": payload.room_number,
        "capacity": payload.capacity,
        "class_teacher_id": payload.class_teacher_id,
        "class_teacher_name": payload.class_teacher_name,
    }

    await db["classes"].update_one(
        {"_id": class_id},
        {"$set": doc},
        upsert=True,
    )

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="CREATE_CLASS_SECTION",
        subject=class_id,
        details=f"Created {payload.grade_level} Section {payload.section} ({payload.academic_year}).",
        category="ACADEMIC_SETUP",
        ip_address=client_ip(request),
    )

    return ClassSectionOut(
        class_id=class_id,
        institution_id=inst_id,
        grade_level=payload.grade_level,
        section=payload.section.upper(),
        academic_year=payload.academic_year,
        room_number=payload.room_number,
        capacity=payload.capacity,
        class_teacher_id=payload.class_teacher_id,
        class_teacher_name=payload.class_teacher_name,
    )


@router.get("/classes", response_model=List[ClassSectionOut], summary="List school classes")
async def list_classes(
    academic_year: Optional[str] = None,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> List[ClassSectionOut]:
    """List configured classes and sections."""
    query: dict[str, Any] = {}
    if principal.role not in {"aicte_admin", "platform_operator"} and principal.institution_id:
        query["institution_id"] = principal.institution_id
    if academic_year:
        query["academic_year"] = academic_year

    rows = await db["classes"].find(query).sort([("grade_level", 1), ("section", 1)]).to_list(200)
    return [
        ClassSectionOut(
            class_id=r.get("class_id") or str(r["_id"]),
            institution_id=r.get("institution_id", ""),
            grade_level=r.get("grade_level", ""),
            section=r.get("section", ""),
            academic_year=r.get("academic_year", ""),
            room_number=r.get("room_number"),
            capacity=r.get("capacity", 40),
            class_teacher_id=r.get("class_teacher_id"),
            class_teacher_name=r.get("class_teacher_name"),
        )
        for r in rows
    ]


# ------------------------------------------------------------- Subjects
@router.post("/subjects", response_model=SubjectOut, summary="Define academic subject")
async def create_subject(
    payload: SubjectIn,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.MANAGE_ACADEMIC_SETUP)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> SubjectOut:
    """Create a subject for a class or course."""
    inst_id = principal.institution_id or "INST-DEFAULT"
    subj_id = f"SUB-{inst_id}-{payload.subject_code.upper()}"

    doc = {
        "_id": subj_id,
        "subject_id": subj_id,
        "institution_id": inst_id,
        "subject_code": payload.subject_code.upper(),
        "subject_name": payload.subject_name,
        "category": payload.category.upper(),
        "applicable_to": payload.applicable_to,
    }

    await db["subjects"].update_one(
        {"_id": subj_id},
        {"$set": doc},
        upsert=True,
    )

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="CREATE_SUBJECT",
        subject=subj_id,
        details=f"Created subject {payload.subject_name} ({payload.subject_code}).",
        category="ACADEMIC_SETUP",
        ip_address=client_ip(request),
    )

    return SubjectOut(
        subject_id=subj_id,
        institution_id=inst_id,
        subject_code=payload.subject_code.upper(),
        subject_name=payload.subject_name,
        category=payload.category.upper(),
        applicable_to=payload.applicable_to,
    )


@router.get("/subjects", response_model=List[SubjectOut], summary="List subjects")
async def list_subjects(
    applicable_to: Optional[str] = None,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> List[SubjectOut]:
    """List configured subjects."""
    query: dict[str, Any] = {}
    if principal.role not in {"aicte_admin", "platform_operator"} and principal.institution_id:
        query["institution_id"] = principal.institution_id
    if applicable_to:
        query["applicable_to"] = applicable_to

    rows = await db["subjects"].find(query).sort("subject_name", 1).to_list(200)
    return [
        SubjectOut(
            subject_id=r.get("subject_id") or str(r["_id"]),
            institution_id=r.get("institution_id", ""),
            subject_code=r.get("subject_code", ""),
            subject_name=r.get("subject_name", ""),
            category=r.get("category", "CORE"),
            applicable_to=r.get("applicable_to", ""),
        )
        for r in rows
    ]


# ------------------------------------------------------------- Teacher Assignments
@router.post("/teacher-assignments", response_model=TeacherAssignmentOut, summary="Assign teacher to class/course")
async def create_teacher_assignment(
    payload: TeacherAssignmentIn,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.MANAGE_ACADEMIC_SETUP)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> TeacherAssignmentOut:
    """Allocate a faculty/teacher to a subject and class/programme."""
    inst_id = principal.institution_id or "INST-DEFAULT"
    assign_id = f"ASN-{secrets.token_hex(6)}"

    doc = {
        "_id": assign_id,
        "assignment_id": assign_id,
        "institution_id": inst_id,
        "teacher_id": payload.teacher_id,
        "teacher_name": payload.teacher_name,
        "subject_id": payload.subject_id,
        "subject_name": payload.subject_name,
        "target_type": payload.target_type,
        "target_id": payload.target_id,
        "target_label": payload.target_label,
    }

    await db["teacher_assignments"].insert_one(doc)

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="ASSIGN_TEACHER",
        subject=assign_id,
        details=f"Assigned {payload.teacher_name} to teach {payload.subject_name} for {payload.target_label}.",
        category="ACADEMIC_SETUP",
        ip_address=client_ip(request),
    )

    return TeacherAssignmentOut(
        assignment_id=assign_id,
        institution_id=inst_id,
        teacher_id=payload.teacher_id,
        teacher_name=payload.teacher_name,
        subject_id=payload.subject_id,
        subject_name=payload.subject_name,
        target_type=payload.target_type,
        target_id=payload.target_id,
        target_label=payload.target_label,
    )


@router.get("/teacher-assignments", response_model=List[TeacherAssignmentOut], summary="List teacher assignments")
async def list_teacher_assignments(
    teacher_id: Optional[str] = None,
    target_id: Optional[str] = None,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> List[TeacherAssignmentOut]:
    """List allocations of teachers to classes/courses."""
    query: dict[str, Any] = {}
    if principal.role not in {"aicte_admin", "platform_operator"} and principal.institution_id:
        query["institution_id"] = principal.institution_id
    if teacher_id:
        query["teacher_id"] = teacher_id
    if target_id:
        query["target_id"] = target_id

    rows = await db["teacher_assignments"].find(query).sort("target_label", 1).to_list(300)
    return [
        TeacherAssignmentOut(
            assignment_id=r.get("assignment_id") or str(r["_id"]),
            institution_id=r.get("institution_id", ""),
            teacher_id=r.get("teacher_id", ""),
            teacher_name=r.get("teacher_name", ""),
            subject_id=r.get("subject_id", ""),
            subject_name=r.get("subject_name", ""),
            target_type=r.get("target_type", "CLASS"),
            target_id=r.get("target_id", ""),
            target_label=r.get("target_label", ""),
        )
        for r in rows
    ]
