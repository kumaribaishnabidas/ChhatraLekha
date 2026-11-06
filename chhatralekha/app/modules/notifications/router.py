"""Notification Module REST Router."""

from __future__ import annotations

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query, Request, Response
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import Principal, client_ip, get_db, get_principal, require_permission
from app.core import rbac
from app.modules.notifications.schemas import (
    BroadcastNotificationRequest,
    DeviceTokenOut,
    DeviceTokenRegisterIn,
    NotificationOut,
    NotificationPageOut,
    NotificationPreferenceOut,
    NotificationPreferenceUpdate,
    UnreadCountOut,
)
from app.modules.notifications.service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notification-management"])


@router.get("", response_model=List[NotificationOut], summary="List in-app notifications")
async def list_notifications(
    response: Response,
    category: Optional[str] = Query(None, description="Category filter (ACADEMIC, ATTENDANCE, etc.)"),
    unread_only: bool = Query(False, description="Filter only unread notifications"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    page: Optional[int] = Query(None, ge=1),
    page_size: Optional[int] = Query(None, ge=1, le=100),
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> List[NotificationOut]:
    service = NotificationService(db)
    items = await service.list_notifications(
        principal,
        category=category,
        unread_only=unread_only,
        skip=skip,
        limit=limit,
        page=page,
        page_size=page_size,
    )
    response.headers["X-Total-Count"] = str(len(items))
    if page:
        response.headers["X-Page"] = str(page)
    if page_size:
        response.headers["X-Page-Size"] = str(page_size)
    return items


@router.get("/paged", response_model=NotificationPageOut, summary="List paginated notifications")
async def list_notifications_paged(
    category: Optional[str] = Query(None, description="Category filter"),
    unread_only: bool = Query(False, description="Filter only unread notifications"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> NotificationPageOut:
    service = NotificationService(db)
    return await service.list_notifications_paged(
        principal,
        category=category,
        unread_only=unread_only,
        page=page,
        page_size=page_size,
    )


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


@router.post("/devices", response_model=DeviceTokenOut, summary="Register mobile device token for push notifications")
async def register_device(
    payload: DeviceTokenRegisterIn,
    request: Request,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> DeviceTokenOut:
    service = NotificationService(db)
    return await service.register_device(principal, payload, client_ip(request))


@router.delete("/devices/{token}", summary="Revoke mobile device token for push notifications")
async def revoke_device(
    token: str,
    request: Request,
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict[str, Any]:
    service = NotificationService(db)
    return await service.revoke_device(principal, token, client_ip(request))


@router.get("/devices", response_model=List[DeviceTokenOut], summary="List registered device tokens")
async def list_devices(
    principal: Principal = Depends(get_principal),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> List[DeviceTokenOut]:
    service = NotificationService(db)
    return await service.list_devices(principal)


@router.post("/broadcast", response_model=NotificationOut, summary="Broadcast notification to role or class")
async def broadcast_notification(
    payload: BroadcastNotificationRequest,
    request: Request,
    principal: Principal = Depends(require_permission(rbac.Permission.MANAGE_ANNOUNCEMENTS)),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> NotificationOut:
    service = NotificationService(db)
    return await service.broadcast_notification(principal, payload, client_ip(request))
