"""Repository for the programme intakes collection."""

from __future__ import annotations

from typing import Any

from app.models.documents import Doc, docs, utcnow


class ProgrammeRepository:
    """Reads and writes the sanctioned capacity of every programme."""

    def __init__(self, collection: Any) -> None:
        self._collection = collection

    # ---------------------------------------------------------------- reads

    async def all(self) -> list[Doc]:
        rows = await self._collection.find({}).sort("program_name", 1).to_list(length=None)
        return docs(rows)

    async def for_institution(self, institution_id: str) -> list[Doc]:
        rows = (
            await self._collection.find({"institution_id": institution_id})
            .sort("program_name", 1)
            .to_list(length=None)
        )
        return docs(rows)

    async def get(
        self, institution_id: str, program_id: str, academic_year: str | None = None
    ) -> Doc | None:
        query: dict[str, Any] = {
            "institution_id": institution_id,
            "program_id": program_id,
        }
        if academic_year:
            query["academic_year"] = academic_year
        row = await self._collection.find_one(query)
        return Doc(row) if row else None

    async def count(self) -> int:
        return await self._collection.count_documents({})

    async def total_approved_intake(self) -> int:
        """The sum of every sanctioned regular seat."""
        pipeline = [
            {"$group": {"_id": None, "total": {"$sum": "$approved_intake"}}}
        ]
        rows = await self._collection.aggregate(pipeline).to_list(length=None)
        return int(rows[0]["total"]) if rows else 0

    # --------------------------------------------------------------- writes

    async def upsert(self, document: dict[str, Any]) -> Doc:
        """Create or replace one programme's sanctioned capacity."""
        now = utcnow()
        document = dict(document)
        document.setdefault("academic_year", "2024-25")
        document.setdefault("policy_version", "aph-2024-01")
        document["total_sanctioned"] = (
            int(document.get("approved_intake", 0))
            + int(document.get("max_supernumerary_nri", 0))
            + int(document.get("max_supernumerary_fn_oci", 0))
            + int(document.get("max_supernumerary_tfw", 0))
            + int(document.get("max_pmsss", 0))
        )
        document.setdefault("created_at", now)
        document["updated_at"] = now
        await self._collection.replace_one(
            {
                "institution_id": document["institution_id"],
                "program_id": document["program_id"],
                "academic_year": document["academic_year"],
            },
            document,
            upsert=True,
        )
        stored = await self._collection.find_one(
            {
                "institution_id": document["institution_id"],
                "program_id": document["program_id"],
                "academic_year": document["academic_year"],
            }
        )
        return Doc(stored)

    async def insert_many(self, documents: list[dict[str, Any]]) -> int:
        now = utcnow()
        prepared = []
        for document in documents:
            item = dict(document)
            item.setdefault("academic_year", "2024-25")
            item.setdefault("policy_version", "aph-2024-01")
            item["total_sanctioned"] = (
                int(item.get("approved_intake", 0))
                + int(item.get("max_supernumerary_nri", 0))
                + int(item.get("max_supernumerary_fn_oci", 0))
                + int(item.get("max_supernumerary_tfw", 0))
                + int(item.get("max_pmsss", 0))
            )
            item.setdefault("created_at", now)
            item.setdefault("updated_at", now)
            prepared.append(item)
        if not prepared:
            return 0
        result = await self._collection.insert_many(prepared)
        return len(result.inserted_ids)

    async def delete_all(self) -> int:
        result = await self._collection.delete_many({})
        return result.deleted_count
