"""Repository for the opaque verification tokens.

A verification token is a high-entropy, short-lived, revocable handle to a
credential. It replaces putting the raw APAAR ID in a URL: the token itself
discloses nothing, and only its hash is stored, so a dump of the collection
cannot be replayed.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from app.models.documents import Doc, docs, utcnow


def generate_token() -> tuple[str, str]:
    """Return ``(plaintext, hash)`` for a fresh token.

    Only the hash is ever stored. The plaintext is shown to the issuer once
    and never logged.
    """
    raw = secrets.token_urlsafe(32)
    return raw, hash_token(raw)


def hash_token(raw: str) -> str:
    """The SHA-256 hash of a token value."""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def tokens_match(raw: str, expected_hash: str) -> bool:
    """Constant-time comparison of a presented token with a stored hash."""
    if not raw or not expected_hash:
        return False
    return hmac.compare_digest(hash_token(raw), expected_hash.strip().lower())


class VerificationTokenRepository:
    """Reads and writes the verification tokens."""

    def __init__(self, collection: Any) -> None:
        self._collection = collection

    # ---------------------------------------------------------------- reads

    async def by_hash(self, token_hash: str) -> Doc | None:
        """The token with the given hash."""
        row = await self._collection.find_one({"token_hash": token_hash})
        return Doc(row) if row else None

    async def get(self, token_id: str) -> Doc | None:
        row = await self._collection.find_one({"token_id": token_id})
        return Doc(row) if row else None

    async def for_record(self, student_record_id: str) -> list[Doc]:
        """Every token issued against one record, newest first."""
        rows = (
            await self._collection.find({"student_record_id": student_record_id})
            .sort("issued_at", -1)
            .to_list(length=None)
        )
        return docs(rows)

    async def count(self) -> int:
        return await self._collection.count_documents({})

    # --------------------------------------------------------------- writes

    async def issue(
        self,
        student_record_id: str,
        claims_snapshot: dict[str, Any],
        *,
        issued_by: str,
        minutes: int = 60,
    ) -> tuple[Doc, str]:
        """Issue a token and return the stored document with the plaintext."""
        raw, token_hash = generate_token()
        now = datetime.now(timezone.utc)
        document = {
            "token_id": secrets.token_hex(8),
            "token_hash": token_hash,
            "student_record_id": student_record_id,
            "claims_snapshot": claims_snapshot,
            "issued_at": now,
            "expires_at": now + timedelta(minutes=minutes),
            "revoked": False,
            "needs_reissue": False,
            "issued_by": issued_by,
        }
        await self._collection.insert_one(document)
        return Doc(document), raw

    async def revoke(self, token_id: str) -> Doc | None:
        """Revoke a token."""
        await self._collection.update_one(
            {"token_id": token_id}, {"$set": {"revoked": True, "updated_at": utcnow()}}
        )
        return await self.get(token_id)

    async def mark_needs_reissue(
        self, student_record_id: str, session: Any = None
    ) -> int:
        """Flag every live token of a record as needing a fresh issue.

        This is the ``CIA-F`` effect: a correction that changes a field the
        seal commits to makes the tokens that were issued against the old
        values describe outdated data.
        """
        result = await self._collection.update_many(
            {"student_record_id": student_record_id, "revoked": False},
            {"$set": {"needs_reissue": True, "updated_at": utcnow()}},
            session=session,
        )
        return result.modified_count
