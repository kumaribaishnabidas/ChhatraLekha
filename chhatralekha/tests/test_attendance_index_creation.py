"""Regression tests for attendance index option construction.

The unique attendance indexes carry their name inside their options dict.
Passing that dict through ``**options`` alongside an explicit ``name=``
argument would raise ``TypeError: got multiple values for keyword argument
'name'``. Startup catches broad exceptions, so the failure would otherwise be
silent and the uniqueness guarantees would never be created.
"""

from __future__ import annotations

from typing import Any

import pytest
from mongomock_motor import AsyncMongoMockClient
from pymongo.errors import DuplicateKeyError

from app.core.database import Mongo


class _FakeCollection:
    def __init__(self) -> None:
        self.calls: list[tuple[list[tuple[str, int]], dict[str, Any]]] = []

    async def create_index(self, keys: list[tuple[str, int]], **options: Any) -> str:
        self.calls.append((keys, options))
        return "index_name"


class _FakeDatabase:
    def __init__(self) -> None:
        self.collections: dict[str, _FakeCollection] = {}

    def __getitem__(self, name: str) -> _FakeCollection:
        return self.collections.setdefault(name, _FakeCollection())


@pytest.mark.asyncio
async def test_unique_attendance_indexes_are_created_with_a_single_name_argument():
    fake_db = _FakeDatabase()
    mongo = Mongo.__new__(Mongo)
    mongo.db = lambda: fake_db  # type: ignore[method-assign]

    await mongo.ensure_indexes()

    session_calls = fake_db.collections["attendance_sessions"].calls
    by_name = {options["name"]: (keys, options) for keys, options in session_calls}

    assert "uniq_attendance_session_daily" in by_name
    daily_keys, daily_options = by_name["uniq_attendance_session_daily"]
    assert daily_keys == [
        ("institution_id", 1),
        ("target_id", 1),
        ("session_date", 1),
        ("mode", 1),
    ]
    assert daily_options == {
        "name": "uniq_attendance_session_daily",
        "unique": True,
        "partialFilterExpression": {"mode": "DAILY"},
    }

    assert "uniq_attendance_session_period" in by_name
    _, period_options = by_name["uniq_attendance_session_period"]
    assert period_options == {
        "name": "uniq_attendance_session_period",
        "unique": True,
        "partialFilterExpression": {"mode": "PERIOD_WISE"},
    }

    record_calls = fake_db.collections["attendance_records"].calls
    record_by_name = {options["name"]: (keys, options) for keys, options in record_calls}
    assert "uniq_attendance_record_student" in record_by_name
    record_keys, record_options = record_by_name["uniq_attendance_record_student"]
    assert record_keys == [("session_id", 1), ("student_id", 1)]
    assert record_options["unique"] is True
    assert record_options["partialFilterExpression"] == {
        "session_id": {"$exists": True, "$ne": None}
    }

    policy_calls = fake_db.collections["attendance_policies"].calls
    _, policy_options = next(
        (keys, options)
        for keys, options in policy_calls
        if options["name"] == "uniq_attendance_policy_institution"
    )
    assert policy_options == {
        "name": "uniq_attendance_policy_institution",
        "unique": True,
    }


@pytest.mark.asyncio
async def test_sessionless_attendance_rows_are_not_deduplicated():
    """The unique index must not reject legacy rows that have no session."""
    db = AsyncMongoMockClient()["index_probe"]
    mongo = Mongo.__new__(Mongo)
    mongo.db = lambda: db  # type: ignore[method-assign]

    await mongo.ensure_indexes()

    records = db["attendance_records"]
    # Two historical rows for the same student without a session are valid.
    await records.insert_one({"student_id": "STU-1", "status": "PRESENT"})
    await records.insert_one({"student_id": "STU-1", "status": "ABSENT"})

    # A real duplicate within one session is still rejected.
    await records.insert_one({"session_id": "SES-1", "student_id": "STU-2"})
    with pytest.raises(DuplicateKeyError):
        await records.insert_one({"session_id": "SES-1", "student_id": "STU-2"})
