"""MongoDB connection, collections and index management.

EduSynC stores its registry in MongoDB. The connection is created lazily on
first use so that importing the application never opens a socket, which keeps
the unit tests fast and lets the CLI scripts run without a server.

Two drivers are supported:

* ``motor`` against a real MongoDB server (production and development);
* ``mongomock_motor``, an in-memory asynchronous MongoDB, used automatically
  when ``MONGODB_URL`` is empty. It implements the query, projection,
  aggregation and index APIs that the application relies on, so the whole
  test-suite runs with no external service.
"""

from __future__ import annotations

import logging
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger("edusync.db")

settings = get_settings()

#: The collection names used by the platform.
COLLECTIONS = {
    "institutions": "institutions",
    "programmes": "programmes",
    "students": "students",
    "anomalies": "anomalies",
    "consents": "consents",
    "audit_events": "audit_events",
    "users": "users",
    "api_keys": "api_keys",
    "revoked_credentials": "revoked_credentials",
    "submissions": "submissions",
    "policy_rules": "policy_rules",
}


class Mongo:
    """A thin wrapper around the async MongoDB client and its collections."""

    def __init__(self) -> None:
        self._client: Any = None
        self._db: Any = None
        self._in_memory = False

    # ------------------------------------------------------------ lifecycle

    async def connect(self) -> Any:
        """Open the connection (idempotent) and return the database handle."""
        if self._db is not None:
            return self._db

        url = settings.mongodb_url.strip()
        if not url:
            logger.info("MONGODB_URL is not set - using the in-memory MongoDB.")
            from mongomock_motor import AsyncMongoMockClient

            self._client = AsyncMongoMockClient()
            self._in_memory = True
        else:
            from motor.motor_asyncio import AsyncIOMotorClient

            self._client = AsyncIOMotorClient(
                url,
                serverSelectionTimeoutMS=settings.mongodb_timeout_ms,
                uuidRepresentation="standard",
                tz_aware=True,
            )
            self._in_memory = False

        self._db = self._client[settings.mongodb_database]
        await self.ensure_indexes()
        logger.info(
            "Connected to MongoDB database '%s'%s",
            settings.mongodb_database,
            " (in-memory)" if self._in_memory else "",
        )
        return self._db

    async def disconnect(self) -> None:
        """Close the connection."""
        if self._client is not None:
            self._client.close()
        self._client = None
        self._db = None

    @property
    def is_connected(self) -> bool:
        return self._db is not None

    @property
    def is_in_memory(self) -> bool:
        return self._in_memory

    def db(self) -> Any:
        """The database handle, connecting on first use."""
        if self._db is None:
            raise RuntimeError(
                "The MongoDB connection has not been established. "
                "Call 'await mongo.connect()' during start-up."
            )
        return self._db

    def collection(self, name: str) -> Any:
        """A named collection."""
        return self.db()[COLLECTIONS.get(name, name)]

    # --------------------------------------------------------------- indexes

    async def ensure_indexes(self) -> None:
        """Create every index the query patterns rely on."""
        db = self.db()
        specifications: list[tuple[str, list[tuple[str, int]]]] = [
            (
                "institutions",
                [("institution_id", 1)],
            ),
            (
                "programmes",
                [("institution_id", 1), ("program_id", 1), ("academic_year", 1)],
            ),
            (
                "programmes",
                [("program_id", 1), ("academic_year", 1)],
            ),
            (
                "students",
                [("apaar_id", 1)],
            ),
            (
                "students",
                [("apaar_id_hmac", 1)],
            ),
            (
                "students",
                [("institution_id", 1), ("program_id", 1)],
            ),
            (
                "students",
                [("institution_id", 1), ("student_institute_roll_no", 1)],
            ),
            (
                "students",
                [("record_status", 1), ("academic_year", 1)],
            ),
            (
                "anomalies",
                [("severity", 1), ("review_status", 1)],
            ),
            (
                "anomalies",
                [("student_apaar_id", 1)],
            ),
            (
                "anomalies",
                [("institution_id", 1)],
            ),
            (
                "consents",
                [("student_apaar_id", 1)],
            ),
            (
                "consents",
                [("purpose", 1), ("status", 1)],
            ),
            (
                "audit_events",
                [("timestamp", -1)],
            ),
            (
                "audit_events",
                [("actor", 1)],
            ),
            (
                "users",
                [("email", 1)],
            ),
            (
                "api_keys",
                [("key_id", 1)],
            ),
            (
                "revoked_credentials",
                [("apaar_id", 1)],
            ),
            (
                "submissions",
                [("created_at", -1), ("status", 1)],
            ),
        ]

        for collection_name, keys in specifications:
            try:
                await db[collection_name].create_index(keys, name=_index_name(keys))
            except Exception as exc:  # noqa: BLE001 - an index must never block start-up
                logger.warning(
                    "Could not create the index %s on %s: %s",
                    _index_name(keys),
                    collection_name,
                    exc,
                )


def _index_name(keys: list[tuple[str, int]]) -> str:
    """A deterministic, legal index name."""
    return "_".join(f"{field}_{direction}" for field, direction in keys)


#: The shared connection holder.
mongo = Mongo()


async def get_db() -> Any:
    """FastAPI dependency returning the database handle."""
    if not mongo.is_connected:
        await mongo.connect()
    return mongo.db()


async def get_collection(name: str) -> Any:
    """FastAPI dependency returning one collection."""
    if not mongo.is_connected:
        await mongo.connect()
    return mongo.collection(name)
