"""Repository for the students collection.

``apaar_id`` is deliberately **not** uniquely indexed: the registry has to be
able to hold the same APAAR ID claimed by two institutions so that the
cross-institution duplicate check can fire. A unique index would hide the
very anomaly the platform exists to detect.
"""

from __future__ import annotations

from typing import Any, Optional

from app.models.documents import Doc, docs, match_token, utcnow


class StudentRepository:
    """Reads and writes the student enrolment records."""

    def __init__(self, collection: Any) -> None:
        self._collection = collection

    # ---------------------------------------------------------------- reads

    async def all(
        self,
        institution_id: Optional[str] = None,
        program_id: Optional[str] = None,
        quota: Optional[str] = None,
        record_status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 500,
        offset: int = 0,
    ) -> list[Doc]:
        query: dict[str, Any] = {}
        if institution_id:
            query["institution_id"] = institution_id
        if program_id:
            query["program_id"] = program_id
        if quota:
            query["admission_quota"] = quota
        if record_status:
            query["record_status"] = record_status
        if search:
            pattern = {"$regex": search.strip(), "$options": "i"}
            query["$or"] = [{"student_name": pattern}, {"apaar_id": pattern}]
        rows = (
            await self._collection.find(query)
            .sort("student_name", 1)
            .skip(offset)
            .limit(limit)
            .to_list(length=None)
        )
        return docs(rows)

    async def count(self, institution_id: Optional[str] = None) -> int:
        query = {"institution_id": institution_id} if institution_id else {}
        return await self._collection.count_documents(query)

    async def get(self, apaar_id: str) -> Doc | None:
        """Every enrolment record that claims this APAAR ID."""
        rows = await self._collection.find({"apaar_id": apaar_id}).to_list(length=None)
        return Doc(rows[0]) if rows else None

    async def all_for_apaar_id(self, apaar_id: str) -> list[Doc]:
        """Every enrolment record that claims this APAAR ID."""
        rows = await self._collection.find({"apaar_id": apaar_id}).to_list(length=None)
        return docs(rows)

    async def by_match_token(self, token: str) -> list[Doc]:
        """Every record whose keyed match token equals *token*."""
        if not token:
            return []
        rows = await self._collection.find({"apaar_id_hmac": token}).to_list(length=None)
        return docs(rows)

    async def by_roll_number(self, institution_id: str, roll_number: str) -> list[Doc]:
        rows = (
            await self._collection.find(
                {
                    "institution_id": institution_id,
                    "student_institute_roll_no": roll_number.strip(),
                }
            )
            .to_list(length=None)
        )
        return docs(rows)

    async def existing_apaar_ids(self, institution_id: str) -> set[str]:
        """The APAAR IDs already enrolled at one institution."""
        rows = (
            await self._collection.find(
                {"institution_id": institution_id}, {"apaar_id": 1}
            )
            .to_list(length=None)
        )
        return {row["apaar_id"] for row in rows if row.get("apaar_id")}

    async def seat_counts(self, institution_id: str) -> dict[str, dict[str, int]]:
        """The per-programme regular / supernumerary counts of an institution."""
        pipeline = [
            {"$match": {"institution_id": institution_id, "record_status": "ACTIVE"}},
            {
                "$group": {
                    "_id": {
                        "program_id": "$program_id",
                        "quota": "$admission_quota",
                    },
                    "count": {"$sum": 1},
                }
            },
        ]
        rows = await self._collection.aggregate(pipeline).to_list(length=None)
        counts: dict[str, dict[str, int]] = {}
        for row in rows:
            program_id = row["_id"]["program_id"]
            quota = row["_id"]["quota"]
            bucket = counts.setdefault(program_id, {})
            bucket[quota] = bucket.get(quota, 0) + int(row["count"])
        return counts

    # --------------------------------------------------------------- writes

    async def insert(self, document: dict[str, Any]) -> Doc:
        """Insert one enrolment record."""
        now = utcnow()
        document = dict(document)
        document.setdefault("record_status", "ACTIVE")
        document.setdefault("is_active", True)
        document.setdefault("created_at", now)
        document["updated_at"] = now
        if "apaar_id" in document:
            document["apaar_id_hmac"] = match_token(document["apaar_id"])
        result = await self._collection.insert_one(document)
        document["_id"] = result.inserted_id
        return Doc(document)

    async def insert_many(self, documents: list[dict[str, Any]]) -> list[str]:
        """Insert many enrolment records and return their identifiers."""
        now = utcnow()
        prepared = []
        for document in documents:
            item = dict(document)
            item.setdefault("record_status", "ACTIVE")
            item.setdefault("is_active", True)
            item.setdefault("created_at", now)
            item.setdefault("updated_at", now)
            if "apaar_id" in item:
                item["apaar_id_hmac"] = match_token(item["apaar_id"])
            prepared.append(item)
        if not prepared:
            return []
        result = await self._collection.insert_many(prepared)
        return [str(value) for value in result.inserted_ids]

    async def update(self, apaar_id: str, changes: dict[str, Any]) -> Doc | None:
        """Apply a partial update to every record that claims this APAAR ID."""
        changes = dict(changes)
        changes["updated_at"] = utcnow()
        if "apaar_id" in changes:
            changes["apaar_id_hmac"] = match_token(changes["apaar_id"])
        await self._collection.update_many({"apaar_id": apaar_id}, {"$set": changes})
        return await self.get(apaar_id)

    async def set_record_status(self, apaar_id: str, status: str) -> int:
        """Deactivate or reactivate every record that claims this APAAR ID."""
        result = await self._collection.update_many(
            {"apaar_id": apaar_id},
            {
                "$set": {
                    "record_status": status,
                    "is_active": status == "ACTIVE",
                    "updated_at": utcnow(),
                }
            },
        )
        return result.modified_count

    async def set_verification_status(self, apaar_ids: set[str], status: str) -> int:
        """Refresh the verification status of the given APAAR IDs."""
        if not apaar_ids:
            return 0
        result = await self._collection.update_many(
            {"apaar_id": {"$in": list(apaar_ids)}},
            {"$set": {"verification_status": status, "updated_at": utcnow()}},
        )
        return result.modified_count

    async def delete_all(self) -> int:
        result = await self._collection.delete_many({})
        return result.deleted_count
