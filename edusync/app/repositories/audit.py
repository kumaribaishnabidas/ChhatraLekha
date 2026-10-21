"""Repository for the audit trail."""

from __future__ import annotations

from typing import Any

from app.models.documents import Doc, docs, utcnow


class AuditRepository:
    """Reads and writes the tamper-evident audit trail."""

    def __init__(self, collection: Any) -> None:
        self._collection = collection

    # ---------------------------------------------------------------- reads

    async def recent(self, limit: int = 200) -> list[Doc]:
        """The most recent entries, newest first."""
        rows = (
            await self._collection.find({})
            .sort("timestamp", -1)
            .limit(limit)
            .to_list(length=None)
        )
        return docs(rows)

    async def oldest_first(self, limit: int = 500) -> list[Doc]:
        """The oldest entries first - the order the chain is verified in."""
        rows = (
            await self._collection.find({})
            .sort("timestamp", 1)
            .limit(limit)
            .to_list(length=None)
        )
        return docs(rows)

    async def last_hash(self) -> str:
        """The hash of the most recent entry (or the genesis hash)."""
        from app.services import audit_chain

        row = await self._collection.find_one(sort=[("timestamp", -1)])
        if not row:
            return audit_chain.GENESIS_HASH
        return row.get("hash") or audit_chain.GENESIS_HASH

    async def count(self) -> int:
        return await self._collection.count_documents({})

    # --------------------------------------------------------------- writes

    async def insert(self, document: dict[str, Any]) -> Doc:
        """Append one chained entry."""
        now = utcnow()
        document = dict(document)
        document.setdefault("timestamp", now)
        document.setdefault("created_at", now)
        await self._collection.insert_one(document)
        return Doc(document)

    async def delete_all(self) -> int:
        result = await self._collection.delete_many({})
        return result.deleted_count
