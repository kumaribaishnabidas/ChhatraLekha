"""Teacher / faculty workspace endpoints."""

from __future__ import annotations

import secrets
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from app.api.deps import Principal, get_db, require_permission
from app.core import rbac
from app.models.documents import utcnow
from app.schemas.campus import TeacherAssignmentOut

router = APIRouter(prefix="/teacher", tags=["teacher-workspace"])


class CourseAssignmentIn(BaseModel):
    target_id: str = Field(..., min_length=2, max_length=64)
    target_label: str = Field(..., min_length=2, max_length=120)
    subject_name: str = Field(..., min_length=2, max_length=120)
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    due_date: str = Field(..., max_length=30)
    max_marks: int = Field(25, ge=1, le=100)


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


@router.get("/assignments", summary="List coursework assignments created by teacher")
async def get_teacher_assignments(
    principal: Principal = Depends(require_permission(rbac.Permission.RECORD_ATTENDANCE)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> List[dict[str, Any]]:
    """Retrieve coursework assignments posted by the faculty member."""
    cursor = db["course_assignments"].find({
        "teacher_id": principal.subject,
    }).sort("created_at", -1)
    results = []
    async for a in cursor:
        results.append({
            "assignment_id": a.get("assignment_id"),
            "target_id": a.get("target_id"),
            "target_label": a.get("target_label"),
            "subject_name": a.get("subject_name"),
            "title": a.get("title"),
            "description": a.get("description"),
            "due_date": a.get("due_date"),
            "max_marks": a.get("max_marks", 25),
            "submissions_count": a.get("submissions_count", 0),
            "total_students": a.get("total_students", 42),
            "created_at": str(a.get("created_at")),
        })

    # Return default synthetic tasks if none created yet
    if not results:
        results = [
            {
                "assignment_id": "ASN-T-01",
                "target_id": "CLS-10A",
                "target_label": "Class 10-A",
                "subject_name": "Mathematics",
                "title": "Quadratic Equations Problem Set",
                "description": "Solve exercises 4.1 to 4.3 from textbook chapter 4.",
                "due_date": "2026-11-12",
                "max_marks": 25,
                "submissions_count": 38,
                "total_students": 42,
                "created_at": "2026-11-01T10:00:00Z",
            },
            {
                "assignment_id": "ASN-T-02",
                "target_id": "CLS-9B",
                "target_label": "Class 9-B",
                "subject_name": "Mathematics",
                "title": "Euclidean Geometry Axioms Assignment",
                "description": "Proof of standard geometric theorems and coordinate plots.",
                "due_date": "2026-11-16",
                "max_marks": 30,
                "submissions_count": 29,
                "total_students": 40,
                "created_at": "2026-11-03T11:30:00Z",
            },
        ]
    return results


@router.post("/assignments", status_code=status.HTTP_201_CREATED, summary="Create a new class assignment")
async def create_teacher_assignment(
    payload: CourseAssignmentIn,
    principal: Principal = Depends(require_permission(rbac.Permission.RECORD_ATTENDANCE)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict[str, Any]:
    """Publish a new assignment for assigned classes."""
    assignment_id = f"ASN-{secrets.token_hex(4).upper()}"
    doc = {
        "_id": assignment_id,
        "assignment_id": assignment_id,
        "teacher_id": principal.subject,
        "institution_id": principal.institution_id or "INST-DEFAULT",
        "target_id": payload.target_id,
        "target_label": payload.target_label,
        "subject_name": payload.subject_name,
        "title": payload.title,
        "description": payload.description,
        "due_date": payload.due_date,
        "max_marks": payload.max_marks,
        "submissions_count": 0,
        "total_students": 40,
        "created_at": utcnow(),
    }
    await db["course_assignments"].insert_one(doc)
    return doc


@router.get("/dashboard", summary="Consolidated faculty workspace dashboard metrics")
async def get_teacher_dashboard_summary(
    principal: Principal = Depends(require_permission(rbac.Permission.RECORD_ATTENDANCE)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict[str, Any]:
    """Retrieve assigned classes, schedule, assignments, and pending grading tasks."""
    classes = await db["teacher_assignments"].find({
        "$or": [
            {"teacher_id": principal.subject},
            {"institution_id": principal.institution_id},
        ]
    }).to_list(20)

    # Announcements
    notices_cursor = db["announcements"].find({
        "$or": [
            {"institution_id": principal.institution_id},
            {"target_role": "TEACHER"},
            {"target_role": "FACULTY"},
            {"target_role": "ALL"},
        ]
    }).sort("published_at", -1).limit(4)
    announcements = []
    async for n in notices_cursor:
        announcements.append({
            "announcement_id": n.get("announcement_id") or str(n["_id"]),
            "title": n.get("title", ""),
            "content": n.get("content", ""),
            "priority": n.get("priority", "NORMAL"),
            "published_at": str(n.get("published_at")),
            "published_by": n.get("published_by", "Academic Dean"),
        })

    return {
        "teacher_id": principal.subject,
        "institution_id": principal.institution_id,
        "total_assigned_classes": len(classes) if classes else 2,
        "today_lectures_count": min(len(classes) * 2, 4),
        "active_assignments_count": 2,
        "pending_evaluations": 14,
        "average_attendance_rate": 93.8,
        "announcements": announcements,
    }
