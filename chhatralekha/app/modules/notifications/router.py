"""Notification Module REST Router."""

from __future__ import annotations

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query, Request
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import Principal, client_ip, get_db, get_principal, require_permission
from app.core import rbac
from app.modules.notifications.schemas import (
    BroadcastNotificationRequest,
    NotificationOut,
    NotificationPreferenceOut,
    NotificationPreferenceUpdate,
    UnreadCountOut,
)
from app.modules.notifications.service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notification-management"])


@router.get("", response_model=List[NotificationOut], summary="List in-app notifications")
async def list_notifications(
    category: Optional[str] = Query(None, description="Category filter (ACADEMIC, ATTENDANCE, etc.)"),
    unread_only: bool = Query(False, description="Filter only unread notifications"),
    limit: int = Query(50, ge=1, le=100),
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> List[NotificationOut]:
    service = NotificationService(db)
    return await service.list_notifications(principal, category=category, unread_only=unread_only, limit=limit)


@router.get("/unread-count", response_model=UnreadCountOut, summary="Get count of unread notifications")
async def get_unread_count(
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> UnreadCountOut:
    service = NotificationService(db)
    return await service.get_unread_count(principal)


@router.post("/{notification_id}/read", summary="Mark notification as read")
async def mark_notification_read(
    notification_id: str,
    request: Request,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict[str, Any]:
    service = NotificationService(db)
    return await service.mark_as_read(principal, notification_id, client_ip(request))


@router.post("/read-all", summary="Mark all notifications as read")
async def mark_all_notifications_read(
    request: Request,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict[str, Any]:
    service = NotificationService(db)
    return await service.mark_all_as_read(principal, client_ip(request))


@router.delete("/{notification_id}", summary="Delete or dismiss notification")
async def delete_notification(
    notification_id: str,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict[str, Any]:
    service = NotificationService(db)
    return await service.delete_notification(principal, notification_id)


@router.get("/preferences", response_model=NotificationPreferenceOut, summary="Get notification preferences")
async def get_preferences(
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> NotificationPreferenceOut:
    service = NotificationService(db)
    return await service.get_preferences(principal)


@router.put("/preferences", response_model=NotificationPreferenceOut, summary="Update notification preferences and quiet hours")
async def update_preferences(
    payload: NotificationPreferenceUpdate,
    request: Request,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> NotificationPreferenceOut:
    service = NotificationService(db)
    return await service.update_preferences(principal, payload, client_ip(request))


@router.post("/broadcast", response_model=NotificationOut, summary="Broadcast notification to role or class")
async def broadcast_notification(
    payload: BroadcastNotificationRequest,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.MANAGE_ANNOUNCEMENTS)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> NotificationOut:
    service = NotificationService(db)
    return await service.broadcast_notification(principal, payload, client_ip(request))

