"""Repository for stateful refresh token sessions.

Each refresh session is associated with a cryptographic hash of the refresh
token (never plaintext), its unique JWT ID (jti), family lineage identifier,
issuance and expiry timestamps, user linkage, client IP and User-Agent metadata,
and revocation status.
"""

from __future__ import annotations

import secrets
from datetime import datetime
from typing import Any, Optional

from app.models.documents import Doc, docs, utcnow


class SessionRepository:
    """Reads, writes, rotates and revokes stateful refresh token sessions."""

    def __init__(self, collection: Any) -> None:
        self._collection = collection

    # ---------------------------------------------------------------- queries

    async def by_jti(self, jti: str) -> Doc | None:
        """Find a session document by its unique token identifier (jti)."""
        if not jti:
            return None
        row = await self._collection.find_one({"jti": jti})
        return Doc(row) if row else None

    async def by_token_hash(self, token_hash: str) -> Doc | None:
        """Find a session document by cryptographic SHA-256 token hash."""
        if not token_hash:
            return None
        row = await self._collection.find_one({"token_hash": token_hash})
        return Doc(row) if row else None

    async def active_sessions_for_user(self, user_id: str) -> list[Doc]:
        """Return all active, non-rotated, non-revoked sessions for a user."""
        rows = (
            await self._collection.find(
                {"user_id": user_id, "is_revoked": False, "rotated_at": None}
            )
            .sort("created_at", -1)
            .to_list(length=None)
        )
        return docs(rows)

    # ---------------------------------------------------------------- creation

    async def create_session(
        self,
        user_id: str,
        jti: str,
        token_hash: str,
        expires_at: datetime,
        session_id: Optional[str] = None,
        family_id: Optional[str] = None,
        parent_jti: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Doc:
        """Persist a new refresh session with cryptographic token hash and metadata."""
        now = utcnow()
        effective_session_id = session_id or f"ses_{secrets.token_urlsafe(24)}"
        effective_family_id = family_id or f"fam_{secrets.token_urlsafe(24)}"

        document: dict[str, Any] = {
            "session_id": effective_session_id,
            "family_id": effective_family_id,
            "user_id": user_id,
            "jti": jti,
            "token_hash": token_hash,
            "parent_jti": parent_jti,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "created_at": now,
            "expires_at": expires_at,
            "last_used_at": None,
            "is_revoked": False,
            "revoked_at": None,
            "revoked_reason": None,
            "rotated_at": None,
            "child_jti": None,
        }
        await self._collection.insert_one(document)
        return Doc(document)

    # ---------------------------------------------------------------- rotation

    async def rotate_session(
        self,
        old_jti: str,
        new_jti: str,
        new_token_hash: str,
        new_expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> tuple[bool, Doc | None]:
        """Atomically invalidate the predecessor token and persist the rotated child.

        Returns (True, child_doc) on success.
        If another concurrent request already rotated the predecessor token or if
        the token was revoked, returns (False, None) to prevent split-brain descendant tokens.
        """
        now = utcnow()
        updated_old = await self._collection.find_one_and_update(
            {"jti": old_jti, "rotated_at": None, "is_revoked": False},
            {"$set": {"rotated_at": now, "last_used_at": now, "child_jti": new_jti}},
        )
        if not updated_old:
            return False, None

        child_document: dict[str, Any] = {
            "session_id": updated_old.get("session_id"),
            "family_id": updated_old.get("family_id"),
            "user_id": updated_old.get("user_id"),
            "jti": new_jti,
            "token_hash": new_token_hash,
            "parent_jti": old_jti,
            "ip_address": ip_address or updated_old.get("ip_address"),
            "user_agent": user_agent or updated_old.get("user_agent"),
            "created_at": now,
            "expires_at": new_expires_at,
            "last_used_at": None,
            "is_revoked": False,
            "revoked_at": None,
            "revoked_reason": None,
            "rotated_at": None,
            "child_jti": None,
        }
        await self._collection.insert_one(child_document)
        return True, Doc(child_document)

    # -------------------------------------------------------------- revocation

    async def revoke_session(
        self, session_id: str, reason: str = "LOGOUT"
    ) -> int:
        """Revoke all tokens associated with a specific device/session ID."""
        now = utcnow()
        result = await self._collection.update_many(
            {"session_id": session_id, "is_revoked": False},
            {"$set": {"is_revoked": True, "revoked_at": now, "revoked_reason": reason}},
        )
        return result.modified_count

    async def revoke_by_jti(
        self, jti: str, reason: str = "LOGOUT"
    ) -> int:
        """Revoke a specific token by its jti."""
        now = utcnow()
        result = await self._collection.update_many(
            {"jti": jti, "is_revoked": False},
            {"$set": {"is_revoked": True, "revoked_at": now, "revoked_reason": reason}},
        )
        return result.modified_count

    async def revoke_family(
        self, family_id: str, reason: str = "TOKEN_REUSE_DETECTED"
    ) -> int:
        """Revoke every token in a family chain upon refresh token reuse detection."""
        now = utcnow()
        result = await self._collection.update_many(
            {"family_id": family_id, "is_revoked": False},
            {"$set": {"is_revoked": True, "revoked_at": now, "revoked_reason": reason}},
        )
        return result.modified_count

    async def revoke_all_user_sessions(
        self, user_id: str, reason: str = "ALL_SESSIONS_LOGOUT"
    ) -> int:
        """Revoke all active sessions for a user across all devices."""
        now = utcnow()
        result = await self._collection.update_many(
            {"user_id": user_id, "is_revoked": False},
            {"$set": {"is_revoked": True, "revoked_at": now, "revoked_reason": reason}},
        )
        return result.modified_count

    # ----------------------------------------------------------------- indexes

    async def ensure_indexes(self) -> None:
        """Create indexes for fast lookup and automatic TTL cleanup of expired sessions."""
        await self._collection.create_index([("token_hash", 1)], unique=True, sparse=True)
        await self._collection.create_index([("jti", 1)], unique=True, sparse=True)
        await self._collection.create_index([("family_id", 1)])
        await self._collection.create_index([("user_id", 1)])
        await self._collection.create_index([("session_id", 1)])
        await self._collection.create_index([("expires_at", 1)], expireAfterSeconds=0)
