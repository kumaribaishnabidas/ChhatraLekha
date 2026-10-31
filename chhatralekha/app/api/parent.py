"""Parent and guardian portal for linked student records."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import (
    Principal,
    client_ip,
    get_db,
    require_permission,
)
from app.audit import writer
from app.core import rbac
from app.models.enums import AssessmentStatus, GuardianVerificationStatus
from app.repositories.audit import AuditRepository
from app.schemas.campus import (
    AnnouncementOut,
    GuardianLinkRequestIn,
    GuardianLinkVerifyIn,
    GuardianStudentOverviewOut,
    StudentResultOut,
)

router = APIRouter(prefix="/parent", tags=["parent-portal"])


@router.post("/link", summary="Request linking parent account to a student")
async def request_guardian_link(
    payload: GuardianLinkRequestIn,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.VIEW_PARENT_PORTAL)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict[str, Any]:
    """Guardian initiates relationship link; requires institution verification before activation."""
    # Find matching student record by apaar_id or student_institute_roll_no
    student = await db["students"].find_one({
        "$or": [
            {"apaar_id": payload.student_identifier},
            {"student_institute_roll_no": payload.student_identifier},
        ]
    })
    if not student:
        raise HTTPException(status_code=404, detail="Student record not found in system.")

    # Verify matching date of birth
    if student.get("date_of_birth") != payload.student_dob:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student identification details do not match.",
        )

    link_id = f"GLINK-{secrets.token_hex(6)}"
    now = datetime.now(timezone.utc)

    link_doc = {
        "_id": link_id,
        "link_id": link_id,
        "parent_user_id": principal.subject,
        "parent_email": principal.email,
        "guardian_phone": payload.guardian_phone,
        "student_id": student.get("apaar_id") or str(student["_id"]),
        "student_name": student.get("student_name", ""),
        "institution_id": student.get("institution_id", ""),
        "relationship": payload.relationship.value,
        "status": GuardianVerificationStatus.PENDING.value,
        "requested_at": now,
        "verified_at": None,
    }

    await db["guardian_relationships"].insert_one(link_doc)

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="REQUEST_GUARDIAN_LINK",
        subject=student.get("apaar_id", ""),
        details=f"Guardian link requested for {student.get('student_name')}.",
        category="RELATIONSHIP",
        ip_address=client_ip(request),
    )

    return {"message": "Guardian link requested. Pending institution verification.", "link_id": link_id}


@router.post("/link/{link_id}/verify", summary="Institution approves guardian relationship")
async def verify_guardian_link(
    link_id: str,
    payload: GuardianLinkVerifyIn,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.ONBOARD_STUDENTS)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict[str, Any]:
    """Academic administrator or institution admin approves verified parent relationship."""
    link = await db["guardian_relationships"].find_one({"_id": link_id})
    if not link:
        raise HTTPException(status_code=404, detail="Link request not found.")

    principal.require_scope(link.get("institution_id"))

    now = datetime.now(timezone.utc)
    await db["guardian_relationships"].update_one(
        {"_id": link_id},
        {"$set": {"status": payload.verification_status.value, "verified_at": now, "verified_by": principal.subject}},
    )

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="VERIFY_GUARDIAN_LINK",
        subject=link.get("student_id", ""),
        details=f"Guardian link {link_id} set to {payload.verification_status.value}.",
        category="RELATIONSHIP",
        ip_address=client_ip(request),
    )

    return {"message": f"Guardian relationship status updated to {payload.verification_status.value}.", "link_id": link_id}


@router.get("/children", response_model=List[GuardianStudentOverviewOut], summary="List verified linked children")
async def list_linked_children(
    principal: Principal = Depends(require_permission(rbac.Permission.VIEW_PARENT_PORTAL)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> List[GuardianStudentOverviewOut]:
    """Guardian views permitted academic summaries of their verified linked children."""
    links = await db["guardian_relationships"].find({
        "parent_user_id": principal.subject,
        "status": GuardianVerificationStatus.VERIFIED.value,
    }).to_list(20)

    overviews: List[GuardianStudentOverviewOut] = []
    for link in links:
        stu_id = link.get("student_id")
        student = await db["students"].find_one({"apaar_id": stu_id}) or await db["students"].find_one({"_id": stu_id})
        inst_id = link.get("institution_id", "")
        inst = await db["institutions"].find_one({"institution_id": inst_id}) or {}

        # Attendance calculation
        records = await db["attendance_records"].find({"student_id": stu_id}).to_list(500)
        total_sessions = len(records)
        present = sum(1 for r in records if r.get("status") in {"PRESENT", "LATE"})
        rate = round((present / total_sessions * 100), 1) if total_sessions > 0 else 100.0

        # Published results only!
        marks = await db["assessment_marks"].find({"student_id": stu_id, "is_published": True}).to_list(50)
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

        # Recent notices
        notices = await db["announcements"].find({"institution_id": inst_id}).sort("published_at", -1).limit(5).to_list(5)
        parsed_notices = [
            AnnouncementOut(
                announcement_id=n.get("announcement_id") or str(n["_id"]),
                institution_id=n.get("institution_id", ""),
                title=n.get("title", ""),
                content=n.get("content", ""),
                priority=n.get("priority", "NORMAL"),
                target_scope=n.get("target_scope", "ALL"),
                target_id=n.get("target_id"),
                target_label=n.get("target_label"),
                target_role=n.get("target_role"),
                published_by=n.get("published_by", ""),
                published_at=n.get("published_at", datetime.now(timezone.utc)),
                attachment_title=n.get("attachment_title"),
                attachment_url=n.get("attachment_url"),
            )
            for n in notices
        ]

        overviews.append(
            GuardianStudentOverviewOut(
                link_id=str(link["_id"]),
                student_id=stu_id,
                student_name=link.get("student_name", ""),
                institution_id=inst_id,
                institution_name=inst.get("name", "Institution"),
                academic_period=(student.get("academic_year") if student else "Current"),
                class_or_programme=(student.get("program_id") if student else "Class/Course"),
                relationship=link.get("relationship", "GUARDIAN"),
                verification_status=link.get("status", "VERIFIED"),
                attendance_percentage=rate,
                total_sessions=total_sessions,
                present_sessions=present,
                published_results=results,
                recent_notices=parsed_notices,
            )
        )

    return overviews
