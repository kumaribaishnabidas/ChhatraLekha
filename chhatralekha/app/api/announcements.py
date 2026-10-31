"""Communication centre: targeted announcements and notifications."""

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
    require_permission,
)
from app.audit import writer
from app.core import rbac
from app.repositories.audit import AuditRepository
from app.schemas.campus import AnnouncementIn, AnnouncementOut

router = APIRouter(prefix="/announcements", tags=["announcements"])


@router.post("", response_model=AnnouncementOut, summary="Publish targeted announcement")
async def create_announcement(
    payload: AnnouncementIn,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.MANAGE_ANNOUNCEMENTS)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> AnnouncementOut:
    """Create and broadcast an institution notice."""
    inst_id = principal.institution_id or "INST-DEFAULT"
    ann_id = f"ANN-{secrets.token_hex(6)}"
    now = datetime.now(timezone.utc)

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
        "published_by": principal.subject,
        "published_at": now,
        "attachment_title": payload.attachment_title,
        "attachment_url": payload.attachment_url,
        "acknowledgements": [],
    }

    await db["announcements"].insert_one(doc)

    await writer.log(
        AuditRepository(db["audit_events"]),
        actor=principal.subject,
        actor_role=principal.role,
        action="POST_ANNOUNCEMENT",
        subject=ann_id,
        details=f"Posted announcement '{payload.title}' with priority {payload.priority.value}.",
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
        published_by=principal.subject,
        published_at=now,
        attachment_title=payload.attachment_title,
        attachment_url=payload.attachment_url,
        is_acknowledged=False,
    )


@router.get("", response_model=List[AnnouncementOut], summary="List permitted announcements")
async def list_announcements(
    target_id: Optional[str] = None,
    priority: Optional[str] = None,
    principal: Principal = Depends(require_permission(rbac.Permission.VIEW_ANNOUNCEMENTS)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> List[AnnouncementOut]:
    """List announcements targeted to the caller's institution, class, or role."""
    query: dict[str, Any] = {}
    if principal.role not in {"aicte_admin", "platform_operator"} and principal.institution_id:
        query["$or"] = [
            {"institution_id": principal.institution_id},
            {"institution_id": "INST-ALL"},
        ]
    if priority:
        query["priority"] = priority
    if target_id:
        query["$or"] = query.get("$or", []) + [{"target_id": target_id}, {"target_scope": "ALL"}]

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
            published_by=r.get("published_by", ""),
            published_at=r.get("published_at", datetime.now(timezone.utc)),
            attachment_title=r.get("attachment_title"),
            attachment_url=r.get("attachment_url"),
            is_acknowledged=user_sub in r.get("acknowledgements", []),
        )
        for r in rows
    ]


@router.post("/{announcement_id}/acknowledge", summary="Acknowledge reading a notice")
async def acknowledge_announcement(
    announcement_id: str,
    principal: Principal = Depends(require_permission(rbac.Permission.VIEW_ANNOUNCEMENTS)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict[str, Any]:
    """Record receipt / read acknowledgement for an announcement."""
    res = await db["announcements"].update_one(
        {"_id": announcement_id},
        {"$addToSet": {"acknowledgements": principal.subject}},
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found.")
    return {"message": "Acknowledged successfully.", "announcement_id": announcement_id}
