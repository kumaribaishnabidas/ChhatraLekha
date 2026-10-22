"""MongoDB connection, collections and index management.

EduSynC stores its registry in MongoDB. The connection is created lazily on
first use so that importing the application never opens a socket, which keeps
the unit tests fast and lets the CLI scripts run without a server.

Two drivers are supported:

* ``motor`` against a real MongoDB server (production and development);
* ``mongomock_motor``, an in-memory asynchronous MongoDB, used only when
  ``ALLOW_IN_MEMORY_DB=true`` **and** ``MONGODB_URL`` is empty. It is a demo
  and test facility: the data is not persisted, and it is refused outright in
  production. A missing or unreachable ``MONGODB_URL`` is an error, never a
  silent downgrade to an in-memory database.
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
    "record_versions": "record_versions",
    "impact_assessments": "impact_assessments",
    "review_tasks": "review_tasks",
    "verification_tokens": "verification_tokens",
    "operation_status": "operation_status",
}


class MongoConnectionError(RuntimeError):
    """Raised when the configured MongoDB server cannot be reached."""


def redact_url(url: str) -> str:
    """A connection string with its credentials removed.

    A MongoDB connection string carries the database user's password. It must
    never reach a log, an error message or a health response, so it is
    stripped down to the host and the database before it is shown.
    """
    if not url:
        return ""
    if "@" in url:
        scheme, _, rest = url.partition("://")
        credentials, _, host = rest.rpartition("@")
        user = credentials.split(":", 1)[0]
        return f"{scheme}://{user}:***@{host}"
    return url


class Mongo:
    """A thin wrapper around the async MongoDB client and its collections."""

    def __init__(self) -> None:
        self._client: Any = None
        self._db: Any = None
        self._in_memory = False
        self._supports_transactions = False

    # ------------------------------------------------------------ lifecycle

    async def connect(self) -> Any:
        """Open the connection (idempotent) and return the database handle."""
        if self._db is not None:
            return self._db

        url = settings.mongodb_url.strip()
        if not url:
            if settings.is_production:
                raise MongoConnectionError(
                    "The in-memory database is a demo facility and is never used in "
                    "production. Set MONGODB_URL to a real MongoDB server."
                )
            if not settings.allow_in_memory_db:
                raise MongoConnectionError(
                    "MONGODB_URL is not set. Configure it to a real MongoDB server, "
                    "or set ALLOW_IN_MEMORY_DB=true to run the throwaway demo "
                    "database. The in-memory database is never used in production."
                )
            logger.warning(
                "=" * 74
                + "\n"
                + "  EduSynC is running on the IN-MEMORY DEMO DATABASE.\n"
                + "  Nothing is persisted, and the data disappears when the process\n"
                + "  stops. This mode is for demos and tests only - set MONGODB_URL\n"
                + "  to a real MongoDB server for anything real.\n"
                + "=" * 74
            )
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
            try:
                await self._client.admin.command("ping")
            except Exception as exc:  # noqa: BLE001
                raise MongoConnectionError(
                    "Could not reach the MongoDB server at "
                    f"{redact_url(url)!r}: {exc}"
                ) from exc

        self._db = self._client[settings.mongodb_database]
        self._supports_transactions = await self._detect_transaction_support()
        await self.ensure_indexes()
        logger.info(
            "Connected to MongoDB database '%s'%s",
            settings.mongodb_database,
            " (in-memory demo data, not persisted)" if self._in_memory else "",
        )
        return self._db

    async def _detect_transaction_support(self) -> bool:
        """Whether the server can run multi-document transactions.

        Transactions need a replica set. MongoDB Atlas provides one, so a
        deployed instance gets them; a standalone development server does not.
        """
        if self._in_memory:
            return False
        try:
            info = await self._client.admin.command("hello")
        except Exception:  # noqa: BLE001
            return False
        return bool(info.get("setName") or info.get("msg") == "isdbgrid")

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

    @property
    def supports_transactions(self) -> bool:
        """True when the server can run multi-document transactions."""
        return self._supports_transactions

    @property
    def client(self) -> Any:
        """The underlying client, for starting a transaction session."""
        if self._client is None:
            raise RuntimeError("The MongoDB connection has not been established.")
        return self._client

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
                "users",
                [("google_sub", 1)],
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
            (
                "policy_rules",
                [("policy_id", 1), ("active", 1)],
            ),
            (
                "record_versions",
                [("student_record_id", 1), ("version_no", -1)],
            ),
            (
                "impact_assessments",
                [("assessment_id", 1)],
            ),
            (
                "impact_assessments",
                [("student_record_id", 1), ("created_at", -1)],
            ),
            (
                "review_tasks",
                [("assessment_id", 1)],
            ),
            (
                "review_tasks",
                [("institution_id", 1), ("status", 1), ("severity", 1)],
            ),
            (
                "verification_tokens",
                [("token_hash", 1)],
            ),
            (
                "verification_tokens",
                [("student_record_id", 1), ("revoked", 1)],
            ),
            (
                "operation_status",
                [("operation_id", 1)],
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
