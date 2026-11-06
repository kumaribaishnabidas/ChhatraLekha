"""Communication centre: targeted announcements and notifications."""

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
    require_permission,
)
from app.audit import writer
from app.core import rbac
from app.repositories.audit import AuditRepository
from app.schemas.campus import AnnouncementIn, AnnouncementOut, AnnouncementUpdateIn

router = APIRouter(prefix="/announcements", tags=["announcements"])


@router.post("", response_model=AnnouncementOut, summary="Publish targeted announcement")
async def create_announcement(
    payload: AnnouncementIn,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.MANAGE_ANNOUNCEMENTS)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> AnnouncementOut:
    """Create and broadcast an institution notice with scheduling and audience targeting."""
    inst_id = principal.require_tenant_context()
    ann_id = f"ANN-{secrets.token_hex(6)}"
    now = datetime.now(timezone.utc)

    # Determine status based on schedule
    is_scheduled = payload.scheduled_for is not None and payload.scheduled_for > now
    status_val = "SCHEDULED" if is_scheduled else "PUBLISHED"

    # Simulated audience delivery summary counts
    channels = payload.delivery_channels or ["IN_APP", "EMAIL"]
    delivery_summary = {
        "in_app": 150 if "IN_APP" in channels else 0,
        "email": 142 if "EMAIL" in channels else 0,
        "push": 118 if "PUSH" in channels else 0,
    }

    doc = {
        "_id": ann_id,
        "announcement_id": ann_id,
        "institution_id": inst_id,
        "title": payload.title,
        "content": payload.content,
        "priority": payload.priority.value,
        "target_scope": payload.target_scope.value,
        "target_id": payload.target_id,
        "target_label": payload.target_label,
        "target_role": payload.target_role,
        "target_departments": payload.target_departments or [],
        "target_classes": payload.target_classes or [],
        "scheduled_for": payload.scheduled_for,
        "expires_at": payload.expires_at,
        "delivery_channels": channels,
        "delivery_summary": delivery_summary,
        "status": status_val,
        "published_by": principal.subject,
        "published_at": now,
        "attachment_title": payload.attachment_title,
        "attachment_url": payload.attachment_url,
        "acknowledgements": [],
    }

    await db["announcements"].insert_one(doc)

    # Log asynchronous multi-channel simulation deliveries
    for ch in channels:
        del_rec = {
            "delivery_id": f"DEL-{secrets.token_hex(5)}",
            "notification_id": ann_id,
            "channel": ch,
            "recipient": f"AUDIENCE_{payload.target_scope.value}",
            "status": "SENT" if ch == "IN_APP" else "SIMULATED",
            "attempt_count": 1,
            "sent_at": now.isoformat(),
            "error_message": None,
        }
        await db["notification_deliveries"].insert_one(del_rec)

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="POST_ANNOUNCEMENT",
        subject=ann_id,
        details=f"Posted announcement '{payload.title}' with priority {payload.priority.value} and status {status_val}.",
        category="COMMUNICATION",
        ip_address=client_ip(request),
    )

    return AnnouncementOut(
        announcement_id=ann_id,
        institution_id=inst_id,
        title=payload.title,
        content=payload.content,
        priority=payload.priority.value,
        target_scope=payload.target_scope.value,
        target_id=payload.target_id,
        target_label=payload.target_label,
        target_role=payload.target_role,
        target_departments=payload.target_departments,
        target_classes=payload.target_classes,
        scheduled_for=payload.scheduled_for,
        expires_at=payload.expires_at,
        delivery_channels=channels,
        delivery_summary=delivery_summary,
        status=status_val,
        published_by=principal.subject,
        published_at=now,
        attachment_title=payload.attachment_title,
        attachment_url=payload.attachment_url,
        is_acknowledged=False,
    )


@router.put("/{announcement_id}", response_model=AnnouncementOut, summary="Update scheduled or published announcement")
async def update_announcement(
    announcement_id: str,
    payload: AnnouncementUpdateIn,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.MANAGE_ANNOUNCEMENTS)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> AnnouncementOut:
    """Edit announcement before or during publication with publisher authority check."""
    doc = await db["announcements"].find_one({"_id": announcement_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found.")

    # Authority check: must belong to caller's institution unless platform admin
    if principal.role not in {"aicte_admin", "platform_operator"}:
        if doc.get("institution_id") != principal.institution_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-institution edit prohibited.")

    updates: dict[str, Any] = {"updated_at": datetime.now(timezone.utc)}
    payload_data = payload.dict(exclude_unset=True)

    if "priority" in payload_data and payload_data["priority"] is not None:
        updates["priority"] = payload_data["priority"].value
    if "target_scope" in payload_data and payload_data["target_scope"] is not None:
        updates["target_scope"] = payload_data["target_scope"].value

    for field in [
        "title",
        "content",
        "target_id",
        "target_label",
        "target_role",
        "target_departments",
        "target_classes",
        "scheduled_for",
        "expires_at",
        "attachment_title",
        "attachment_url",
    ]:
        if field in payload_data:
            updates[field] = payload_data[field]

    # Re-evaluate status if scheduled_for is updated
    if "scheduled_for" in updates:
        now = datetime.now(timezone.utc)
        sched = updates["scheduled_for"]
        updates["status"] = "SCHEDULED" if sched and sched > now else "PUBLISHED"

    await db["announcements"].update_one({"_id": announcement_id}, {"$set": updates})

    updated_doc = await db["announcements"].find_one({"_id": announcement_id})

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="UPDATE_ANNOUNCEMENT",
        subject=announcement_id,
        details=f"Updated announcement '{updated_doc.get('title')}'.",
        category="COMMUNICATION",
        ip_address=client_ip(request),
    )

    user_sub = principal.subject
    return AnnouncementOut(
        announcement_id=updated_doc.get("announcement_id") or str(updated_doc["_id"]),
        institution_id=updated_doc.get("institution_id", ""),
        title=updated_doc.get("title", ""),
        content=updated_doc.get("content", ""),
        priority=updated_doc.get("priority", "NORMAL"),
        target_scope=updated_doc.get("target_scope", "ALL"),
        target_id=updated_doc.get("target_id"),
        target_label=updated_doc.get("target_label"),
        target_role=updated_doc.get("target_role"),
        target_departments=updated_doc.get("target_departments"),
        target_classes=updated_doc.get("target_classes"),
        scheduled_for=updated_doc.get("scheduled_for"),
        expires_at=updated_doc.get("expires_at"),
        delivery_channels=updated_doc.get("delivery_channels"),
        delivery_summary=updated_doc.get("delivery_summary"),
        status=updated_doc.get("status", "PUBLISHED"),
        published_by=updated_doc.get("published_by", ""),
        published_at=updated_doc.get("published_at", datetime.now(timezone.utc)),
        attachment_title=updated_doc.get("attachment_title"),
        attachment_url=updated_doc.get("attachment_url"),
        is_acknowledged=user_sub in updated_doc.get("acknowledgements", []),
    )


@router.get("", response_model=List[AnnouncementOut], summary="List permitted announcements")
async def list_announcements(
    target_id: Optional[str] = None,
    priority: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    include_expired: bool = Query(False),
    principal: Principal = Depends(require_permission(rbac.Permission.VIEW_ANNOUNCEMENTS)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> List[AnnouncementOut]:
    """List announcements targeted to the caller's institution, class, or role."""
    query: dict[str, Any] = {}
    target_inst_id = principal.get_scoped_institution_id()
    if target_inst_id:
        query["$or"] = [
            {"institution_id": target_inst_id},
            {"institution_id": "INST-ALL"},
        ]
    if priority:
        query["priority"] = priority
    if target_id:
        query["$or"] = query.get("$or", []) + [{"target_id": target_id}, {"target_scope": "ALL"}]

    now = datetime.now(timezone.utc)

    # Status handling: non-staff callers should not see upcoming scheduled notices
    is_staff = principal.role in {"school_admin", "college_admin", "university_admin", "teacher", "aicte_admin", "platform_operator"}
    if status_filter:
        query["status"] = status_filter
    elif not is_staff:
        # Hide scheduled notices that are not yet active
        query["$and"] = query.get("$and", []) + [
            {"$or": [{"status": "PUBLISHED"}, {"status": None}, {"scheduled_for": {"$lte": now}}]}
        ]

    if not include_expired:
        query["$and"] = query.get("$and", []) + [
            {"$or": [{"expires_at": None}, {"expires_at": {"$gte": now}}]}
        ]

    rows = await db["announcements"].find(query).sort("published_at", -1).to_list(100)
    user_sub = principal.subject
    return [
        AnnouncementOut(
            announcement_id=r.get("announcement_id") or str(r["_id"]),
            institution_id=r.get("institution_id", ""),
            title=r.get("title", ""),
            content=r.get("content", ""),
            priority=r.get("priority", "NORMAL"),
            target_scope=r.get("target_scope", "ALL"),
            target_id=r.get("target_id"),
            target_label=r.get("target_label"),
            target_role=r.get("target_role"),
            target_departments=r.get("target_departments"),
            target_classes=r.get("target_classes"),
            scheduled_for=r.get("scheduled_for"),
            expires_at=r.get("expires_at"),
            delivery_channels=r.get("delivery_channels"),
            delivery_summary=r.get("delivery_summary"),
            status=r.get("status", "PUBLISHED"),
            published_by=r.get("published_by", ""),
            published_at=r.get("published_at", datetime.now(timezone.utc)),
            attachment_title=r.get("attachment_title"),
            attachment_url=r.get("attachment_url"),
            is_acknowledged=user_sub in r.get("acknowledgements", []),
        )
        for r in rows
    ]


@router.get("/{announcement_id}/delivery-summary", summary="Get delivery statistics and audience breakdown")
async def get_announcement_delivery_summary(
    announcement_id: str,
    principal: Principal = Depends(require_permission(rbac.Permission.MANAGE_ANNOUNCEMENTS)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict[str, Any]:
    """Retrieve delivery performance and channel metrics for an announcement."""
    doc = await db["announcements"].find_one({"_id": announcement_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found.")

    principal.require_scope(doc.get("institution_id", ""))

    acks = doc.get("acknowledgements", [])
    ack_count = len(acks)
    summary = doc.get("delivery_summary", {"in_app": 150, "email": 142, "push": 118})
    total_delivered = summary.get("in_app", 150)
    ack_rate = round((ack_count / max(1, total_delivered)) * 100, 1)

    return {
        "announcement_id": announcement_id,
        "status": doc.get("status", "PUBLISHED"),
        "delivery_channels": doc.get("delivery_channels", ["IN_APP", "EMAIL"]),
        "delivery_summary": summary,
        "acknowledgements_count": ack_count,
        "acknowledgement_rate_percent": ack_rate,
        "published_at": doc.get("published_at"),
        "scheduled_for": doc.get("scheduled_for"),
        "expires_at": doc.get("expires_at"),
    }


@router.post("/{announcement_id}/acknowledge", summary="Acknowledge reading a notice")
async def acknowledge_announcement(
    announcement_id: str,
    principal: Principal = Depends(require_permission(rbac.Permission.VIEW_ANNOUNCEMENTS)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict[str, Any]:
    """Record receipt / read acknowledgement for an announcement."""
    doc = await db["announcements"].find_one({"_id": announcement_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found.")

    inst_scope = doc.get("institution_id")
    if inst_scope and inst_scope != "INST-ALL":
        principal.require_scope(inst_scope)

    await db["announcements"].update_one(
        {"_id": announcement_id},
        {"$addToSet": {"acknowledgements": principal.subject}},
    )
    return {"message": "Acknowledged successfully.", "announcement_id": announcement_id}
