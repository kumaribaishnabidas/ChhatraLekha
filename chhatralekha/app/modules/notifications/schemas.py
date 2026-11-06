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
    RESULTS = "RESULTS"
    TIMETABLE = "TIMETABLE"
    ANNOUNCEMENTS = "ANNOUNCEMENTS"
    ADMISSIONS = "ADMISSIONS"
    ADMINISTRATIVE = "ADMINISTRATIVE"
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


class DevicePlatform(str, Enum):
    ANDROID = "ANDROID"
    IOS = "IOS"


class NotificationOut(BaseModel):
    notification_id: str
    institution_id: str
    category: str
    priority: str
    title: str
    message: str
    deep_link: Optional[str] = None
    channels: Optional[List[str]] = Field(default_factory=lambda: ["IN_APP"])
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
    language_preference: str = "en"
    subscribed_categories: List[str] = Field(
        default_factory=lambda: [c.value for c in NotificationCategory]
    )


class NotificationPreferenceUpdate(BaseModel):
    in_app_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    language_preference: Optional[str] = None
    subscribed_categories: Optional[List[str]] = None


class BroadcastNotificationRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=150)
    message: str = Field(..., min_length=5, max_length=1000)
    category: NotificationCategory = NotificationCategory.ANNOUNCEMENTS
    priority: NotificationPriority = NotificationPriority.NORMAL
    target_role: Optional[str] = None
    target_class: Optional[str] = None
    deep_link: Optional[str] = None
    channels: Optional[List[DeliveryChannel]] = Field(
        default_factory=lambda: [DeliveryChannel.IN_APP]
    )
    institution_id: Optional[str] = None


class UnreadCountOut(BaseModel):
    unread_count: int
    urgent_count: int


class DeviceTokenRegisterIn(BaseModel):
    token: str = Field(..., min_length=10, max_length=512)
    platform: DevicePlatform
    device_name: Optional[str] = Field(None, max_length=100)
    device_model: Optional[str] = Field(None, max_length=100)
    app_version: Optional[str] = Field(None, max_length=50)


class DeviceTokenOut(BaseModel):
    device_id: str
    user_id: str
    token: str
    platform: str
    device_name: Optional[str] = None
    device_model: Optional[str] = None
    app_version: Optional[str] = None
    registered_at: str
    last_active_at: str


class NotificationDeliveryRecordOut(BaseModel):
    delivery_id: str
    notification_id: str
    channel: str
    recipient: str
    status: str
    attempt_count: int = 1
    sent_at: Optional[str] = None
    error_message: Optional[str] = None


class NotificationPageOut(BaseModel):
    items: List[NotificationOut]
    total: int
    page: int
    page_size: int
    total_pages: int
    unread_count: int
