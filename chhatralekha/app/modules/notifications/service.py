"""Notification Module Business Service."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import Principal
from app.audit import writer
from app.core.config import get_settings
from app.models.documents import utcnow
from app.modules.notifications.schemas import (
    BroadcastNotificationRequest,
    NotificationCategory,
    NotificationOut,
    NotificationPreferenceOut,
    NotificationPreferenceUpdate,
    NotificationPriority,
    UnreadCountOut,
)
from app.repositories.audit import AuditRepository

settings = get_settings()


SAMPLE_NOTIFICATIONS_SEED = [
    {
        "notification_id": "ntf-01",
        "category": "ATTENDANCE",
        "priority": "HIGH",
        "title": "Monthly Attendance Summary (October 2024)",
        "message": "Your overall attendance for October 2024 is recorded at 94.2%. Keep up the good work.",
        "deep_link": "/me/attendance",
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
        "is_read": True,
        "created_at": datetime(2024, 10, 24, 8, 20, tzinfo=timezone.utc),
    },
]


class NotificationService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db
        self.audit_repo = AuditRepository(db["audit_events"])

    async def list_notifications(
        self,
        principal: Principal,
        category: Optional[str] = None,
        unread_only: bool = False,
        limit: int = 50,
    ) -> List[NotificationOut]:
        """List permitted notifications for the authenticated user."""
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

        cursor = self.db["notifications"].find(query).sort("created_at", -1).limit(limit)
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
                    is_read=bool(doc.get("is_read", False)),
                    read_at=read_str,
                    created_at=created_str,
                )
            )

        # Seed sample notifications if empty
        if not results and not category and not unread_only:
            inst_id = principal.institution_id or "INST-0421"
            for sample in SAMPLE_NOTIFICATIONS_SEED:
                doc = {
                    **sample,
                    "user_id": principal.subject,
                    "institution_id": inst_id,
                }
                await self.db["notifications"].insert_one(doc)
                results.append(
                    NotificationOut(
                        notification_id=sample["notification_id"],
                        institution_id=inst_id,
                        category=sample["category"],
                        priority=sample["priority"],
                        title=sample["title"],
                        message=sample["message"],
                        deep_link=sample["deep_link"],
                        is_read=sample["is_read"],
                        created_at=sample["created_at"].isoformat(),
                    )
                )

        return results

    async def get_unread_count(self, principal: Principal) -> UnreadCountOut:
        """Count unread and urgent notifications."""
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
        """Mark single notification as read."""
        now = utcnow()
        await self.db["notifications"].update_one(
            {"notification_id": notification_id},
            {"$set": {"is_read": True, "read_at": now}},
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
        """Dismiss or delete notification from user's view."""
        await self.db["notifications"].delete_one({"notification_id": notification_id})
        return {"status": "DELETED", "notification_id": notification_id}

    async def get_preferences(self, principal: Principal) -> NotificationPreferenceOut:
        """Get notification and quiet hours preferences."""
        doc = await self.db["notification_preferences"].find_one({"user_id": principal.subject})
        if not doc:
            return NotificationPreferenceOut(user_id=principal.subject)
        return NotificationPreferenceOut(
            user_id=principal.subject,
            in_app_enabled=doc.get("in_app_enabled", True),
            email_enabled=doc.get("email_enabled", True),
            push_enabled=doc.get("push_enabled", True),
            quiet_hours_enabled=doc.get("quiet_hours_enabled", False),
            quiet_hours_start=doc.get("quiet_hours_start", "22:00"),
            quiet_hours_end=doc.get("quiet_hours_end", "07:00"),
            subscribed_categories=doc.get("subscribed_categories", [c.value for c in NotificationCategory]),
        )

    async def update_preferences(
        self,
        principal: Principal,
        payload: NotificationPreferenceUpdate,
        client_ip_addr: str,
    ) -> NotificationPreferenceOut:
        """Update notification and quiet hours preferences."""
        updates: dict[str, Any] = {"updated_at": utcnow()}
        for k, v in payload.dict(exclude_unset=True).items():
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

    async def broadcast_notification(
        self,
        principal: Principal,
        payload: BroadcastNotificationRequest,
        client_ip_addr: str,
    ) -> NotificationOut:
        """Broadcast a notification to role, class, or institution."""
        nid = f"NTF-{secrets.token_hex(6)}"
        inst_id = payload.institution_id or principal.institution_id or "INST-0421"
        now = utcnow()

        doc = {
            "notification_id": nid,
            "institution_id": inst_id,
            "category": payload.category.value,
            "priority": payload.priority.value,
            "title": payload.title,
            "message": payload.message,
            "deep_link": payload.deep_link,
            "target_role": payload.target_role,
            "target_class": payload.target_class,
            "published_by": principal.subject,
            "created_at": now,
            "is_read": False,
        }

        await self.db["notifications"].insert_one(doc)

        await writer.log(
            self.audit_repo,
            actor=principal.subject,
            actor_role=principal.role,
            action="BROADCAST_NOTIFICATION",
            subject=nid,
            details=f"Broadcasted '{payload.title}' with priority {payload.priority.value}.",
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
            is_read=False,
            created_at=now.isoformat(),
        )
