"""Repository for the users, API keys and revoked credentials."""

from __future__ import annotations

from typing import Any

from app.models.documents import Doc, docs, utcnow


class UserRepository:
    """Reads and writes the accounts, API keys and revocation list."""

    def __init__(
        self,
        users: Any,
        api_keys: Any = None,
        revoked: Any = None,
    ) -> None:
        self._users = users
        self._api_keys = api_keys
        self._revoked = revoked

    # ---------------------------------------------------------------- users

    async def by_email(self, email: str) -> Doc | None:
        row = await self._users.find_one({"email": email.strip().lower()})
        return Doc(row) if row else None

    async def by_user_id(self, user_id: str) -> Doc | None:
        row = await self._users.find_one({"user_id": user_id})
        return Doc(row) if row else None

    async def all(self) -> list[Doc]:
        rows = await self._users.find({}).sort("role", 1).to_list(length=None)
        return docs(rows)

    async def insert(self, document: dict[str, Any]) -> Doc:
        now = utcnow()
        document = dict(document)
        document.setdefault("created_at", now)
        document["updated_at"] = now
        await self._users.insert_one(document)
        return Doc(document)

    async def insert_many(self, documents: list[dict[str, Any]]) -> int:
        now = utcnow()
        prepared = []
        for document in documents:
            item = dict(document)
            item.setdefault("created_at", now)
            item.setdefault("updated_at", now)
            prepared.append(item)
        if not prepared:
            return 0
        result = await self._users.insert_many(prepared)
        return len(result.inserted_ids)

    async def set_last_login(self, user_id: str) -> None:
        await self._users.update_one(
            {"user_id": user_id}, {"$set": {"last_login_at": utcnow()}}
        )

    # ------------------------------------------------------------- api keys

    async def api_key_by_id(self, key_id: str) -> Doc | None:
        if self._api_keys is None:
            return None
        row = await self._api_keys.find_one({"key_id": key_id, "is_active": True})
        return Doc(row) if row else None

    async def api_key_by_hash(self, key_hash: str) -> Doc | None:
        if self._api_keys is None:
            return None
        row = await self._api_keys.find_one({"key_hash": key_hash, "is_active": True})
        return Doc(row) if row else None

    async def insert_api_key(self, document: dict[str, Any]) -> Doc:
        now = utcnow()
        document = dict(document)
        document.setdefault("created_at", now)
        document["updated_at"] = now
        await self._api_keys.insert_one(document)
        return Doc(document)

    # --------------------------------------------------- revoked credentials

    async def revoked_for(self, apaar_id: str) -> Doc | None:
        if self._revoked is None:
            return None
        row = await self._revoked.find_one({"apaar_id": apaar_id})
        return Doc(row) if row else None

    async def revoke(self, document: dict[str, Any]) -> Doc:
        now = utcnow()
        document = dict(document)
        document.setdefault("revoked_at", now)
        await self._revoked.insert_one(document)
        return Doc(document)

    # --------------------------------------------------------------- resets

    async def delete_all(self) -> int:
        total = 0
        for collection in (self._users, self._api_keys, self._revoked):
            if collection is None:
                continue
            result = await collection.delete_many({})
            total += result.deleted_count
        return total
