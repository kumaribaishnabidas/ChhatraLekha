"""Repository for the institutions collection."""

from __future__ import annotations

from typing import Any, Optional

from app.models.documents import Doc, docs, utcnow


class InstitutionRepository:
    """Reads and writes the AICTE-approved institutions."""

    def __init__(self, collection: Any) -> None:
        self._collection = collection

    # ---------------------------------------------------------------- reads

    async def all(
        self,
        state: Optional[str] = None,
        q: Optional[str] = None,
        category: Optional[str] = None,
    ) -> list[Doc]:
        """Every institution, ordered by name with optional search and filters."""
        query: dict[str, Any] = {}
        if state:
            query["state"] = state
        if category:
            query["category"] = category.upper()
        if q and q.strip():
            clean_q = q.strip()
            query["$or"] = [
                {"name": {"$regex": clean_q, "$options": "i"}},
                {"institution_id": {"$regex": clean_q, "$options": "i"}},
                {"city": {"$regex": clean_q, "$options": "i"}},
            ]
        rows = await self._collection.find(query).sort("name", 1).to_list(length=None)
        return docs(rows)

    async def get(self, institution_id: str) -> Doc | None:
        """One institution by its AICTE identifier."""
        row = await self._collection.find_one({"institution_id": institution_id})
        return Doc(row) if row else None

    async def count(self) -> int:
        return await self._collection.count_documents({})

    async def states(self) -> list[str]:
        """The distinct states, for the filter dropdowns."""
        return await self._collection.distinct("state")

    # --------------------------------------------------------------- writes

    async def upsert(self, document: dict[str, Any]) -> Doc:
        """Create or replace one institution."""
        now = utcnow()
        document = dict(document)
        document.setdefault("created_at", now)
        document["updated_at"] = now
        await self._collection.replace_one(
            {"institution_id": document["institution_id"]}, document, upsert=True
        )
        stored = await self._collection.find_one(
            {"institution_id": document["institution_id"]}
        )
        return Doc(stored)

    async def insert_many(self, documents: list[dict[str, Any]]) -> int:
        """Insert many institutions."""
        now = utcnow()
        prepared = []
        for document in documents:
            item = dict(document)
            item.setdefault("created_at", now)
            item.setdefault("updated_at", now)
            prepared.append(item)
        if not prepared:
            return 0
        result = await self._collection.insert_many(prepared)
        return len(result.inserted_ids)

    async def delete_all(self) -> int:
        """Remove every institution (used by the seed script)."""
        result = await self._collection.delete_many({})
        return result.deleted_count
