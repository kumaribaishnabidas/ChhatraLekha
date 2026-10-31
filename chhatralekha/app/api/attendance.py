"""Attendance tracking module for Schools and Colleges."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Request
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import (
    Principal,
    client_ip,
    get_db,
    require_permission,
)
from app.audit import writer
from app.core import rbac
from app.models.enums import AttendanceMode, AttendanceStatus
from app.repositories.audit import AuditRepository
from app.schemas.campus import (
    AttendanceBatchSubmitIn,
    AttendanceSessionOut,
)

router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.post("/sessions", response_model=AttendanceSessionOut, summary="Submit class attendance session")
async def record_attendance_session(
    payload: AttendanceBatchSubmitIn,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.RECORD_ATTENDANCE)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> AttendanceSessionOut:
    """Record an attendance session (daily or period-wise) with student marks."""
    inst_id = principal.institution_id or "INST-DEFAULT"
    session_id = f"ATT-{secrets.token_hex(6)}"
    now = datetime.now(timezone.utc)

    # Compute tally
    total = len(payload.records)
    present = sum(1 for r in payload.records if r.status == AttendanceStatus.PRESENT)
    absent = sum(1 for r in payload.records if r.status == AttendanceStatus.ABSENT)
    late = sum(1 for r in payload.records if r.status == AttendanceStatus.LATE)

    session_doc = {
        "_id": session_id,
        "session_id": session_id,
        "institution_id": inst_id,
        "session_date": payload.session_date,
        "mode": payload.mode.value,
        "period_number": payload.period_number,
        "target_type": payload.target_type,
        "target_id": payload.target_id,
        "target_label": payload.target_label,
        "recorded_by": principal.subject,
        "total_students": total,
        "present_count": present,
        "absent_count": absent,
        "late_count": late,
        "created_at": now,
    }

    # Insert individual attendance records for history & student/parent views
    record_docs = [
        {
            "session_id": session_id,
            "institution_id": inst_id,
            "session_date": payload.session_date,
            "student_id": r.student_id,
            "student_name": r.student_name,
            "status": r.status.value,
            "remarks": r.remarks,
            "target_id": payload.target_id,
            "target_label": payload.target_label,
            "recorded_by": principal.subject,
            "created_at": now,
        }
        for r in payload.records
    ]

    await db["attendance_sessions"].insert_one(session_doc)
    if record_docs:
        await db["attendance_records"].insert_many(record_docs)

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="RECORD_ATTENDANCE",
        subject=session_id,
        details=f"Attendance recorded for {payload.target_label} on {payload.session_date}: {present}/{total} present.",
        category="ATTENDANCE",
        ip_address=client_ip(request),
    )

    return AttendanceSessionOut(
        session_id=session_id,
        institution_id=inst_id,
        session_date=payload.session_date,
        mode=payload.mode.value,
        period_number=payload.period_number,
        target_type=payload.target_type,
        target_id=payload.target_id,
        target_label=payload.target_label,
        recorded_by=principal.subject,
        total_students=total,
        present_count=present,
        absent_count=absent,
        late_count=late,
    )


@router.get("/sessions", response_model=List[AttendanceSessionOut], summary="List attendance sessions")
async def list_attendance_sessions(
    target_id: Optional[str] = None,
    session_date: Optional[str] = None,
    principal: Principal = Depends(require_permission(rbac.Permission.VIEW_ATTENDANCE)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> List[AttendanceSessionOut]:
    """List historical attendance sessions."""
    query: dict[str, Any] = {}
    if principal.role not in {"aicte_admin", "platform_operator"} and principal.institution_id:
        query["institution_id"] = principal.institution_id
    if target_id:
        query["target_id"] = target_id
    if session_date:
        query["session_date"] = session_date

    rows = await db["attendance_sessions"].find(query).sort("session_date", -1).to_list(100)
    return [
        AttendanceSessionOut(
            session_id=r.get("session_id") or str(r["_id"]),
            institution_id=r.get("institution_id", ""),
            session_date=r.get("session_date", ""),
            mode=r.get("mode", AttendanceMode.DAILY.value),
            period_number=r.get("period_number"),
            target_type=r.get("target_type", "CLASS"),
            target_id=r.get("target_id", ""),
            target_label=r.get("target_label", ""),
            recorded_by=r.get("recorded_by", ""),
            total_students=r.get("total_students", 0),
            present_count=r.get("present_count", 0),
            absent_count=r.get("absent_count", 0),
            late_count=r.get("late_count", 0),
        )
        for r in rows
    ]


@router.get("/my-summary", summary="Get student attendance summary")
async def get_my_attendance_summary(
    student_id: Optional[str] = None,
    principal: Principal = Depends(require_permission(rbac.Permission.VIEW_ATTENDANCE)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict[str, Any]:
    """Retrieve attendance tally and percentage for a student."""
    resolved_id = student_id or principal.apaar_id or principal.subject
    records = await db["attendance_records"].find({"student_id": resolved_id}).to_list(500)
    total = len(records)
    present = sum(1 for r in records if r.get("status") in {"PRESENT", "LATE"})
    absent = sum(1 for r in records if r.get("status") == "ABSENT")
    rate = round((present / total * 100), 1) if total > 0 else 100.0

    return {
        "student_id": resolved_id,
        "total_sessions": total,
        "present_sessions": present,
        "absent_sessions": absent,
        "attendance_rate": rate,
        "recent_records": [
            {
                "session_date": r.get("session_date"),
                "status": r.get("status"),
                "target_label": r.get("target_label"),
                "remarks": r.get("remarks"),
            }
            for r in records[-10:]
        ],
    }
