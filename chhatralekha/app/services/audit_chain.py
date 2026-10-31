"""Tamper-evident audit chain.

Every entry stores the hash of the previous entry and its own hash::

    hash(n) = SHA-256( hash(n-1) || timestamp || actor || action || subject || details || category )

Deleting, reordering or editing any row invalidates every hash after it, so
an auditor can prove that the trail has not been rewritten. The chain is
self-contained - no server, no key - which means it can be re-verified
offline.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Iterable

from app.models.documents import field

GENESIS_HASH = "0" * 64


def _iso(moment: datetime | None) -> str:
    if moment is None:
        return ""
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).isoformat()


def truncate(moment: datetime) -> datetime:
    """Floor a datetime to whole milliseconds.

    MongoDB stores a date with millisecond precision, so a timestamp that
    carries microseconds is not the value that comes back out. The audit
    chain hashes the timestamp, so it has to be truncated before it is
    written - otherwise the stored value and the hashed value differ and the
    chain never verifies.
    """
    return moment.replace(microsecond=(moment.microsecond // 1000) * 1000)


def compute_hash(
    prev_hash: str,
    timestamp: datetime | None,
    actor: str,
    action: str,
    subject: str,
    details: str,
    category: str,
) -> str:
    """Compute the chain hash of a single entry."""
    canonical = "|".join(
        [
            (prev_hash or GENESIS_HASH).strip() or GENESIS_HASH,
            _iso(timestamp),
            actor or "",
            action or "",
            subject or "",
            details or "",
            category or "",
        ]
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def hash_of(entry) -> str:
    """Compute the chain hash of an entry that has no hash yet."""
    return compute_hash(
        prev_hash=field(entry, "prev_hash", "") or "",
        timestamp=field(entry, "timestamp"),
        actor=field(entry, "actor", "") or "",
        action=field(entry, "action", "") or "",
        subject=field(entry, "subject", "") or "",
        details=field(entry, "details", "") or "",
        category=field(entry, "category", "") or "",
    )


def chain(entries: Iterable) -> list:
    """Return the entries with their chain hashes filled in (oldest first)."""
    prev = GENESIS_HASH
    chained = []
    for entry in entries:
        digest = compute_hash(
            prev_hash=prev,
            timestamp=field(entry, "timestamp"),
            actor=field(entry, "actor", "") or "",
            action=field(entry, "action", "") or "",
            subject=field(entry, "subject", "") or "",
            details=field(entry, "details", "") or "",
            category=field(entry, "category", "") or "",
        )
        entry.prev_hash = prev
        entry.hash = digest
        chained.append(entry)
        prev = digest
    return chained


def verify(entries: Iterable) -> bool:
    """Verify a chain of entries supplied oldest-first."""
    prev = GENESIS_HASH
    for entry in entries:
        if (field(entry, "prev_hash", "") or "") != prev:
            return False
        if (field(entry, "hash", "") or "") != compute_hash(
            prev_hash=field(entry, "prev_hash", "") or "",
            timestamp=field(entry, "timestamp"),
            actor=field(entry, "actor", "") or "",
            action=field(entry, "action", "") or "",
            subject=field(entry, "subject", "") or "",
            details=field(entry, "details", "") or "",
            category=field(entry, "category", "") or "",
        ):
            return False
        prev = field(entry, "hash", "") or ""
    return True


def first_break(entries: Iterable) -> str | None:
    """Describe the first broken link of a chain, or ``None`` when intact."""
    prev = GENESIS_HASH
    for index, entry in enumerate(entries, start=1):
        if (field(entry, "prev_hash", "") or "") != prev:
            return f"Entry {index} does not link to the previous entry."
        if (field(entry, "hash", "") or "") != compute_hash(
            prev_hash=field(entry, "prev_hash", "") or "",
            timestamp=field(entry, "timestamp"),
            actor=field(entry, "actor", "") or "",
            action=field(entry, "action", "") or "",
            subject=field(entry, "subject", "") or "",
            details=field(entry, "details", "") or "",
            category=field(entry, "category", "") or "",
        ):
            return f"Entry {index} has been altered after it was written."
        prev = field(entry, "hash", "") or ""
    return None
