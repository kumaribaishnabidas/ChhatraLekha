"""Repository for the anomalies collection."""

from __future__ import annotations

from typing import Any, Optional

from app.models.documents import Doc, docs, utcnow


class AnomalyRepository:
    """Reads and writes the detected regulatory anomalies."""

    def __init__(self, collection: Any) -> None:
        self._collection = collection

    # ---------------------------------------------------------------- reads

    async def all(
        self,
        institution_id: Optional[str] = None,
        severity: Optional[str] = None,
        anomaly_type: Optional[str] = None,
        apaar_id: Optional[str] = None,
        review_status: Optional[str] = None,
        limit: int = 500,
        offset: int = 0,
    ) -> list[Doc]:
        query: dict[str, Any] = {}
        if institution_id:
            query["institution_id"] = institution_id
        if severity:
            query["severity"] = severity
        if anomaly_type:
            query["anomaly_type"] = anomaly_type
        if apaar_id:
            query["student_apaar_id"] = apaar_id
        if review_status:
            query["review_status"] = review_status
        rows = (
            await self._collection.find(query)
            .sort("detected_at", -1)
            .skip(offset)
            .limit(limit)
            .to_list(length=None)
        )
        return docs(rows)

    async def for_apaar_id(self, apaar_id: str) -> list[Doc]:
        rows = (
            await self._collection.find({"student_apaar_id": apaar_id})
            .to_list(length=None)
        )
        return docs(rows)

    async def count(self, institution_id: Optional[str] = None) -> int:
        query = {"institution_id": institution_id} if institution_id else {}
        return await self._collection.count_documents(query)

    async def summary(self, institution_id: Optional[str] = None) -> dict[str, Any]:
        """A roll-up of the anomaly register by severity, type and institution."""
        match: dict[str, Any] = {}
        if institution_id:
            match["institution_id"] = institution_id
        rows = (
            await self._collection.find(match, {"severity": 1, "anomaly_type": 1, "institution_id": 1})
            .to_list(length=None)
        )
        by_type: dict[str, int] = {}
        by_institution: dict[str, int] = {}
        by_severity: dict[str, int] = {"CRITICAL": 0, "HIGH": 0, "WARNING": 0, "INFO": 0}
        for row in rows:
            by_type[row.get("anomaly_type", "UNKNOWN")] = (
                by_type.get(row.get("anomaly_type", "UNKNOWN"), 0) + 1
            )
            by_institution[row.get("institution_id", "")] = (
                by_institution.get(row.get("institution_id", ""), 0) + 1
            )
            severity = row.get("severity", "WARNING")
            by_severity[severity] = by_severity.get(severity, 0) + 1
        return {
            "total": len(rows),
            "critical": by_severity.get("CRITICAL", 0),
            "high": by_severity.get("HIGH", 0),
            "warning": by_severity.get("WARNING", 0),
            "info": by_severity.get("INFO", 0),
            "by_type": by_type,
            "by_institution": by_institution,
        }

    # --------------------------------------------------------------- writes

    async def replace_all(
        self, findings: list[dict[str, Any]]
    ) -> int:
        """Replace the whole register with a fresh set of findings."""
        await self._collection.delete_many({})
        if not findings:
            return 0
        now = utcnow()
        prepared = []
        for finding in findings:
            item = dict(finding)
            item.setdefault("detected_at", now)
            item.setdefault("review_status", "PENDING")
            item.setdefault("resolved", False)
            prepared.append(item)
        result = await self._collection.insert_many(prepared)
        return len(result.inserted_ids)

    async def set_review_status(self, anomaly_id: str, review_status: str) -> Doc | None:
        """Move one finding into review."""
        from bson import ObjectId

        await self._collection.update_one(
            {"_id": ObjectId(anomaly_id)},
            {
                "$set": {
                    "review_status": review_status,
                    "resolved": review_status == "RESOLVED",
                    "reviewed_at": utcnow(),
                }
            },
        )
        row = await self._collection.find_one({"_id": ObjectId(anomaly_id)})
        return Doc(row) if row else None

    async def delete_all(self) -> int:
        result = await self._collection.delete_many({})
        return result.deleted_count
