"""Notification Module Business Service."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any, List, Optional

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import Principal
from app.audit import writer
from app.core.config import get_settings
from app.models.documents import utcnow
from app.modules.notifications.schemas import (
    BroadcastNotificationRequest,
    DeviceTokenOut,
    DeviceTokenRegisterIn,
    NotificationCategory,
    NotificationDeliveryRecordOut,
    NotificationOut,
    NotificationPageOut,
    NotificationPreferenceOut,
    NotificationPreferenceUpdate,
    UnreadCountOut,
)
from app.repositories.audit import AuditRepository

settings = get_settings()

ALL_NOTIFICATION_CATEGORIES = [c.value for c in NotificationCategory]

SAMPLE_NOTIFICATIONS_SEED = [
    {
        "notification_id": "ntf-01",
        "category": "ATTENDANCE",
        "priority": "HIGH",
        "title": "Monthly Attendance Summary (October 2024)",
        "message": "Your overall attendance for October 2024 is recorded at 94.2%. Keep up the good work.",
        "deep_link": "/me/attendance",
        "channels": ["IN_APP", "EMAIL"],
        "is_read": False,
        "created_at": datetime(2024, 11, 1, 9, 30, tzinfo=timezone.utc),
    },
    {
        "notification_id": "ntf-02",
        "category": "ASSIGNMENTS",
        "priority": "NORMAL",
        "title": "New Assignment: Database Relational Normalization",
        "message": "Problem Set 4 for Database Systems has been published. Submission deadline: Friday, 15 November.",
        "deep_link": "/me/assignments",
        "channels": ["IN_APP"],
        "is_read": False,
        "created_at": datetime(2024, 10, 30, 14, 15, tzinfo=timezone.utc),
    },
    {
        "notification_id": "ntf-03",
        "category": "EXAMINATIONS",
        "priority": "URGENT",
        "title": "Mid-Term Examination Schedule Released",
        "message": "The mid-term examination timetable for Semester 5 has been officially published.",
        "deep_link": "/me/results",
        "channels": ["IN_APP", "PUSH"],
        "is_read": True,
        "created_at": datetime(2024, 10, 28, 11, 0, tzinfo=timezone.utc),
    },
    {
        "notification_id": "ntf-04",
        "category": "ANNOUNCEMENTS",
        "priority": "NORMAL",
        "title": "National Digital Library of India Access Enabled",
        "message": "Students and faculty can now access NDLI digital repositories using institutional single sign-on.",
        "deep_link": "/announcements",
        "channels": ["IN_APP", "EMAIL"],
        "is_read": True,
        "created_at": datetime(2024, 10, 25, 16, 45, tzinfo=timezone.utc),
    },
    {
        "notification_id": "ntf-05",
        "category": "SECURITY",
        "priority": "NORMAL",
        "title": "New Web Session Authenticated",
        "message": "Your ChhatraLekha account was signed into from a new browser session.",
        "deep_link": "/profile",
        "channels": ["IN_APP", "EMAIL", "PUSH"],
        "is_read": True,
        "created_at": datetime(2024, 10, 24, 8, 20, tzinfo=timezone.utc),
    },
    {
        "notification_id": "ntf-06",
        "category": "RESULTS",
        "priority": "HIGH",
        "title": "Semester Grade Card Published",
        "message": "Your validated term report card for Semester 4 is now available in your academic wallet.",
        "deep_link": "/me/results",
        "channels": ["IN_APP", "EMAIL"],
        "is_read": False,
        "created_at": datetime(2024, 10, 20, 10, 15, tzinfo=timezone.utc),
    },
    {
        "notification_id": "ntf-07",
        "category": "TIMETABLE",
        "priority": "NORMAL",
        "title": "Timetable Reschedule: Physics Lab",
        "message": "Physics Laboratory session on Wednesday has been rescheduled from 10:00 AM to 02:00 PM.",
        "deep_link": "/me",
        "channels": ["IN_APP", "PUSH"],
        "is_read": False,
        "created_at": datetime(2024, 10, 18, 14, 0, tzinfo=timezone.utc),
    },
    {
        "notification_id": "ntf-08",
        "category": "ADMISSIONS",
        "priority": "NORMAL",
        "title": "Elective Course Registration Window",
        "message": "Admissions office has opened enrollment for open elective courses for the upcoming term.",
        "deep_link": "/announcements",
        "channels": ["IN_APP"],
        "is_read": True,
        "created_at": datetime(2024, 10, 15, 9, 0, tzinfo=timezone.utc),
    },
    {
        "notification_id": "ntf-09",
        "category": "ADMINISTRATIVE",
        "priority": "NORMAL",
        "title": "Institutional Fee Clearance Reminder",
        "message": "Tuition clearance receipts for the academic semester are ready for digital download.",
        "deep_link": "/me",
        "channels": ["IN_APP", "EMAIL"],
        "is_read": True,
        "created_at": datetime(2024, 10, 10, 11, 30, tzinfo=timezone.utc),
    },
    {
        "notification_id": "ntf-10",
        "category": "ACADEMIC",
        "priority": "HIGH",
        "title": "Academic Council Curriculum Advisory",
        "message": "Updated syllabus guidelines complying with the National Curriculum Framework are now in effect.",
        "deep_link": "/announcements",
        "channels": ["IN_APP"],
        "is_read": False,
        "created_at": datetime(2024, 10, 5, 8, 45, tzinfo=timezone.utc),
    },
]


class NotificationService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db
        self.audit_repo = AuditRepository(db["audit_events"])

    def _build_user_query(
        self,
        principal: Principal,
        category: Optional[str] = None,
        unread_only: bool = False,
    ) -> dict[str, Any]:
        """Construct user-scoped tenant-isolated query."""
        query: dict[str, Any] = {
            "$or": [
                {"user_id": principal.subject},
                {"user_id": None, "institution_id": {"$in": [principal.institution_id, "INST-ALL", None]}},
            ]
        }
        if category and category.upper() != "ALL":
            query["category"] = category.upper()
        if unread_only:
            query["is_read"] = False
        return query

    async def _ensure_seed_notifications(self, principal: Principal) -> None:
        """Seed sample notifications if collection is empty for caller."""
        user_doc_count = await self.db["notifications"].count_documents({"user_id": principal.subject})
        if user_doc_count == 0:
            inst_id = principal.institution_id or "INST-0421"
            seed_docs = [
                {
                    **sample,
                    "user_id": principal.subject,
                    "institution_id": inst_id,
                }
                for sample in SAMPLE_NOTIFICATIONS_SEED
            ]
            await self.db["notifications"].insert_many(seed_docs)

    async def list_notifications(
        self,
        principal: Principal,
        category: Optional[str] = None,
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 50,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> List[NotificationOut]:
        """List permitted notifications for the authenticated user."""
        await self._ensure_seed_notifications(principal)
        query = self._build_user_query(principal, category=category, unread_only=unread_only)

        if page is not None and page_size is not None:
            computed_skip = max(0, (page - 1) * page_size)
            computed_limit = page_size
        else:
            computed_skip = skip
            computed_limit = limit

        cursor = self.db["notifications"].find(query).sort("created_at", -1).skip(computed_skip).limit(computed_limit)
        results: List[NotificationOut] = []

        async for doc in cursor:
            created_at_val = doc.get("created_at")
            created_str = created_at_val.isoformat() if isinstance(created_at_val, datetime) else str(created_at_val or utcnow().isoformat())
            read_at_val = doc.get("read_at")
            read_str = read_at_val.isoformat() if isinstance(read_at_val, datetime) else (str(read_at_val) if read_at_val else None)

            results.append(
                NotificationOut(
                    notification_id=doc["notification_id"],
                    institution_id=doc.get("institution_id", principal.institution_id or "INST-0421"),
                    category=doc.get("category", "ANNOUNCEMENTS"),
                    priority=doc.get("priority", "NORMAL"),
                    title=doc.get("title", ""),
                    message=doc.get("message", ""),
                    deep_link=doc.get("deep_link"),
                    channels=doc.get("channels", ["IN_APP"]),
                    is_read=bool(doc.get("is_read", False)),
                    read_at=read_str,
                    created_at=created_str,
                )
            )

        return results

    async def list_notifications_paged(
        self,
        principal: Principal,
        category: Optional[str] = None,
        unread_only: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> NotificationPageOut:
        """List notifications with pagination metadata."""
        await self._ensure_seed_notifications(principal)
        query = self._build_user_query(principal, category=category, unread_only=unread_only)
        total = await self.db["notifications"].count_documents(query)
        unread_count_query = self._build_user_query(principal, unread_only=True)
        unread = await self.db["notifications"].count_documents(unread_count_query)

        items = await self.list_notifications(
            principal,
            category=category,
            unread_only=unread_only,
            page=page,
            page_size=page_size,
        )

        total_pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 1
        return NotificationPageOut(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            unread_count=unread,
        )

    async def get_unread_count(self, principal: Principal) -> UnreadCountOut:
        """Count unread and urgent notifications."""
        await self._ensure_seed_notifications(principal)
        query = {
            "is_read": False,
            "$or": [
                {"user_id": principal.subject},
                {"user_id": None, "institution_id": {"$in": [principal.institution_id, "INST-ALL", None]}},
            ],
        }
        unread = await self.db["notifications"].count_documents(query)
        urgent = await self.db["notifications"].count_documents({**query, "priority": "URGENT"})
        return UnreadCountOut(unread_count=unread, urgent_count=urgent)

    async def mark_as_read(
        self,
        principal: Principal,
        notification_id: str,
        client_ip_addr: str,
    ) -> dict[str, Any]:
        """Mark single notification as read, enforcing user ownership."""
        now = utcnow()
        filter_query = {
            "notification_id": notification_id,
            "$or": [
                {"user_id": principal.subject},
                {"user_id": None, "institution_id": {"$in": [principal.institution_id, "INST-ALL", None]}},
            ],
        }
        res = await self.db["notifications"].update_one(
            filter_query,
            {"$set": {"is_read": True, "read_at": now}},
        )
        if res.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found or access denied.",
            )
        return {"status": "SUCCESS", "notification_id": notification_id, "read_at": now.isoformat()}

    async def mark_all_as_read(
        self,
        principal: Principal,
        client_ip_addr: str,
    ) -> dict[str, Any]:
        """Mark all notifications for the caller as read."""
        now = utcnow()
        res = await self.db["notifications"].update_many(
            {
                "is_read": False,
                "$or": [
                    {"user_id": principal.subject},
                    {"user_id": None, "institution_id": {"$in": [principal.institution_id, "INST-ALL", None]}},
                ],
            },
            {"$set": {"is_read": True, "read_at": now}},
        )
        return {"status": "SUCCESS", "marked_count": res.modified_count, "read_at": now.isoformat()}

    async def delete_notification(
        self,
        principal: Principal,
        notification_id: str,
    ) -> dict[str, Any]:
        """Dismiss or delete notification from user's view, enforcing user ownership."""
        filter_query = {
            "notification_id": notification_id,
            "$or": [
                {"user_id": principal.subject},
                {"user_id": None, "institution_id": {"$in": [principal.institution_id, "INST-ALL", None]}},
            ],
        }
        res = await self.db["notifications"].delete_one(filter_query)
        if res.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found or access denied.",
            )
        return {"status": "DELETED", "notification_id": notification_id}

    async def get_preferences(self, principal: Principal) -> NotificationPreferenceOut:
        """Get notification and quiet hours preferences."""
        doc = await self.db["notification_preferences"].find_one({"user_id": principal.subject})
        if not doc:
            return NotificationPreferenceOut(
                user_id=principal.subject,
                subscribed_categories=ALL_NOTIFICATION_CATEGORIES,
            )
        return NotificationPreferenceOut(
            user_id=principal.subject,
            in_app_enabled=doc.get("in_app_enabled", True),
            email_enabled=doc.get("email_enabled", True),
            push_enabled=doc.get("push_enabled", True),
            quiet_hours_enabled=doc.get("quiet_hours_enabled", False),
            quiet_hours_start=doc.get("quiet_hours_start", "22:00"),
            quiet_hours_end=doc.get("quiet_hours_end", "07:00"),
            language_preference=doc.get("language_preference", "en"),
            subscribed_categories=doc.get("subscribed_categories", ALL_NOTIFICATION_CATEGORIES),
        )

    async def update_preferences(
        self,
        principal: Principal,
        payload: NotificationPreferenceUpdate,
        client_ip_addr: str,
    ) -> NotificationPreferenceOut:
        """Update notification and quiet hours preferences."""
        updates: dict[str, Any] = {"updated_at": utcnow()}
        payload_dict = payload.dict(exclude_unset=True)

        # Enforce that SECURITY notifications can NEVER be suppressed
        if "subscribed_categories" in payload_dict and payload_dict["subscribed_categories"] is not None:
            categories = list(payload_dict["subscribed_categories"])
            if "SECURITY" not in categories:
                categories.append("SECURITY")
            payload_dict["subscribed_categories"] = categories

        for k, v in payload_dict.items():
            updates[k] = v

        await self.db["notification_preferences"].update_one(
            {"user_id": principal.subject},
            {"$set": updates},
            upsert=True,
        )

        await writer.log(
            self.audit_repo,
            actor=principal.subject,
            actor_role=principal.role,
            action="UPDATE_NOTIFICATION_PREFERENCES",
            subject=principal.subject,
            details="User updated notification channels and quiet hours preferences.",
            category="USER_PREFERENCE",
            ip_address=client_ip_addr,
        )

        return await self.get_preferences(principal)

    async def register_device(
        self,
        principal: Principal,
        payload: DeviceTokenRegisterIn,
        client_ip_addr: str,
    ) -> DeviceTokenOut:
        """Register or update mobile device token for push notifications."""
        device_id = f"DEV-{secrets.token_hex(6)}"
        now = utcnow()
        now_str = now.isoformat()

        doc = {
            "device_id": device_id,
            "user_id": principal.subject,
            "token": payload.token,
            "platform": payload.platform.value,
            "device_name": payload.device_name or "Mobile Client",
            "device_model": payload.device_model or "Generic Handset",
            "app_version": payload.app_version or "2.0.0",
            "registered_at": now_str,
            "last_active_at": now_str,
            "ip_address": client_ip_addr,
        }

        await self.db["device_tokens"].update_one(
            {"user_id": principal.subject, "token": payload.token},
            {"$set": doc},
            upsert=True,
        )

        await writer.log(
            self.audit_repo,
            actor=principal.subject,
            actor_role=principal.role,
            action="REGISTER_DEVICE_TOKEN",
            subject=payload.token[:12] + "...",
            details=f"Registered {payload.platform.value} device token for push delivery.",
            category="COMMUNICATION",
            ip_address=client_ip_addr,
        )

        return DeviceTokenOut(
            device_id=device_id,
            user_id=principal.subject,
            token=payload.token,
            platform=payload.platform.value,
            device_name=payload.device_name,
            device_model=payload.device_model,
            app_version=payload.app_version,
            registered_at=now_str,
            last_active_at=now_str,
        )

    async def revoke_device(
        self,
        principal: Principal,
        token: str,
        client_ip_addr: str,
    ) -> dict[str, Any]:
        """Revoke a registered device token for push notifications."""
        res = await self.db["device_tokens"].delete_one({"user_id": principal.subject, "token": token})
        if res.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device token not found or already revoked.",
            )

        await writer.log(
            self.audit_repo,
            actor=principal.subject,
            actor_role=principal.role,
            action="REVOKE_DEVICE_TOKEN",
            subject=token[:12] + "...",
            details="Revoked device token for push notifications.",
            category="COMMUNICATION",
            ip_address=client_ip_addr,
        )
        return {"status": "REVOKED", "token": token}

    async def list_devices(self, principal: Principal) -> List[DeviceTokenOut]:
        """List active device tokens registered by the caller."""
        cursor = self.db["device_tokens"].find({"user_id": principal.subject}).sort("registered_at", -1)
        results: List[DeviceTokenOut] = []
        async for doc in cursor:
            results.append(
                DeviceTokenOut(
                    device_id=doc.get("device_id", "DEV-UNKNOWN"),
                    user_id=doc.get("user_id", principal.subject),
                    token=doc.get("token", ""),
                    platform=doc.get("platform", "ANDROID"),
                    device_name=doc.get("device_name"),
                    device_model=doc.get("device_model"),
                    app_version=doc.get("app_version"),
                    registered_at=doc.get("registered_at", utcnow().isoformat()),
                    last_active_at=doc.get("last_active_at", utcnow().isoformat()),
                )
            )
        return results

    async def simulate_dispatch_records(
        self,
        notification_id: str,
        title: str,
        recipient_id: str,
        channels: List[str],
    ) -> List[NotificationDeliveryRecordOut]:
        """Simulate async multi-channel dispatch records without blocking caller."""
        deliveries: List[NotificationDeliveryRecordOut] = []
        now_str = utcnow().isoformat()

        for ch in channels:
            del_id = f"DEL-{secrets.token_hex(5)}"
            record = {
                "delivery_id": del_id,
                "notification_id": notification_id,
                "channel": ch,
                "recipient": recipient_id,
                "status": "SENT" if ch == "IN_APP" else "SIMULATED",
                "attempt_count": 1,
                "sent_at": now_str,
                "error_message": None,
            }
            await self.db["notification_deliveries"].insert_one(record)
            deliveries.append(NotificationDeliveryRecordOut(**record))

        return deliveries

    async def broadcast_notification(
        self,
        principal: Principal,
        payload: BroadcastNotificationRequest,
        client_ip_addr: str,
    ) -> NotificationOut:
        """Broadcast a notification to role, class, or institution across selected channels."""
        nid = f"NTF-{secrets.token_hex(6)}"
        inst_id = payload.institution_id or principal.institution_id or "INST-0421"
        now = utcnow()
        channels = [c.value if hasattr(c, "value") else str(c) for c in (payload.channels or ["IN_APP"])]

        doc = {
            "notification_id": nid,
            "institution_id": inst_id,
            "category": payload.category.value,
            "priority": payload.priority.value,
            "title": payload.title,
            "message": payload.message,
            "deep_link": payload.deep_link,
            "channels": channels,
            "target_role": payload.target_role,
            "target_class": payload.target_class,
            "published_by": principal.subject,
            "created_at": now,
            "is_read": False,
        }

        await self.db["notifications"].insert_one(doc)

        # Asynchronous multi-channel dispatch simulation
        await self.simulate_dispatch_records(
            notification_id=nid,
            title=payload.title,
            recipient_id=payload.target_role or "ALL_MEMBERS",
            channels=channels,
        )

        await writer.log(
            self.audit_repo,
            actor=principal.subject,
            actor_role=principal.role,
            action="BROADCAST_NOTIFICATION",
            subject=nid,
            details=f"Broadcasted '{payload.title}' with priority {payload.priority.value} via {', '.join(channels)}.",
            category="COMMUNICATION",
            ip_address=client_ip_addr,
        )

        return NotificationOut(
            notification_id=nid,
            institution_id=inst_id,
            category=payload.category.value,
            priority=payload.priority.value,
            title=payload.title,
            message=payload.message,
            deep_link=payload.deep_link,
            channels=channels,
            is_read=False,
            created_at=now.isoformat(),
        )
