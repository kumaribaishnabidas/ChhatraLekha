"""Teacher / faculty workspace endpoints."""

from __future__ import annotations

from typing import Any, List

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import Principal, get_db, require_permission
from app.core import rbac
from app.schemas.campus import TeacherAssignmentOut

router = APIRouter(prefix="/teacher", tags=["teacher-workspace"])


@router.get("/classes", response_model=List[TeacherAssignmentOut], summary="List assigned classes for signed-in teacher")
async def get_teacher_classes(
    principal: Principal = Depends(require_permission(rbac.Permission.RECORD_ATTENDANCE)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> List[TeacherAssignmentOut]:
    """Retrieve the classes and subjects allocated to the teacher."""
    teacher_id = principal.subject
    rows = await db["teacher_assignments"].find({
        "$or": [
            {"teacher_id": teacher_id},
            {"institution_id": principal.institution_id},
        ]
    }).to_list(100)

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


@router.get("/timetable", summary="Get teacher timetable")
async def get_teacher_timetable(
    principal: Principal = Depends(require_permission(rbac.Permission.RECORD_ATTENDANCE)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> List[dict[str, Any]]:
    """Retrieve weekly schedule and assigned periods."""
    assignments = await db["teacher_assignments"].find({
        "teacher_id": principal.subject
    }).to_list(50)

    # Basic timetable entries derived from assignments
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    schedule = []
    period = 1
    for a in assignments:
        for day in days[:3]:
            schedule.append({
                "day": day,
                "period": period,
                "time": f"{8 + period}:00 - {9 + period}:00",
                "target_label": a.get("target_label"),
                "subject_name": a.get("subject_name"),
            })
            period = (period % 5) + 1
    return schedule
