"""Shared pytest fixtures.

The whole suite runs against the in-memory MongoDB, so it never needs a
MongoDB server and never touches a developer's working data.
"""

from __future__ import annotations

import os

import pytest

# The in-memory MongoDB is selected by leaving MONGODB_URL empty. It has to
# be set before ``app.core.database`` is imported.
os.environ["MONGODB_URL"] = ""
# The test-suite runs on the in-memory database, which has to be asked for
# explicitly - the application never falls back to it silently.
os.environ["ALLOW_IN_MEMORY_DB"] = "true"
os.environ.setdefault(
    "SECRET_KEY", "test-secret-key-that-is-long-enough-for-tests"
)
os.environ.setdefault("SEAL_HMAC_KEY", "test-seal-hmac-key")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "0")
# bcrypt at production cost (12 rounds) would dominate the runtime of the
# suite, because every test needs a hashed password.
os.environ.setdefault("BCRYPT_ROUNDS", "4")

import httpx  # noqa: E402

from app.core.database import mongo  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.enums import InstitutionType  # noqa: E402

COLLECTIONS = (
    "anomalies",
    "audit_events",
    "consents",
    "students",
    "programmes",
    "institutions",
    "users",
    "api_keys",
    "revoked_credentials",
    "submissions",
)

#: The password hash of the test accounts, computed once for the whole suite.
TEST_PASSWORD_HASH = hash_password("Test@1234")


@pytest.fixture(scope="session", autouse=True)
async def _connect():
    """Open the in-memory MongoDB once for the whole session."""
    await mongo.connect()
    yield
    await mongo.disconnect()


@pytest.fixture(autouse=True)
async def _clean():
    """Every test starts with an empty database."""
    db = mongo.db()
    for name in COLLECTIONS:
        await db[name].delete_many({})
    yield


@pytest.fixture
async def seeded():
    """One institution and one programme."""
    db = mongo.db()
    await db["institutions"].insert_one(
        {
            "institution_id": "INST-T1",
            "name": "Test Institute of Technology",
            "institution_type": InstitutionType.ENGINEERING.value,
            "state": "Karnataka",
            "city": "Bengaluru",
            "affiliation_university": "Test University",
            "approval_year": 2015,
            "naac_grade": "A+",
            "is_active": True,
        }
    )
    await db["programmes"].insert_one(
        {
            "institution_id": "INST-T1",
            "program_id": "BTECH_CSE",
            "program_name": "B.Tech Computer Science",
            "program_level": "UG",
            "academic_year": "2024-25",
            "policy_version": "aph-2024-01",
            "approved_intake": 10,
            "max_supernumerary_nri": 1,
            "max_supernumerary_fn_oci": 2,
            "max_supernumerary_tfw": 1,
            "max_pmsss": 1,
            "total_sanctioned": 15,
        }
    )
    return db


@pytest.fixture
async def users(seeded):
    """One account per role."""
    db = mongo.db()
    await db["users"].insert_many(
        [
            {
                "user_id": "USR-AICTE",
                "email": "aicte@edusync.test",
                "full_name": "Aicte Admin",
                "role": "aicte_admin",
                "institution_id": None,
                "password_hash": TEST_PASSWORD_HASH,
                "is_active": True,
            },
            {
                "user_id": "USR-INST",
                "email": "principal@inst.test",
                "full_name": "Institution Admin",
                "role": "institution_admin",
                "institution_id": "INST-T1",
                "password_hash": TEST_PASSWORD_HASH,
                "is_active": True,
            },
            {
                "user_id": "USR-VER",
                "email": "verifier@edusync.test",
                "full_name": "Verifier",
                "role": "verifier",
                "institution_id": None,
                "password_hash": TEST_PASSWORD_HASH,
                "is_active": True,
            },
            {
                "user_id": "USR-STU",
                "email": "student@edusync.test",
                "full_name": "Student",
                "role": "student",
                "institution_id": None,
                "password_hash": TEST_PASSWORD_HASH,
                "is_active": True,
            },
        ]
    )
    return db


@pytest.fixture
async def client(seeded, users):
    """An HTTP client bound to the ASGI app."""
    from app.main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as http:
        yield http


async def login(client: httpx.AsyncClient, email: str) -> str:
    """Sign in and return the bearer token."""
    response = await client.post(
        "/api/auth/login", json={"email": email, "password": "Test@1234"}
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture
async def aicte_token(client):
    return await login(client, "aicte@edusync.test")


@pytest.fixture
async def institution_token(client):
    return await login(client, "principal@inst.test")


@pytest.fixture
async def verifier_token(client):
    return await login(client, "verifier@edusync.test")
