"""Academic structure and management core for Schools, Colleges, and Universities."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
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
    AcademicCalendarEventIn,
    AcademicCalendarEventOut,
    AcademicOverviewOut,
    AcademicYearIn,
    AcademicYearOut,
    ClassSectionIn,
    ClassSectionOut,
    DepartmentIn,
    DepartmentOut,
    ProgrammeIn,
    ProgrammeOut,
    SectionTransferIn,
    SemesterTermIn,
    SemesterTermOut,
    StudentEnrolmentIn,
    StudentEnrolmentOut,
    StudentPromotionIn,
    SubjectIn,
    SubjectOut,
    TeacherAssignmentIn,
    TeacherAssignmentOut,
)

router = APIRouter(prefix="/academic", tags=["academic-core"])


# ==============================================================================
# Helper functions & Auto-Seeding
# ==============================================================================

async def seed_academic_data(db: AsyncIOMotorDatabase, inst_id: str) -> None:
    """Seed synthetic demonstration academic data if institution collections are empty."""
    year_count = await db["academic_years"].count_documents({"institution_id": inst_id})
    if year_count > 0:
        return

    now_iso = datetime.now(timezone.utc).isoformat()

    # 1. Academic Years
    years_seed = [
        {
            "_id": f"AY-{inst_id}-2025-26",
            "institution_id": inst_id,
            "year_label": "2025-26",
            "start_date": "2025-06-01",
            "end_date": "2026-05-31",
            "admission_start_date": "2025-04-01",
            "admission_end_date": "2025-05-15",
            "is_current": True,
            "status": "ACTIVE",
            "terms": ["Term 1", "Term 2"],
            "created_at": now_iso,
        },
        {
            "_id": f"AY-{inst_id}-2024-25",
            "institution_id": inst_id,
            "year_label": "2024-25",
            "start_date": "2024-06-01",
            "end_date": "2025-05-31",
            "admission_start_date": "2024-04-01",
            "admission_end_date": "2024-05-15",
            "is_current": False,
            "status": "ARCHIVED",
            "terms": ["Term 1", "Term 2"],
            "created_at": now_iso,
        },
    ]
    for y in years_seed:
        await db["academic_years"].update_one({"_id": y["_id"]}, {"$set": y}, upsert=True)

    # 2. Semester Terms
    terms_seed = [
        {
            "_id": f"TRM-{inst_id}-2025-26-T1",
            "term_id": f"TRM-{inst_id}-2025-26-T1",
            "institution_id": inst_id,
            "academic_year": "2025-26",
            "name": "Term 1 (Monsoon Session)",
            "term_type": "SEMESTER",
            "start_date": "2025-06-15",
            "end_date": "2025-11-30",
            "status": "ACTIVE",
        },
        {
            "_id": f"TRM-{inst_id}-2025-26-T2",
            "term_id": f"TRM-{inst_id}-2025-26-T2",
            "institution_id": inst_id,
            "academic_year": "2025-26",
            "name": "Term 2 (Spring Session)",
            "term_type": "SEMESTER",
            "start_date": "2025-12-15",
            "end_date": "2026-05-15",
            "status": "UPCOMING",
        },
    ]
    for t in terms_seed:
        await db["semester_terms"].update_one({"_id": t["_id"]}, {"$set": t}, upsert=True)

    # 3. Departments
    dept_id = f"DEP-{inst_id}-CSE"
    dept_seed = [
        {
            "_id": dept_id,
            "department_id": dept_id,
            "institution_id": inst_id,
            "department_code": "CSE",
            "name": "Department of Computer Science & Engineering",
            "description": "Undergraduate and postgraduate computing, AI, and systems engineering.",
            "head_of_department_id": "FAC-0101",
            "head_of_department_name": "Dr. Ramesh Kumar",
            "contact_email": "cse.hod@institution.edu.in",
            "campus_id": "MAIN-CAMPUS",
            "faculty_count": 18,
            "programme_count": 2,
            "status": "ACTIVE",
        },
        {
            "_id": f"DEP-{inst_id}-SCI",
            "department_id": f"DEP-{inst_id}-SCI",
            "institution_id": inst_id,
            "department_code": "SCI",
            "name": "Department of General Sciences",
            "description": "Secondary and higher secondary foundational sciences and mathematics.",
            "head_of_department_id": "FAC-0102",
            "head_of_department_name": "Prof. Sunita Sharma",
            "contact_email": "science.hod@institution.edu.in",
            "campus_id": "MAIN-CAMPUS",
            "faculty_count": 12,
            "programme_count": 1,
            "status": "ACTIVE",
        },
    ]
    for d in dept_seed:
        await db["departments"].update_one({"_id": d["_id"]}, {"$set": d}, upsert=True)

    # 4. Programmes
    prg_id = f"PRG-{inst_id}-BTECH-CSE"
    prg_seed = [
        {
            "_id": prg_id,
            "programme_id": prg_id,
            "institution_id": inst_id,
            "programme_code": "BTECH-CSE",
            "name": "Bachelor of Technology in Computer Science and Engineering",
            "department_id": dept_id,
            "academic_level": "UNDERGRADUATE",
            "duration_years": 4,
            "total_semesters": 8,
            "degree_awarded": "B.Tech",
            "curriculum_framework": "AICTE Model Curriculum 2024",
            "approved_intake": 120,
            "status": "ACTIVE",
        },
        {
            "_id": f"PRG-{inst_id}-SEC-10",
            "programme_id": f"PRG-{inst_id}-SEC-10",
            "institution_id": inst_id,
            "programme_code": "CLASS-10",
            "name": "Secondary School Curriculum (Class 10)",
            "department_id": f"DEP-{inst_id}-SCI",
            "academic_level": "SECONDARY",
            "duration_years": 1,
            "total_semesters": 2,
            "degree_awarded": "Secondary School Certificate",
            "curriculum_framework": "NCF-SE 2023",
            "approved_intake": 80,
            "status": "ACTIVE",
        },
    ]
    for p in prg_seed:
        await db["programmes"].update_one({"_id": p["_id"]}, {"$set": p}, upsert=True)

    # 5. Classes & Sections
    classes_seed = [
        {
            "_id": f"CLS-{inst_id}-CLASS_10-A-2025-26",
            "class_id": f"CLS-{inst_id}-CLASS_10-A-2025-26",
            "institution_id": inst_id,
            "grade_level": "Class 10",
            "section": "A",
            "academic_year": "2025-26",
            "programme_id": f"PRG-{inst_id}-SEC-10",
            "room_number": "Room 201",
            "capacity": 40,
            "enrolled_count": 38,
            "class_teacher_id": "FAC-0102",
            "class_teacher_name": "Prof. Sunita Sharma",
            "status": "ACTIVE",
        },
        {
            "_id": f"CLS-{inst_id}-CLASS_10-B-2025-26",
            "class_id": f"CLS-{inst_id}-CLASS_10-B-2025-26",
            "institution_id": inst_id,
            "grade_level": "Class 10",
            "section": "B",
            "academic_year": "2025-26",
            "programme_id": f"PRG-{inst_id}-SEC-10",
            "room_number": "Room 202",
            "capacity": 40,
            "enrolled_count": 35,
            "class_teacher_id": "FAC-0103",
            "class_teacher_name": "Prof. Ananya Sen",
            "status": "ACTIVE",
        },
        {
            "_id": f"CLS-{inst_id}-SEM_5_CSE-A-2025-26",
            "class_id": f"CLS-{inst_id}-SEM_5_CSE-A-2025-26",
            "institution_id": inst_id,
            "grade_level": "Semester 5",
            "section": "A",
            "academic_year": "2025-26",
            "programme_id": prg_id,
            "room_number": "Tech Block LH-3",
            "capacity": 60,
            "enrolled_count": 58,
            "class_teacher_id": "FAC-0101",
            "class_teacher_name": "Dr. Ramesh Kumar",
            "status": "ACTIVE",
        },
    ]
    for c in classes_seed:
        await db["classes"].update_one({"_id": c["_id"]}, {"$set": c}, upsert=True)

    # 6. Subjects
    subjects_seed = [
        {
            "_id": f"SUB-{inst_id}-MATH-10",
            "subject_id": f"SUB-{inst_id}-MATH-10",
            "institution_id": inst_id,
            "subject_code": "MATH-10",
            "subject_name": "Mathematics (Class 10)",
            "subject_name_hi": "गणित (कक्षा 10)",
            "category": "CORE",
            "applicable_to": "Class 10",
            "department_id": f"DEP-{inst_id}-SCI",
            "programme_id": f"PRG-{inst_id}-SEC-10",
            "semester": 1,
            "credits": 4.0,
            "theory_hours": 4,
            "practical_hours": 0,
            "is_practical": False,
            "status": "ACTIVE",
        },
        {
            "_id": f"SUB-{inst_id}-SCI-10",
            "subject_id": f"SUB-{inst_id}-SCI-10",
            "institution_id": inst_id,
            "subject_code": "SCI-10",
            "subject_name": "Integrated Science & Laboratory",
            "subject_name_hi": "एकीकृत विज्ञान एवं प्रयोगशाला",
            "category": "CORE",
            "applicable_to": "Class 10",
            "department_id": f"DEP-{inst_id}-SCI",
            "programme_id": f"PRG-{inst_id}-SEC-10",
            "semester": 1,
            "credits": 4.0,
            "theory_hours": 3,
            "practical_hours": 2,
            "is_practical": True,
            "status": "ACTIVE",
        },
        {
            "_id": f"SUB-{inst_id}-CS301",
            "subject_id": f"SUB-{inst_id}-CS301",
            "institution_id": inst_id,
            "subject_code": "CS301",
            "subject_name": "Database Management Systems",
            "subject_name_hi": "डेटाबेस प्रबंधन प्रणाली",
            "category": "CORE",
            "applicable_to": "B.Tech CSE",
            "department_id": dept_id,
            "programme_id": prg_id,
            "semester": 5,
            "credits": 4.0,
            "theory_hours": 3,
            "practical_hours": 2,
            "is_practical": True,
            "status": "ACTIVE",
        },
    ]
    for s in subjects_seed:
        await db["subjects"].update_one({"_id": s["_id"]}, {"$set": s}, upsert=True)

    # 7. Student Enrolments
    enrolment_seed = [
        {
            "_id": f"ENR-{inst_id}-DEMO-01",
            "enrolment_id": f"ENR-{inst_id}-DEMO-01",
            "institution_id": inst_id,
            "student_id": "STU-001",
            "student_name": "Aarav Sharma",
            "roll_number": "10-A-01",
            "academic_year": "2025-26",
            "programme_id": f"PRG-{inst_id}-SEC-10",
            "programme_name": "Secondary School Curriculum (Class 10)",
            "class_id": f"CLS-{inst_id}-CLASS_10-A-2025-26",
            "class_name": "Class 10-A",
            "section": "A",
            "semester": 1,
            "status": "ACTIVE",
            "enrolled_date": "2025-06-01",
            "is_current": True,
            "remarks": "Regular admission enrolled under merit intake.",
        },
        {
            "_id": f"ENR-{inst_id}-DEMO-02",
            "enrolment_id": f"ENR-{inst_id}-DEMO-02",
            "institution_id": inst_id,
            "student_id": "STU-002",
            "student_name": "Priya Verma",
            "roll_number": "10-A-02",
            "academic_year": "2025-26",
            "programme_id": f"PRG-{inst_id}-SEC-10",
            "programme_name": "Secondary School Curriculum (Class 10)",
            "class_id": f"CLS-{inst_id}-CLASS_10-A-2025-26",
            "class_name": "Class 10-A",
            "section": "A",
            "semester": 1,
            "status": "ACTIVE",
            "enrolled_date": "2025-06-01",
            "is_current": True,
            "remarks": "Regular admission.",
        },
        {
            "_id": f"ENR-{inst_id}-DEMO-03",
            "enrolment_id": f"ENR-{inst_id}-DEMO-03",
            "institution_id": inst_id,
            "student_id": "STU-003",
            "student_name": "Rohan Deshmukh",
            "roll_number": "CSE-2023-042",
            "academic_year": "2025-26",
            "programme_id": prg_id,
            "programme_name": "B.Tech in Computer Science and Engineering",
            "class_id": f"CLS-{inst_id}-SEM_5_CSE-A-2025-26",
            "class_name": "Semester 5-A",
            "section": "A",
            "semester": 5,
            "status": "ACTIVE",
            "enrolled_date": "2025-06-05",
            "is_current": True,
            "remarks": "Promoted to Semester 5.",
        },
    ]
    for e in enrolment_seed:
        await db["student_enrolments"].update_one({"_id": e["_id"]}, {"$set": e}, upsert=True)

    # 8. Teacher Assignments
    teachers_seed = [
        {
            "_id": f"ASN-{inst_id}-01",
            "assignment_id": f"ASN-{inst_id}-01",
            "institution_id": inst_id,
            "teacher_id": "FAC-0102",
            "teacher_name": "Prof. Sunita Sharma",
            "subject_id": f"SUB-{inst_id}-MATH-10",
            "subject_name": "Mathematics (Class 10)",
            "target_type": "CLASS",
            "target_id": f"CLS-{inst_id}-CLASS_10-A-2025-26",
            "target_label": "Class 10-A",
            "academic_year": "2025-26",
            "role_in_course": "PRIMARY_INSTRUCTOR",
            "status": "ACTIVE",
        },
        {
            "_id": f"ASN-{inst_id}-02",
            "assignment_id": f"ASN-{inst_id}-02",
            "institution_id": inst_id,
            "teacher_id": "FAC-0101",
            "teacher_name": "Dr. Ramesh Kumar",
            "subject_id": f"SUB-{inst_id}-CS301",
            "subject_name": "Database Management Systems",
            "target_type": "PROGRAMME",
            "target_id": prg_id,
            "target_label": "B.Tech CSE Semester 5",
            "academic_year": "2025-26",
            "role_in_course": "PRIMARY_INSTRUCTOR",
            "status": "ACTIVE",
        },
    ]
    for ta in teachers_seed:
        await db["teacher_assignments"].update_one({"_id": ta["_id"]}, {"$set": ta}, upsert=True)

    # 9. Academic Calendar Events
    events_seed = [
        {
            "_id": f"EVT-{inst_id}-01",
            "event_id": f"EVT-{inst_id}-01",
            "institution_id": inst_id,
            "academic_year": "2025-26",
            "title": "Semester 1 Teaching Session Begins",
            "description": "Formal commencement of lectures and laboratory sessions.",
            "event_type": "SEMESTER_START",
            "start_date": "2025-06-15",
            "end_date": "2025-06-15",
            "target_audience": "ALL",
            "is_holiday": False,
            "timezone": "Asia/Kolkata",
        },
        {
            "_id": f"EVT-{inst_id}-02",
            "event_id": f"EVT-{inst_id}-02",
            "institution_id": inst_id,
            "academic_year": "2025-26",
            "title": "Independence Day National Holiday",
            "description": "Institution closed in observance of national holiday.",
            "event_type": "HOLIDAY",
            "start_date": "2025-08-15",
            "end_date": "2025-08-15",
            "target_audience": "ALL",
            "is_holiday": True,
            "timezone": "Asia/Kolkata",
        },
        {
            "_id": f"EVT-{inst_id}-03",
            "event_id": f"EVT-{inst_id}-03",
            "institution_id": inst_id,
            "academic_year": "2025-26",
            "title": "Mid-Term Examination Period",
            "description": "Mid-term written assessments for all registered classes.",
            "event_type": "EXAM",
            "start_date": "2025-10-10",
            "end_date": "2025-10-20",
            "target_audience": "ALL",
            "is_holiday": False,
            "timezone": "Asia/Kolkata",
        },
    ]
    for ev in events_seed:
        await db["academic_calendar_events"].update_one({"_id": ev["_id"]}, {"$set": ev}, upsert=True)


# Backwards-compatible alias for explicit development seeding
_ensure_academic_seeds = seed_academic_data


# ==============================================================================
# 1. Academic Overview & Summary
# ==============================================================================

@router.get("/overview", response_model=AcademicOverviewOut, summary="Get institutional academic structure overview")
async def get_academic_overview(
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> AcademicOverviewOut:
    """Return consolidated statistics of the academic hierarchy for the caller's institution."""
    inst_id = principal.require_tenant_context()

    # Fetch current active year
    current_year_doc = await db["academic_years"].find_one({"institution_id": inst_id, "is_current": True})
    current_year_label = current_year_doc.get("year_label") if current_year_doc else None

    # Aggregated metric counts
    total_departments = await db["departments"].count_documents({"institution_id": inst_id, "status": "ACTIVE"})
    total_programmes = await db["programmes"].count_documents({"institution_id": inst_id, "status": "ACTIVE"})
    total_classes = await db["classes"].count_documents({"institution_id": inst_id, "status": "ACTIVE"})
    total_subjects = await db["subjects"].count_documents({"institution_id": inst_id, "status": "ACTIVE"})
    total_enrolled = await db["student_enrolments"].count_documents({"institution_id": inst_id, "is_current": True})
    total_faculty = await db["teacher_assignments"].count_documents({"institution_id": inst_id, "status": "ACTIVE"})
    active_terms = await db["semester_terms"].count_documents({"institution_id": inst_id, "status": "ACTIVE"})
    upcoming_events = await db["academic_calendar_events"].count_documents({"institution_id": inst_id})

    # Fetch institution metadata if available
    inst_doc = await db["institutions"].find_one({"_id": inst_id})
    inst_name = inst_doc.get("name", "Kendriya Vidyalaya / Autonomous Campus") if inst_doc else "Kendriya Vidyalaya / Autonomous Campus"
    inst_cat = inst_doc.get("category", "INSTITUTION") if inst_doc else "INSTITUTION"

    return AcademicOverviewOut(
        institution_id=inst_id,
        institution_name=inst_name,
        institution_category=inst_cat,
        current_academic_year=current_year_label,
        total_departments=total_departments,
        total_programmes=total_programmes,
        total_classes=total_classes,
        total_subjects=total_subjects,
        total_enrolled_students=total_enrolled,
        total_faculty_assigned=total_faculty,
        active_terms_count=active_terms,
        upcoming_events_count=upcoming_events,
    )


# ==============================================================================
# 2. Academic Years Management
# ==============================================================================

@router.post("/years", response_model=AcademicYearOut, summary="Create an academic year")
async def create_academic_year(
    payload: AcademicYearIn,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.MANAGE_ACADEMIC_SETUP)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> AcademicYearOut:
    """Create or activate an academic year with strict date validation."""
    if payload.start_date >= payload.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Academic year start_date must precede end_date.",
        )

    inst_id = principal.require_tenant_context()
    year_id = f"AY-{inst_id}-{payload.year_label.replace('/', '-')}"

    doc = {
        "_id": year_id,
        "institution_id": inst_id,
        "year_label": payload.year_label,
        "start_date": payload.start_date,
        "end_date": payload.end_date,
        "admission_start_date": payload.admission_start_date,
        "admission_end_date": payload.admission_end_date,
        "is_current": payload.is_current,
        "status": payload.status,
        "terms": payload.terms,
        "updated_at": datetime.now(timezone.utc).isoformat(),
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
        admission_start_date=payload.admission_start_date,
        admission_end_date=payload.admission_end_date,
        is_current=payload.is_current,
        status=payload.status,
        terms=payload.terms,
    )


@router.get("/years", response_model=List[AcademicYearOut], summary="List academic years")
async def list_academic_years(
    institution_id: Optional[str] = None,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> List[AcademicYearOut]:
    """List configured academic years for the caller's institution."""
    target_inst_id = principal.get_scoped_institution_id(institution_id)

    query: dict[str, Any] = {}
    if target_inst_id:
        query["institution_id"] = target_inst_id

    rows = await db["academic_years"].find(query).sort("start_date", -1).to_list(100)
    return [
        AcademicYearOut(
            id=str(r["_id"]),
            institution_id=r.get("institution_id", ""),
            year_label=r.get("year_label", ""),
            start_date=r.get("start_date", ""),
            end_date=r.get("end_date", ""),
            admission_start_date=r.get("admission_start_date"),
            admission_end_date=r.get("admission_end_date"),
            is_current=r.get("is_current", False),
            status=r.get("status", "ACTIVE"),
            terms=r.get("terms", []),
        )
        for r in rows
    ]


@router.post("/years/{year_id}/activate", response_model=AcademicYearOut, summary="Activate academic year as current")
async def activate_academic_year(
    year_id: str,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.MANAGE_ACADEMIC_SETUP)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> AcademicYearOut:
    """Set the specified academic year as the current active year, deactivating others."""
    inst_id = principal.require_tenant_context()
    doc = await db["academic_years"].find_one({"_id": year_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic year not found.")
    principal.require_scope(doc.get("institution_id", ""))

    await db["academic_years"].update_many(
        {"institution_id": inst_id},
        {"$set": {"is_current": False}},
    )
    await db["academic_years"].update_one(
        {"_id": year_id},
        {"$set": {"is_current": True, "status": "ACTIVE", "updated_at": datetime.now(timezone.utc).isoformat()}},
    )

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="ACTIVATE_ACADEMIC_YEAR",
        subject=year_id,
        details=f"Academic year {doc.get('year_label')} marked active as current.",
        category="ACADEMIC_SETUP",
        ip_address=client_ip(request),
    )

    updated = await db["academic_years"].find_one({"_id": year_id})
    return AcademicYearOut(
        id=str(updated["_id"]),
        institution_id=updated["institution_id"],
        year_label=updated["year_label"],
        start_date=updated["start_date"],
        end_date=updated["end_date"],
        admission_start_date=updated.get("admission_start_date"),
        admission_end_date=updated.get("admission_end_date"),
        is_current=True,
        status="ACTIVE",
        terms=updated.get("terms", []),
    )


@router.post("/years/{year_id}/archive", response_model=AcademicYearOut, summary="Archive completed academic year")
async def archive_academic_year(
    year_id: str,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.MANAGE_ACADEMIC_SETUP)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> AcademicYearOut:
    """Archive an academic year. Historical records and enrolments are strictly preserved."""
    principal.require_tenant_context()
    doc = await db["academic_years"].find_one({"_id": year_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic year not found.")
    principal.require_scope(doc.get("institution_id", ""))

    await db["academic_years"].update_one(
        {"_id": year_id},
        {"$set": {"is_current": False, "status": "ARCHIVED", "updated_at": datetime.now(timezone.utc).isoformat()}},
    )

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="ARCHIVE_ACADEMIC_YEAR",
        subject=year_id,
        details=f"Academic year {doc.get('year_label')} archived. Historical records retained.",
        category="ACADEMIC_SETUP",
        ip_address=client_ip(request),
    )

    updated = await db["academic_years"].find_one({"_id": year_id})
    return AcademicYearOut(
        id=str(updated["_id"]),
        institution_id=updated["institution_id"],
        year_label=updated["year_label"],
        start_date=updated["start_date"],
        end_date=updated["end_date"],
        admission_start_date=updated.get("admission_start_date"),
        admission_end_date=updated.get("admission_end_date"),
        is_current=False,
        status="ARCHIVED",
        terms=updated.get("terms", []),
    )


# ==============================================================================
# 3. Semesters and Terms Management
# ==============================================================================

@router.post("/terms", response_model=SemesterTermOut, summary="Define semester or academic term")
async def create_semester_term(
    payload: SemesterTermIn,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.MANAGE_ACADEMIC_SETUP)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> SemesterTermOut:
    """Create a term or semester within an academic year."""
    if payload.start_date >= payload.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Term start_date must precede end_date.",
        )

    inst_id = principal.require_tenant_context()
    slug = payload.name.lower().replace(" ", "_")
    term_id = f"TRM-{inst_id}-{payload.academic_year.replace('/', '-')}-{slug}"

    doc = {
        "_id": term_id,
        "term_id": term_id,
        "institution_id": inst_id,
        "academic_year": payload.academic_year,
        "name": payload.name,
        "term_type": payload.term_type,
        "start_date": payload.start_date,
        "end_date": payload.end_date,
        "status": payload.status,
    }

    await db["semester_terms"].update_one({"_id": term_id}, {"$set": doc}, upsert=True)

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="CREATE_SEMESTER_TERM",
        subject=term_id,
        details=f"Created {payload.name} ({payload.academic_year}).",
        category="ACADEMIC_SETUP",
        ip_address=client_ip(request),
    )

    return SemesterTermOut(
        term_id=term_id,
        institution_id=inst_id,
        academic_year=payload.academic_year,
        name=payload.name,
        term_type=payload.term_type,
        start_date=payload.start_date,
        end_date=payload.end_date,
        status=payload.status,
    )


@router.get("/terms", response_model=List[SemesterTermOut], summary="List semester terms")
async def list_semester_terms(
    academic_year: Optional[str] = None,
    institution_id: Optional[str] = None,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> List[SemesterTermOut]:
    """List configured semesters and academic terms."""
    target_inst_id = principal.get_scoped_institution_id(institution_id)

    query: dict[str, Any] = {}
    if target_inst_id:
        query["institution_id"] = target_inst_id
    if academic_year:
        query["academic_year"] = academic_year

    rows = await db["semester_terms"].find(query).sort("start_date", 1).to_list(100)
    return [
        SemesterTermOut(
            term_id=r.get("term_id") or str(r["_id"]),
            institution_id=r.get("institution_id", ""),
            academic_year=r.get("academic_year", ""),
            name=r.get("name", ""),
            term_type=r.get("term_type", "SEMESTER"),
            start_date=r.get("start_date", ""),
            end_date=r.get("end_date", ""),
            status=r.get("status", "ACTIVE"),
        )
        for r in rows
    ]


# ==============================================================================
# 4. Department Management
# ==============================================================================

@router.post("/departments", response_model=DepartmentOut, summary="Create academic department")
async def create_department(
    payload: DepartmentIn,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.MANAGE_ACADEMIC_SETUP)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> DepartmentOut:
    """Create an academic department (higher ed or specialized school departments)."""
    inst_id = principal.require_tenant_context()
    dept_id = f"DEP-{inst_id}-{payload.department_code.upper()}"

    doc = {
        "_id": dept_id,
        "department_id": dept_id,
        "institution_id": inst_id,
        "department_code": payload.department_code.upper(),
        "name": payload.name,
        "description": payload.description,
        "head_of_department_id": payload.head_of_department_id,
        "head_of_department_name": payload.head_of_department_name,
        "contact_email": payload.contact_email,
        "campus_id": payload.campus_id or "MAIN-CAMPUS",
        "faculty_count": 0,
        "programme_count": 0,
        "status": "ACTIVE",
    }

    await db["departments"].update_one({"_id": dept_id}, {"$set": doc}, upsert=True)

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="CREATE_DEPARTMENT",
        subject=dept_id,
        details=f"Created department {payload.name} ({payload.department_code}).",
        category="ACADEMIC_SETUP",
        ip_address=client_ip(request),
    )

    return DepartmentOut(**doc)


@router.get("/departments", response_model=List[DepartmentOut], summary="List academic departments")
async def list_departments(
    institution_id: Optional[str] = None,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> List[DepartmentOut]:
    """List departments for the caller's institution."""
    target_inst_id = principal.get_scoped_institution_id(institution_id)

    query: dict[str, Any] = {"status": "ACTIVE"}
    if target_inst_id:
        query["institution_id"] = target_inst_id

    rows = await db["departments"].find(query).sort("name", 1).to_list(100)
    return [
        DepartmentOut(
            department_id=r.get("department_id") or str(r["_id"]),
            institution_id=r.get("institution_id", ""),
            department_code=r.get("department_code", ""),
            name=r.get("name", ""),
            description=r.get("description"),
            head_of_department_id=r.get("head_of_department_id"),
            head_of_department_name=r.get("head_of_department_name"),
            contact_email=r.get("contact_email"),
            campus_id=r.get("campus_id"),
            faculty_count=r.get("faculty_count", 0),
            programme_count=r.get("programme_count", 0),
            status=r.get("status", "ACTIVE"),
        )
        for r in rows
    ]


@router.put("/departments/{department_id}", response_model=DepartmentOut, summary="Update department details")
async def update_department(
    department_id: str,
    payload: DepartmentIn,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.MANAGE_ACADEMIC_SETUP)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> DepartmentOut:
    """Update department information and HOD assignments."""
    principal.require_tenant_context()
    doc = await db["departments"].find_one({"_id": department_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found.")
    principal.require_scope(doc.get("institution_id", ""))

    updates = {
        "name": payload.name,
        "description": payload.description,
        "head_of_department_id": payload.head_of_department_id,
        "head_of_department_name": payload.head_of_department_name,
        "contact_email": payload.contact_email,
        "campus_id": payload.campus_id,
    }
    await db["departments"].update_one({"_id": department_id}, {"$set": updates})

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="UPDATE_DEPARTMENT",
        subject=department_id,
        details=f"Updated department {payload.name}.",
        category="ACADEMIC_SETUP",
        ip_address=client_ip(request),
    )

    updated = await db["departments"].find_one({"_id": department_id})
    return DepartmentOut(
        department_id=updated.get("department_id") or str(updated["_id"]),
        institution_id=updated.get("institution_id", ""),
        department_code=updated.get("department_code", ""),
        name=updated.get("name", ""),
        description=updated.get("description"),
        head_of_department_id=updated.get("head_of_department_id"),
        head_of_department_name=updated.get("head_of_department_name"),
        contact_email=updated.get("contact_email"),
        campus_id=updated.get("campus_id"),
        faculty_count=updated.get("faculty_count", 0),
        programme_count=updated.get("programme_count", 0),
        status=updated.get("status", "ACTIVE"),
    )


# ==============================================================================
# 5. Programme and Course Management
# ==============================================================================

@router.post("/programmes", response_model=ProgrammeOut, summary="Define academic programme / degree")
async def create_programme(
    payload: ProgrammeIn,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.MANAGE_ACADEMIC_SETUP)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> ProgrammeOut:
    """Create an academic programme, degree curriculum, or school grade structure."""
    inst_id = principal.require_tenant_context()
    if payload.department_id:
        dept = await db["departments"].find_one({"_id": payload.department_id, "institution_id": inst_id})
        if not dept:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Department '{payload.department_id}' not found in institution.",
            )

    prg_id = f"PRG-{inst_id}-{payload.programme_code.upper()}"

    doc = {
        "_id": prg_id,
        "programme_id": prg_id,
        "institution_id": inst_id,
        "programme_code": payload.programme_code.upper(),
        "name": payload.name,
        "department_id": payload.department_id,
        "academic_level": payload.academic_level,
        "duration_years": payload.duration_years,
        "total_semesters": payload.total_semesters,
        "degree_awarded": payload.degree_awarded,
        "curriculum_framework": payload.curriculum_framework,
        "approved_intake": payload.approved_intake,
        "status": "ACTIVE",
    }

    await db["programmes"].update_one({"_id": prg_id}, {"$set": doc}, upsert=True)

    if payload.department_id:
        await db["departments"].update_one(
            {"_id": payload.department_id},
            {"$inc": {"programme_count": 1}},
        )

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="CREATE_PROGRAMME",
        subject=prg_id,
        details=f"Created programme {payload.name} ({payload.programme_code}).",
        category="ACADEMIC_SETUP",
        ip_address=client_ip(request),
    )

    return ProgrammeOut(**doc)


@router.get("/programmes", response_model=List[ProgrammeOut], summary="List academic programmes")
async def list_programmes(
    department_id: Optional[str] = None,
    academic_level: Optional[str] = None,
    institution_id: Optional[str] = None,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> List[ProgrammeOut]:
    """List academic programmes for the institution."""
    target_inst_id = principal.get_scoped_institution_id(institution_id)

    query: dict[str, Any] = {"status": "ACTIVE"}
    if target_inst_id:
        query["institution_id"] = target_inst_id
    if department_id:
        query["department_id"] = department_id
    if academic_level:
        query["academic_level"] = academic_level

    rows = await db["programmes"].find(query).sort("name", 1).to_list(100)
    return [
        ProgrammeOut(
            programme_id=r.get("programme_id") or str(r["_id"]),
            institution_id=r.get("institution_id", ""),
            programme_code=r.get("programme_code", ""),
            name=r.get("name", ""),
            department_id=r.get("department_id"),
            academic_level=r.get("academic_level", "UNDERGRADUATE"),
            duration_years=r.get("duration_years", 4),
            total_semesters=r.get("total_semesters", 8),
            degree_awarded=r.get("degree_awarded"),
            curriculum_framework=r.get("curriculum_framework"),
            approved_intake=r.get("approved_intake", 60),
            status=r.get("status", "ACTIVE"),
        )
        for r in rows
    ]


# ==============================================================================
# 6. Classes & Sections Management
# ==============================================================================

@router.post("/classes", response_model=ClassSectionOut, summary="Define class grade and section")
async def create_class_section(
    payload: ClassSectionIn,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.MANAGE_ACADEMIC_SETUP)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> ClassSectionOut:
    """Create a school class grade and section or college cohort."""
    inst_id = principal.require_tenant_context()
    if payload.programme_id:
        prg = await db["programmes"].find_one({"_id": payload.programme_id, "institution_id": inst_id})
        if not prg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Programme '{payload.programme_id}' not found in institution.",
            )

    clean_grade = payload.grade_level.replace(" ", "_").upper()
    class_id = f"CLS-{inst_id}-{clean_grade}-{payload.section.upper()}-{payload.academic_year.replace('/', '-')}"

    doc = {
        "_id": class_id,
        "class_id": class_id,
        "institution_id": inst_id,
        "grade_level": payload.grade_level,
        "section": payload.section.upper(),
        "academic_year": payload.academic_year,
        "programme_id": payload.programme_id,
        "room_number": payload.room_number,
        "capacity": payload.capacity,
        "enrolled_count": 0,
        "class_teacher_id": payload.class_teacher_id,
        "class_teacher_name": payload.class_teacher_name,
        "status": "ACTIVE",
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
        programme_id=payload.programme_id,
        room_number=payload.room_number,
        capacity=payload.capacity,
        enrolled_count=0,
        class_teacher_id=payload.class_teacher_id,
        class_teacher_name=payload.class_teacher_name,
        status="ACTIVE",
    )


@router.get("/classes", response_model=List[ClassSectionOut], summary="List school and college classes")
async def list_classes(
    academic_year: Optional[str] = None,
    programme_id: Optional[str] = None,
    institution_id: Optional[str] = None,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> List[ClassSectionOut]:
    """List configured classes and sections."""
    target_inst_id = principal.get_scoped_institution_id(institution_id)

    query: dict[str, Any] = {"status": "ACTIVE"}
    if target_inst_id:
        query["institution_id"] = target_inst_id
    if academic_year:
        query["academic_year"] = academic_year
    if programme_id:
        query["programme_id"] = programme_id

    rows = await db["classes"].find(query).sort([("grade_level", 1), ("section", 1)]).to_list(200)
    return [
        ClassSectionOut(
            class_id=r.get("class_id") or str(r["_id"]),
            institution_id=r.get("institution_id", ""),
            grade_level=r.get("grade_level", ""),
            section=r.get("section", ""),
            academic_year=r.get("academic_year", ""),
            programme_id=r.get("programme_id"),
            room_number=r.get("room_number"),
            capacity=r.get("capacity", 40),
            enrolled_count=r.get("enrolled_count", 0),
            class_teacher_id=r.get("class_teacher_id"),
            class_teacher_name=r.get("class_teacher_name"),
            status=r.get("status", "ACTIVE"),
        )
        for r in rows
    ]


# ==============================================================================
# 7. Subjects Management
# ==============================================================================

@router.post("/subjects", response_model=SubjectOut, summary="Define academic subject")
async def create_subject(
    payload: SubjectIn,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.MANAGE_ACADEMIC_SETUP)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> SubjectOut:
    """Create a subject for a class or course curriculum."""
    inst_id = principal.require_tenant_context()
    if payload.department_id:
        dept = await db["departments"].find_one({"_id": payload.department_id, "institution_id": inst_id})
        if not dept:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Department '{payload.department_id}' not found in institution.",
            )
    if payload.programme_id:
        prg = await db["programmes"].find_one({"_id": payload.programme_id, "institution_id": inst_id})
        if not prg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Programme '{payload.programme_id}' not found in institution.",
            )

    subj_id = f"SUB-{inst_id}-{payload.subject_code.upper()}"

    doc = {
        "_id": subj_id,
        "subject_id": subj_id,
        "institution_id": inst_id,
        "subject_code": payload.subject_code.upper(),
        "subject_name": payload.subject_name,
        "subject_name_hi": payload.subject_name_hi,
        "category": payload.category.upper(),
        "applicable_to": payload.applicable_to,
        "department_id": payload.department_id,
        "programme_id": payload.programme_id,
        "semester": payload.semester,
        "credits": payload.credits,
        "theory_hours": payload.theory_hours,
        "practical_hours": payload.practical_hours,
        "is_practical": payload.is_practical,
        "status": "ACTIVE",
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

    return SubjectOut(**doc)


@router.get("/subjects", response_model=List[SubjectOut], summary="List subjects")
async def list_subjects(
    applicable_to: Optional[str] = None,
    department_id: Optional[str] = None,
    programme_id: Optional[str] = None,
    institution_id: Optional[str] = None,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> List[SubjectOut]:
    """List configured subjects."""
    target_inst_id = principal.get_scoped_institution_id(institution_id)

    query: dict[str, Any] = {"status": "ACTIVE"}
    if target_inst_id:
        query["institution_id"] = target_inst_id
    if applicable_to:
        query["applicable_to"] = applicable_to
    if department_id:
        query["department_id"] = department_id
    if programme_id:
        query["programme_id"] = programme_id

    rows = await db["subjects"].find(query).sort("subject_name", 1).to_list(200)
    return [
        SubjectOut(
            subject_id=r.get("subject_id") or str(r["_id"]),
            institution_id=r.get("institution_id", ""),
            subject_code=r.get("subject_code", ""),
            subject_name=r.get("subject_name", ""),
            subject_name_hi=r.get("subject_name_hi"),
            category=r.get("category", "CORE"),
            applicable_to=r.get("applicable_to", ""),
            department_id=r.get("department_id"),
            programme_id=r.get("programme_id"),
            semester=r.get("semester"),
            credits=r.get("credits", 3.0),
            theory_hours=r.get("theory_hours", 3),
            practical_hours=r.get("practical_hours", 0),
            is_practical=r.get("is_practical", False),
            status=r.get("status", "ACTIVE"),
        )
        for r in rows
    ]


# ==============================================================================
# 8. Student Enrolment Management
# ==============================================================================

@router.post("/enrolments", response_model=StudentEnrolmentOut, summary="Enrol student into class/programme")
async def enrol_student(
    payload: StudentEnrolmentIn,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.MANAGE_ACADEMIC_SETUP)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> StudentEnrolmentOut:
    """Enrol a student. Validates that no active duplicate enrolment exists for the same student in that academic year."""
    inst_id = principal.require_tenant_context()

    # Check for active duplicate enrolment
    existing = await db["student_enrolments"].find_one({
        "institution_id": inst_id,
        "student_id": payload.student_id,
        "academic_year": payload.academic_year,
        "is_current": True,
    })
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Student {payload.student_name} already has an active enrolment for academic year {payload.academic_year}.",
        )

    enrol_id = f"ENR-{inst_id}-{secrets.token_hex(5)}"
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    doc = {
        "_id": enrol_id,
        "enrolment_id": enrol_id,
        "institution_id": inst_id,
        "student_id": payload.student_id,
        "student_name": payload.student_name,
        "roll_number": payload.roll_number,
        "academic_year": payload.academic_year,
        "programme_id": payload.programme_id,
        "programme_name": payload.programme_name,
        "class_id": payload.class_id,
        "class_name": payload.class_name,
        "section": payload.section,
        "semester": payload.semester,
        "status": "ACTIVE",
        "enrolled_date": now_str,
        "is_current": True,
        "remarks": payload.remarks or "Direct enrolment.",
    }

    await db["student_enrolments"].insert_one(doc)

    # Increment class enrolled_count if class_id provided
    if payload.class_id:
        await db["classes"].update_one({"_id": payload.class_id}, {"$inc": {"enrolled_count": 1}})

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="ENROL_STUDENT",
        subject=enrol_id,
        details=f"Enrolled {payload.student_name} into {payload.class_name or payload.programme_name} ({payload.academic_year}).",
        category="ACADEMIC_SETUP",
        ip_address=client_ip(request),
    )

    return StudentEnrolmentOut(**doc)


@router.get("/enrolments", response_model=List[StudentEnrolmentOut], summary="List student enrolments")
async def list_enrolments(
    student_id: Optional[str] = None,
    class_id: Optional[str] = None,
    programme_id: Optional[str] = None,
    academic_year: Optional[str] = None,
    is_current: Optional[bool] = Query(None),
    institution_id: Optional[str] = None,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> List[StudentEnrolmentOut]:
    """List student enrolments with filtering. Preserves all historical records."""
    target_inst_id = principal.get_scoped_institution_id(institution_id)

    query: dict[str, Any] = {}
    if target_inst_id:
        query["institution_id"] = target_inst_id
    if student_id:
        query["student_id"] = student_id
    if class_id:
        query["class_id"] = class_id
    if programme_id:
        query["programme_id"] = programme_id
    if academic_year:
        query["academic_year"] = academic_year
    if is_current is not None:
        query["is_current"] = is_current

    rows = await db["student_enrolments"].find(query).sort("enrolled_date", -1).to_list(300)
    return [
        StudentEnrolmentOut(
            enrolment_id=r.get("enrolment_id") or str(r["_id"]),
            institution_id=r.get("institution_id", ""),
            student_id=r.get("student_id", ""),
            student_name=r.get("student_name", ""),
            roll_number=r.get("roll_number"),
            academic_year=r.get("academic_year", ""),
            programme_id=r.get("programme_id"),
            programme_name=r.get("programme_name"),
            class_id=r.get("class_id"),
            class_name=r.get("class_name"),
            section=r.get("section"),
            semester=r.get("semester"),
            status=r.get("status", "ACTIVE"),
            enrolled_date=r.get("enrolled_date", ""),
            promoted_date=r.get("promoted_date"),
            is_current=r.get("is_current", True),
            remarks=r.get("remarks"),
        )
        for r in rows
    ]


@router.post("/enrolments/{enrolment_id}/promote", response_model=StudentEnrolmentOut, summary="Promote student to next academic year/level")
async def promote_student(
    enrolment_id: str,
    payload: StudentPromotionIn,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.MANAGE_ACADEMIC_SETUP)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> StudentEnrolmentOut:
    """Promote student. Marks current record as PROMOTED (is_current=False) and creates new active enrolment."""
    inst_id = principal.require_tenant_context()
    current_enrol = await db["student_enrolments"].find_one({"_id": enrolment_id})
    if not current_enrol:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrolment record not found.")
    principal.require_scope(current_enrol.get("institution_id", ""))

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # 1. Update existing enrolment as historical record
    await db["student_enrolments"].update_one(
        {"_id": enrolment_id},
        {"$set": {"is_current": False, "status": payload.promotion_status, "promoted_date": now_str}},
    )

    # 2. Insert new active enrolment for the promoted academic year
    new_enrol_id = f"ENR-{inst_id}-{secrets.token_hex(5)}"
    new_doc = {
        "_id": new_enrol_id,
        "enrolment_id": new_enrol_id,
        "institution_id": inst_id,
        "student_id": current_enrol["student_id"],
        "student_name": current_enrol["student_name"],
        "roll_number": current_enrol.get("roll_number"),
        "academic_year": payload.target_academic_year,
        "programme_id": current_enrol.get("programme_id"),
        "programme_name": current_enrol.get("programme_name"),
        "class_id": payload.target_class_id or current_enrol.get("class_id"),
        "class_name": payload.target_grade_or_semester,
        "section": payload.target_section or current_enrol.get("section"),
        "semester": (current_enrol.get("semester") or 1) + 1,
        "status": "ACTIVE",
        "enrolled_date": now_str,
        "is_current": True,
        "remarks": payload.remarks or f"Promoted from {current_enrol.get('academic_year')}.",
    }
    await db["student_enrolments"].insert_one(new_doc)

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="PROMOTE_STUDENT",
        subject=new_enrol_id,
        details=f"Promoted {current_enrol['student_name']} from {current_enrol['academic_year']} to {payload.target_academic_year} ({payload.target_grade_or_semester}).",
        category="ACADEMIC_SETUP",
        ip_address=client_ip(request),
    )

    return StudentEnrolmentOut(**new_doc)


@router.post("/enrolments/{enrolment_id}/transfer-section", response_model=StudentEnrolmentOut, summary="Transfer student to another section")
async def transfer_student_section(
    enrolment_id: str,
    payload: SectionTransferIn,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.MANAGE_ACADEMIC_SETUP)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> StudentEnrolmentOut:
    """Transfer student to another section while auditing the change and preserving history."""
    principal.require_tenant_context()
    enrol = await db["student_enrolments"].find_one({"_id": enrolment_id})
    if not enrol:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrolment record not found.")
    principal.require_scope(enrol.get("institution_id", ""))

    target_cls = await db["classes"].find_one({
        "_id": payload.target_class_id,
        "institution_id": enrol.get("institution_id"),
    })
    if not target_cls:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target class was not found in the student's institution.",
        )

    old_section = enrol.get("section", "")
    await db["student_enrolments"].update_one(
        {"_id": enrolment_id},
        {
            "$set": {
                "class_id": payload.target_class_id,
                "section": payload.target_section,
                "remarks": f"Transferred from Section {old_section} to {payload.target_section}. Reason: {payload.transfer_reason}",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        },
    )

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="TRANSFER_STUDENT_SECTION",
        subject=enrolment_id,
        details=f"Transferred {enrol['student_name']} from Section {old_section} to Section {payload.target_section}. Reason: {payload.transfer_reason}.",
        category="ACADEMIC_SETUP",
        ip_address=client_ip(request),
    )

    updated = await db["student_enrolments"].find_one({"_id": enrolment_id})
    return StudentEnrolmentOut(
        enrolment_id=str(updated["_id"]),
        institution_id=updated["institution_id"],
        student_id=updated["student_id"],
        student_name=updated["student_name"],
        roll_number=updated.get("roll_number"),
        academic_year=updated["academic_year"],
        programme_id=updated.get("programme_id"),
        programme_name=updated.get("programme_name"),
        class_id=updated.get("class_id"),
        class_name=updated.get("class_name"),
        section=updated.get("section"),
        semester=updated.get("semester"),
        status=updated.get("status", "ACTIVE"),
        enrolled_date=updated.get("enrolled_date", ""),
        promoted_date=updated.get("promoted_date"),
        is_current=updated.get("is_current", True),
        remarks=updated.get("remarks"),
    )


# ==============================================================================
# 9. Faculty & Class Assignments
# ==============================================================================

@router.post("/teacher-assignments", response_model=TeacherAssignmentOut, summary="Assign teacher to class/course")
async def create_teacher_assignment(
    payload: TeacherAssignmentIn,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.MANAGE_ACADEMIC_SETUP)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> TeacherAssignmentOut:
    """Allocate a faculty/teacher to a subject and class/programme."""
    inst_id = principal.require_tenant_context()
    assign_id = f"ASN-{inst_id}-{secrets.token_hex(5)}"

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
        "academic_year": payload.academic_year or "2025-26",
        "role_in_course": payload.role_in_course or "PRIMARY_INSTRUCTOR",
        "status": "ACTIVE",
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

    return TeacherAssignmentOut(**doc)


@router.get("/teacher-assignments", response_model=List[TeacherAssignmentOut], summary="List teacher assignments")
async def list_teacher_assignments(
    teacher_id: Optional[str] = None,
    target_id: Optional[str] = None,
    academic_year: Optional[str] = None,
    institution_id: Optional[str] = None,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> List[TeacherAssignmentOut]:
    """List allocations of teachers to classes/courses."""
    target_inst_id = principal.get_scoped_institution_id(institution_id)

    query: dict[str, Any] = {"status": "ACTIVE"}
    if target_inst_id:
        query["institution_id"] = target_inst_id
    if teacher_id:
        query["teacher_id"] = teacher_id
    if target_id:
        query["target_id"] = target_id
    if academic_year:
        query["academic_year"] = academic_year

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
            academic_year=r.get("academic_year", "2025-26"),
            role_in_course=r.get("role_in_course", "PRIMARY_INSTRUCTOR"),
            status=r.get("status", "ACTIVE"),
        )
        for r in rows
    ]


@router.delete("/teacher-assignments/{assignment_id}", summary="Remove teacher assignment")
async def delete_teacher_assignment(
    assignment_id: str,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.MANAGE_ACADEMIC_SETUP)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict[str, Any]:
    """Remove a teacher assignment."""
    principal.require_tenant_context()
    assignment = await db["teacher_assignments"].find_one({"_id": assignment_id})
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found.")
    principal.require_scope(assignment.get("institution_id", ""))

    await db["teacher_assignments"].delete_one({"_id": assignment_id})

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="DELETE_TEACHER_ASSIGNMENT",
        subject=assignment_id,
        details="Removed teacher allocation.",
        category="ACADEMIC_SETUP",
        ip_address=client_ip(request),
    )
    return {"status": "DELETED", "assignment_id": assignment_id}


# ==============================================================================
# 10. Academic Calendar Events
# ==============================================================================

@router.post("/calendar/events", response_model=AcademicCalendarEventOut, summary="Create academic calendar event")
async def create_calendar_event(
    payload: AcademicCalendarEventIn,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.MANAGE_ACADEMIC_SETUP)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> AcademicCalendarEventOut:
    """Create an academic calendar event (holiday, exam week, admission deadline)."""
    if payload.start_date > payload.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event start_date cannot follow end_date.",
        )

    inst_id = principal.require_tenant_context()
    event_id = f"EVT-{inst_id}-{secrets.token_hex(5)}"

    doc = {
        "_id": event_id,
        "event_id": event_id,
        "institution_id": inst_id,
        "academic_year": payload.academic_year,
        "title": payload.title,
        "description": payload.description,
        "event_type": payload.event_type,
        "start_date": payload.start_date,
        "end_date": payload.end_date,
        "target_audience": payload.target_audience,
        "is_holiday": payload.is_holiday,
        "timezone": payload.timezone,
    }

    await db["academic_calendar_events"].insert_one(doc)

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="CREATE_CALENDAR_EVENT",
        subject=event_id,
        details=f"Added calendar event '{payload.title}' ({payload.event_type}).",
        category="ACADEMIC_SETUP",
        ip_address=client_ip(request),
    )

    return AcademicCalendarEventOut(**doc)


@router.get("/calendar/events", response_model=List[AcademicCalendarEventOut], summary="List academic calendar events")
async def list_calendar_events(
    academic_year: Optional[str] = None,
    event_type: Optional[str] = None,
    institution_id: Optional[str] = None,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> List[AcademicCalendarEventOut]:
    """List academic calendar events for the caller's institution."""
    target_inst_id = principal.get_scoped_institution_id(institution_id)

    query: dict[str, Any] = {}
    if target_inst_id:
        query["institution_id"] = target_inst_id
    if academic_year:
        query["academic_year"] = academic_year
    if event_type:
        query["event_type"] = event_type

    rows = await db["academic_calendar_events"].find(query).sort("start_date", 1).to_list(200)
    return [
        AcademicCalendarEventOut(
            event_id=r.get("event_id") or str(r["_id"]),
            institution_id=r.get("institution_id", ""),
            academic_year=r.get("academic_year", ""),
            title=r.get("title", ""),
            description=r.get("description"),
            event_type=r.get("event_type", "INSTITUTION_EVENT"),
            start_date=r.get("start_date", ""),
            end_date=r.get("end_date", ""),
            target_audience=r.get("target_audience", "ALL"),
            is_holiday=r.get("is_holiday", False),
            timezone=r.get("timezone", "Asia/Kolkata"),
        )
        for r in rows
    ]


@router.delete("/calendar/events/{event_id}", summary="Delete academic calendar event")
async def delete_calendar_event(
    event_id: str,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.MANAGE_ACADEMIC_SETUP)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict[str, Any]:
    """Delete a calendar event."""
    principal.require_tenant_context()
    event_doc = await db["academic_calendar_events"].find_one({"_id": event_id})
    if not event_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")
    principal.require_scope(event_doc.get("institution_id", ""))

    await db["academic_calendar_events"].delete_one({"_id": event_id})

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="DELETE_CALENDAR_EVENT",
        subject=event_id,
        details="Deleted academic calendar event.",
        category="ACADEMIC_SETUP",
        ip_address=client_ip(request),
    )
    return {"status": "DELETED", "event_id": event_id}
