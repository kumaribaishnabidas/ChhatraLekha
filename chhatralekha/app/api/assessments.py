"""Examination, grading, and result management."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
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
from app.models.enums import AssessmentStatus
from app.repositories.audit import AuditRepository
from app.schemas.campus import (
    AssessmentIn,
    AssessmentMarksSubmitIn,
    AssessmentOut,
    StudentResultOut,
)

router = APIRouter(prefix="/assessments", tags=["assessments"])


def _calculate_grade(pct: float) -> str:
    if pct >= 90:
        return "A+"
    if pct >= 80:
        return "A"
    if pct >= 70:
        return "B+"
    if pct >= 60:
        return "B"
    if pct >= 50:
        return "C"
    if pct >= 35:
        return "D"
    return "F"


@router.post("", response_model=AssessmentOut, summary="Create an assessment")
async def create_assessment(
    payload: AssessmentIn,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.MANAGE_ACADEMIC_SETUP)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> AssessmentOut:
    """Create a new exam or assessment in DRAFT status."""
    inst_id = principal.institution_id or "INST-DEFAULT"
    assessment_id = f"ASM-{secrets.token_hex(6)}"

    doc = {
        "_id": assessment_id,
        "assessment_id": assessment_id,
        "institution_id": inst_id,
        "name": payload.name,
        "academic_year": payload.academic_year,
        "term": payload.term,
        "target_type": payload.target_type,
        "target_id": payload.target_id,
        "target_label": payload.target_label,
        "subject_id": payload.subject_id,
        "subject_name": payload.subject_name,
        "max_marks": payload.max_marks,
        "passing_marks": payload.passing_marks,
        "status": AssessmentStatus.DRAFT.value,
        "created_by": principal.subject,
        "created_at": datetime.now(timezone.utc),
    }

    await db["assessments"].insert_one(doc)

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="CREATE_ASSESSMENT",
        subject=assessment_id,
        details=f"Created assessment {payload.name} for {payload.target_label} ({payload.subject_name}).",
        category="ASSESSMENT",
        ip_address=client_ip(request),
    )

    return AssessmentOut(
        assessment_id=assessment_id,
        institution_id=inst_id,
        name=payload.name,
        academic_year=payload.academic_year,
        term=payload.term,
        target_type=payload.target_type,
        target_id=payload.target_id,
        target_label=payload.target_label,
        subject_id=payload.subject_id,
        subject_name=payload.subject_name,
        max_marks=payload.max_marks,
        passing_marks=payload.passing_marks,
        status=AssessmentStatus.DRAFT,
        created_by=principal.subject,
    )


@router.post("/{assessment_id}/marks", summary="Enter draft marks for an assessment")
async def enter_assessment_marks(
    assessment_id: str,
    payload: AssessmentMarksSubmitIn,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.RECORD_MARKS)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict[str, Any]:
    """Faculty enters or updates draft student marks."""
    asm = await db["assessments"].find_one({"_id": assessment_id})
    if not asm:
        raise HTTPException(status_code=404, detail="Assessment not found.")

    if asm.get("status") == AssessmentStatus.PUBLISHED.value:
        raise HTTPException(
            status_code=400,
            detail="Cannot edit marks directly on a PUBLISHED assessment. Use correction workflow.",
        )

    principal.require_scope(asm.get("institution_id"))

    # Upsert marks
    now = datetime.now(timezone.utc)
    for item in payload.marks:
        pct = (item.marks_obtained / asm["max_marks"]) * 100.0 if asm["max_marks"] > 0 else 0
        grade = _calculate_grade(pct)
        passed = item.marks_obtained >= asm.get("passing_marks", 35.0)

        mark_doc = {
            "assessment_id": assessment_id,
            "institution_id": asm["institution_id"],
            "student_id": item.student_id,
            "student_name": item.student_name,
            "marks_obtained": item.marks_obtained,
            "max_marks": asm["max_marks"],
            "passing_marks": asm["passing_marks"],
            "percentage": round(pct, 2),
            "grade": grade,
            "status": "PASS" if passed else "FAIL",
            "is_absent": item.is_absent,
            "remarks": item.remarks,
            "entered_by": principal.subject,
            "updated_at": now,
        }
        await db["assessment_marks"].update_one(
            {"assessment_id": assessment_id, "student_id": item.student_id},
            {"$set": mark_doc},
            upsert=True,
        )

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="ENTER_MARKS",
        subject=assessment_id,
        details=f"Draft marks entered for {len(payload.marks)} students.",
        category="ASSESSMENT",
        ip_address=client_ip(request),
    )

    return {"message": f"Successfully recorded marks for {len(payload.marks)} students.", "assessment_id": assessment_id}


@router.post("/{assessment_id}/publish", response_model=AssessmentOut, summary="Moderate and publish assessment results")
async def publish_assessment_results(
    assessment_id: str,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.PUBLISH_RESULTS)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> AssessmentOut:
    """Authorize and publish assessment results to students and parents."""
    asm = await db["assessments"].find_one({"_id": assessment_id})
    if not asm:
        raise HTTPException(status_code=404, detail="Assessment not found.")

    principal.require_scope(asm.get("institution_id"))
    now = datetime.now(timezone.utc)

    await db["assessments"].update_one(
        {"_id": assessment_id},
        {"$set": {"status": AssessmentStatus.PUBLISHED.value, "published_by": principal.subject, "published_at": now}},
    )

    # Mark all child marks as published
    await db["assessment_marks"].update_many(
        {"assessment_id": assessment_id},
        {"$set": {"is_published": True, "published_at": now}},
    )

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="PUBLISH_ASSESSMENT",
        subject=assessment_id,
        details=f"Assessment {asm.get('name')} published.",
        category="ASSESSMENT",
        ip_address=client_ip(request),
    )

    updated = await db["assessments"].find_one({"_id": assessment_id})
    return AssessmentOut(
        assessment_id=assessment_id,
        institution_id=updated.get("institution_id"),
        name=updated.get("name"),
        academic_year=updated.get("academic_year"),
        term=updated.get("term"),
        target_type=updated.get("target_type"),
        target_id=updated.get("target_id"),
        target_label=updated.get("target_label"),
        subject_id=updated.get("subject_id"),
        subject_name=updated.get("subject_name"),
        max_marks=updated.get("max_marks"),
        passing_marks=updated.get("passing_marks"),
        status=AssessmentStatus(updated.get("status")),
        created_by=updated.get("created_by"),
        published_by=updated.get("published_by"),
        published_at=updated.get("published_at"),
    )


@router.get("", response_model=List[AssessmentOut], summary="List assessments")
async def list_assessments(
    target_id: Optional[str] = None,
    academic_year: Optional[str] = None,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> List[AssessmentOut]:
    """List assessments for the institution."""
    query: dict[str, Any] = {}
    if principal.role not in {"aicte_admin", "platform_operator"} and principal.institution_id:
        query["institution_id"] = principal.institution_id
    if target_id:
        query["target_id"] = target_id
    if academic_year:
        query["academic_year"] = academic_year

    rows = await db["assessments"].find(query).sort("created_at", -1).to_list(100)
    return [
        AssessmentOut(
            assessment_id=r.get("assessment_id") or str(r["_id"]),
            institution_id=r.get("institution_id", ""),
            name=r.get("name", ""),
            academic_year=r.get("academic_year", ""),
            term=r.get("term", ""),
            target_type=r.get("target_type", "CLASS"),
            target_id=r.get("target_id", ""),
            target_label=r.get("target_label", ""),
            subject_id=r.get("subject_id", ""),
            subject_name=r.get("subject_name", ""),
            max_marks=r.get("max_marks", 100.0),
            passing_marks=r.get("passing_marks", 35.0),
            status=AssessmentStatus(r.get("status", "DRAFT")),
            created_by=r.get("created_by", ""),
            published_by=r.get("published_by"),
            published_at=r.get("published_at"),
        )
        for r in rows
    ]


@router.get("/my-results", response_model=List[StudentResultOut], summary="Fetch published results for student")
async def get_my_results(
    student_id: Optional[str] = None,
    principal: Principal = Depends(require_permission(rbac.Permission.VIEW_RESULTS)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> List[StudentResultOut]:
    """Fetch only PUBLISHED examination results for the signed-in student or linked parent."""
    resolved_id = student_id or principal.apaar_id or principal.subject

    # Ensure marks are published before releasing
    marks = await db["assessment_marks"].find({"student_id": resolved_id, "is_published": True}).to_list(100)
    results: List[StudentResultOut] = []
    for m in marks:
        asm = await db["assessments"].find_one({"_id": m["assessment_id"]})
        if asm and asm.get("status") == AssessmentStatus.PUBLISHED.value:
            results.append(
                StudentResultOut(
                    assessment_id=m["assessment_id"],
                    assessment_name=asm.get("name", ""),
                    term=asm.get("term", ""),
                    subject_name=asm.get("subject_name", ""),
                    max_marks=m.get("max_marks", 100.0),
                    passing_marks=m.get("passing_marks", 35.0),
                    marks_obtained=m.get("marks_obtained", 0.0),
                    percentage=m.get("percentage", 0.0),
                    grade=m.get("grade", "N/A"),
                    status=m.get("status", "PASS"),
                    published_at=m.get("published_at"),
                )
            )
    return results
