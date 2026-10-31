"""Repository for the batch submissions collection.

Every upload is recorded so that the provenance of a record - who submitted
it, from which file, and with what outcome - stays traceable.
"""

from __future__ import annotations

from typing import Any

from app.models.documents import Doc, docs, utcnow


class SubmissionRepository:
    """Reads and writes the batch submission history."""

    def __init__(self, collection: Any) -> None:
        self._collection = collection

    async def insert(self, document: dict[str, Any]) -> Doc:
        now = utcnow()
        document = dict(document)
        document.setdefault("created_at", now)
        document.setdefault("updated_at", now)
        await self._collection.insert_one(document)
        return Doc(document)

    async def recent(self, limit: int = 50) -> list[Doc]:
        rows = (
            await self._collection.find({})
            .sort("created_at", -1)
            .limit(limit)
            .to_list(length=None)
        )
        return docs(rows)

    async def count(self) -> int:
        return await self._collection.count_documents({})

    async def delete_all(self) -> int:
        result = await self._collection.delete_many({})
        return result.deleted_count
