"""Audit trail writer."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from app.models.documents import redact_apaar
from app.repositories.audit import AuditRepository
from app.services import audit_chain


async def log(
    repository: AuditRepository,
    *,
    actor: str,
    action: str,
    subject: str = "",
    details: str = "",
    category: str = "SYSTEM",
    actor_role: str = "",
    ip_address: Optional[str] = None,
    timestamp: Optional[datetime] = None,
) -> Any:
    """Append a chained entry to the audit trail.

    The subject is stored redacted when it looks like an APAAR ID, so the
    trail never holds a raw identifier in the clear.
    """
    moment = timestamp or datetime.now(timezone.utc)
    prev = await repository.last_hash()
    digest = audit_chain.compute_hash(
        prev_hash=prev,
        timestamp=moment,
        actor=actor,
        action=action,
        subject=subject,
        details=details,
        category=category,
    )
    return await repository.insert(
        {
            "timestamp": moment,
            "actor": actor,
            "actor_role": actor_role,
            "action": action,
            "subject": redact_apaar(subject) if subject.isdigit() else subject,
            "details": details,
            "category": category,
            "ip_address": ip_address,
            "prev_hash": prev,
            "hash": digest,
            "integrity": "sha256-chained",
        }
    )


async def verify_chain(repository: AuditRepository, limit: int = 500) -> tuple[bool, str | None]:
    """Verify the integrity of the most recent *limit* audit entries."""
    entries = await repository.oldest_first(limit=limit)
    return audit_chain.verify(entries), audit_chain.first_break(entries)
