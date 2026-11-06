"""Notification Module Schemas."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class NotificationCategory(str, Enum):
    ACADEMIC = "ACADEMIC"
    ATTENDANCE = "ATTENDANCE"
    ASSIGNMENTS = "ASSIGNMENTS"
    EXAMINATIONS = "EXAMINATIONS"
    ANNOUNCEMENTS = "ANNOUNCEMENTS"
    SECURITY = "SECURITY"


class NotificationPriority(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class DeliveryChannel(str, Enum):
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    PUSH = "PUSH"


class NotificationOut(BaseModel):
    notification_id: str
    institution_id: str
    category: str
    priority: str
    title: str
    message: str
    deep_link: Optional[str] = None
    is_read: bool = False
    read_at: Optional[str] = None
    created_at: str


class NotificationPreferenceOut(BaseModel):
    user_id: str
    in_app_enabled: bool = True
    email_enabled: bool = True
    push_enabled: bool = True
    quiet_hours_enabled: bool = False
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "07:00"
    subscribed_categories: List[str] = Field(
        default_factory=lambda: [
            "ACADEMIC",
            "ATTENDANCE",
            "ASSIGNMENTS",
            "EXAMINATIONS",
            "ANNOUNCEMENTS",
            "SECURITY",
        ]
    )


class NotificationPreferenceUpdate(BaseModel):
    in_app_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    subscribed_categories: Optional[List[str]] = None


class BroadcastNotificationRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=150)
    message: str = Field(..., min_length=5, max_length=1000)
    category: NotificationCategory = NotificationCategory.ANNOUNCEMENTS
    priority: NotificationPriority = NotificationPriority.NORMAL
    target_role: Optional[str] = None
    target_class: Optional[str] = None
    deep_link: Optional[str] = None
    institution_id: Optional[str] = None


class UnreadCountOut(BaseModel):
    unread_count: int
    urgent_count: int
