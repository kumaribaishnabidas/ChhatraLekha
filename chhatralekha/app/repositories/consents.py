"""Repository for the consents collection."""

from __future__ import annotations

from typing import Any

from app.models.documents import Doc, consent_docs, utcnow


class ConsentRepository:
    """Reads and writes the purpose-wise consent ledger."""

    def __init__(self, collection: Any) -> None:
        self._collection = collection

    # ---------------------------------------------------------------- reads

    async def for_apaar_id(self, apaar_id: str) -> list[Doc]:
        rows = (
            await self._collection.find({"student_apaar_id": apaar_id})
            .sort("recorded_at", -1)
            .to_list(length=None)
        )
        return consent_docs(rows)

    async def all(self, limit: int = 500) -> list[Doc]:
        rows = (
            await self._collection.find({})
            .sort("recorded_at", -1)
            .limit(limit)
            .to_list(length=None)
        )
        return consent_docs(rows)

    async def count(self) -> int:
        return await self._collection.count_documents({})

    # --------------------------------------------------------------- writes

    async def insert(self, document: dict[str, Any]) -> Doc:
        """Append one consent record."""
        now = utcnow()
        document = dict(document)
        document.setdefault("recorded_at", now)
        document.setdefault("created_at", now)
        document["updated_at"] = now
        await self._collection.insert_one(document)
        return Doc(document)

    async def delete_all(self) -> int:
        result = await self._collection.delete_many({})
        return result.deleted_count
