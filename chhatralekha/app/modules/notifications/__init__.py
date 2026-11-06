"""Notification Module Export."""

from app.modules.notifications.router import router
from app.modules.notifications.schemas import (
    BroadcastNotificationRequest,
    DeliveryChannel,
    NotificationCategory,
    NotificationOut,
    NotificationPreferenceOut,
    NotificationPreferenceUpdate,
    NotificationPriority,
    UnreadCountOut,
)
from app.modules.notifications.service import NotificationService

__all__ = [
    "router",
    "NotificationService",
    "NotificationCategory",
    "NotificationPriority",
    "DeliveryChannel",
    "NotificationOut",
    "NotificationPreferenceOut",
    "NotificationPreferenceUpdate",
    "BroadcastNotificationRequest",
    "UnreadCountOut",
]
