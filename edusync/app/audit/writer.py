"""Audit trail writer.

Every meaningful action in the platform is written to the immutable audit
trail, and each entry is chained to its predecessor so that the trail is
tamper-evident.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog
from app.services import audit_chain


async def last_hash(session: AsyncSession) -> str:
    """The hash of the most recent audit entry (or the genesis hash)."""
    result = await session.execute(
        select(AuditLog.hash).order_by(AuditLog.log_id.desc()).limit(1)
    )
    value = result.scalar_one_or_none()
    return value or audit_chain.GENESIS_HASH


async def log(
    session: AsyncSession,
    *,
    actor: str,
    action: str,
    subject: str = "",
    details: str = "",
    category: str = "SYSTEM",
    actor_role: str = "",
    ip_address: str | None = None,
    timestamp: datetime | None = None,
) -> AuditLog:
    """Append a chained entry to the audit trail."""
    moment = timestamp or datetime.now(timezone.utc)
    prev = await last_hash(session)
    digest = audit_chain.compute_hash(
        prev_hash=prev,
        timestamp=moment,
        actor=actor,
        action=action,
        subject=subject,
        details=details,
        category=category,
    )
    entry = AuditLog(
        timestamp=moment,
        actor=actor,
        actor_role=actor_role,
        action=action,
        subject=subject,
        details=details,
        category=category,
        ip_address=ip_address,
        prev_hash=prev,
        hash=digest,
    )
    session.add(entry)
    return entry


async def verify_chain(session: AsyncSession, limit: int = 500) -> tuple[bool, str | None]:
    """Verify the integrity of the most recent *limit* audit entries."""
    result = await session.execute(
        select(AuditLog).order_by(AuditLog.log_id.desc()).limit(limit)
    )
    entries = list(reversed(result.scalars().all()))
    return audit_chain.verify(entries), audit_chain.first_break(entries)
