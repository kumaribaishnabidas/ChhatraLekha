"""Repositories for the correction workflow.

Three collections carry the change history:

* ``record_versions`` - the immutable version history of every student record;
* ``impact_assessments`` - the impact assessment of one applied correction;
* ``review_tasks`` - the checklist an authorised reviewer works through.
"""

from __future__ import annotations

from typing import Any, Optional

from app.models.documents import Doc, docs, utcnow


class RecordVersionRepository:
    """The immutable version history of the student records."""

    def __init__(self, collection: Any) -> None:
        self._collection = collection

    async def for_record(self, student_record_id: str, limit: int = 200) -> list[Doc]:
        """The versions of one record, newest first."""
        rows = (
            await self._collection.find({"student_record_id": student_record_id})
            .sort("version_no", -1)
            .limit(limit)
            .to_list(length=None)
        )
        return docs(rows)

    async def next_version_no(self, student_record_id: str) -> int:
        """The version number the next correction will carry."""
        row = (
            await self._collection.find({"student_record_id": student_record_id})
            .sort("version_no", -1)
            .limit(1)
            .to_list(length=None)
        )
        return int(row[0].get("version_no", 0)) + 1 if row else 1

    async def insert(self, document: dict[str, Any], session: Any = None) -> Doc:
        now = utcnow()
        document = dict(document)
        document.setdefault("created_at", now)
        await self._collection.insert_one(document, session=session)
        return Doc(document)

    async def count(self) -> int:
        return await self._collection.count_documents({})


class ImpactAssessmentRepository:
    """The impact assessments of the applied corrections."""

    def __init__(self, collection: Any) -> None:
        self._collection = collection

    async def insert(self, document: dict[str, Any], session: Any = None) -> Doc:
        now = utcnow()
        document = dict(document)
        document.setdefault("created_at", now)
        document.setdefault("status", "open")
        await self._collection.insert_one(document, session=session)
        return Doc(document)

    async def get(self, assessment_id: str) -> Doc | None:
        row = await self._collection.find_one({"assessment_id": assessment_id})
        return Doc(row) if row else None

    async def for_record(self, student_record_id: str, limit: int = 50) -> list[Doc]:
        rows = (
            await self._collection.find({"student_record_id": student_record_id})
            .sort("created_at", -1)
            .limit(limit)
            .to_list(length=None)
        )
        return docs(rows)

    async def page(
        self,
        offset: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        student_record_id: Optional[str] = None,
    ) -> list[Doc]:
        query: dict[str, Any] = {}
        if status:
            query["status"] = status.lower()
        if student_record_id:
            query["student_record_id"] = student_record_id
        rows = (
            await self._collection.find(query)
            .sort("created_at", -1)
            .skip(offset)
            .limit(limit)
            .to_list(length=None)
        )
        return docs(rows)

    async def set_status(self, assessment_id: str, status: str) -> None:
        await self._collection.update_one(
            {"assessment_id": assessment_id}, {"$set": {"status": status.lower()}}
        )

    async def count(self) -> int:
        return await self._collection.count_documents({})


class ReviewTaskRepository:
    """The review checklist of the applied corrections."""

    def __init__(self, collection: Any) -> None:
        self._collection = collection

    async def insert_many(
        self, documents: list[dict[str, Any]], session: Any = None
    ) -> int:
        if not documents:
            return 0
        now = utcnow()
        prepared = []
        for document in documents:
            item = dict(document)
            item.setdefault("status", "open")
            item.setdefault("created_at", now)
            item.setdefault("updated_at", now)
            prepared.append(item)
        result = await self._collection.insert_many(prepared, session=session)
        return len(result.inserted_ids)

    async def get(self, task_id: str) -> Doc | None:
        row = await self._collection.find_one({"task_id": task_id})
        return Doc(row) if row else None

    async def for_assessment(self, assessment_id: str) -> list[Doc]:
        rows = (
            await self._collection.find({"assessment_id": assessment_id})
            .sort("severity", 1)
            .to_list(length=None)
        )
        return docs(rows)

    async def page(
        self,
        offset: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        institution_id: Optional[str] = None,
        assessment_id: Optional[str] = None,
    ) -> list[Doc]:
        query: dict[str, Any] = {}
        if status:
            query["status"] = status.lower()
        if severity:
            query["severity"] = severity.upper()
        if institution_id:
            query["institution_id"] = institution_id
        if assessment_id:
            query["assessment_id"] = assessment_id
        rows = (
            await self._collection.find(query)
            .sort("created_at", -1)
            .skip(offset)
            .limit(limit)
            .to_list(length=None)
        )
        return docs(rows)

    async def update(self, task_id: str, changes: dict[str, Any]) -> Doc | None:
        changes = dict(changes)
        changes["updated_at"] = utcnow()
        await self._collection.update_one({"task_id": task_id}, {"$set": changes})
        return await self.get(task_id)

    async def count(self, status: Optional[str] = None) -> int:
        query = {"status": status.lower()} if status else {}
        return await self._collection.count_documents(query)


class OperationStatusRepository:
    """The explicit operation log used when the server has no transactions.

    A correction is written in several steps. When the deployment cannot run a
    transaction, the operation is recorded here first, so that a crash between
    two steps leaves a visible, recoverable state instead of a half-applied
    correction.
    """

    def __init__(self, collection: Any) -> None:
        self._collection = collection

    async def start(self, operation_id: str, payload: dict[str, Any]) -> None:
        await self._collection.replace_one(
            {"operation_id": operation_id},
            {
                "operation_id": operation_id,
                "status": "in_progress",
                "payload": payload,
                "created_at": utcnow(),
                "updated_at": utcnow(),
            },
            upsert=True,
        )

    async def finish(self, operation_id: str, status: str, result: dict[str, Any]) -> None:
        await self._collection.update_one(
            {"operation_id": operation_id},
            {
                "$set": {
                    "status": status,
                    "result": result,
                    "updated_at": utcnow(),
                }
            },
        )

    async def get(self, operation_id: str) -> Doc | None:
        row = await self._collection.find_one({"operation_id": operation_id})
        return Doc(row) if row else None

    async def incomplete(self) -> list[Doc]:
        """The operations that were started but never finished."""
        rows = await self._collection.find({"status": "in_progress"}).to_list(length=None)
        return docs(rows)
