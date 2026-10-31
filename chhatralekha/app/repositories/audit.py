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
        """The most recent entries, newest first.

        The order is the MongoDB ``_id`` order, which is the true insertion
        order. A timestamp is not precise enough to order entries that were
        written in the same millisecond, and the chain has to be verified in
        exactly the order it was written.
        """
        rows = (
            await self._collection.find({})
            .sort("_id", -1)
            .limit(limit)
            .to_list(length=None)
        )
        return docs(rows)

    async def oldest_first(self, limit: int = 500) -> list[Doc]:
        """The oldest entries first - the order the chain is verified in."""
        rows = (
            await self._collection.find({})
            .sort("_id", 1)
            .limit(limit)
            .to_list(length=None)
        )
        return docs(rows)

    async def last_hash(self) -> str:
        """The hash of the most recent entry (or the genesis hash)."""
        from app.services import audit_chain

        rows = (
            await self._collection.find({}).sort("_id", -1).limit(1).to_list(length=None)
        )
        if not rows:
            return audit_chain.GENESIS_HASH
        return rows[0].get("hash") or audit_chain.GENESIS_HASH

    async def count(self) -> int:
        return await self._collection.count_documents({})

    # --------------------------------------------------------------- writes

    async def insert(self, document: dict[str, Any], session: Any = None) -> Doc:
        """Append one chained entry."""
        now = utcnow()
        document = dict(document)
        document.setdefault("timestamp", now)
        document.setdefault("created_at", now)
        await self._collection.insert_one(document, session=session)
        return Doc(document)

    async def delete_all(self) -> int:
        result = await self._collection.delete_many({})
        return result.deleted_count
