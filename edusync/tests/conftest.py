"""Shared pytest fixtures.

The whole suite runs against a throwaway SQLite database so that it never
touches a developer's working data.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

# The database URL has to be set before ``app.core.database`` is imported.
_TMP_DIR = tempfile.mkdtemp(prefix="edusync-tests-")
os.environ.setdefault(
    "DATABASE_URL", f"sqlite+aiosqlite:///{Path(_TMP_DIR) / 'edusync-test.db'}"
)
os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-long-enough-for-tests")
os.environ.setdefault("SEAL_HMAC_KEY", "test-seal-hmac-key")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "0")

import httpx  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402

from app.core.database import Base  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models import Institution, ProgramIntake, User  # noqa: E402
from app.models.enums import InstitutionType  # noqa: E402

TEST_DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_async_engine(TEST_DATABASE_URL, future=True)
SessionFactory = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)


@pytest.fixture(scope="session", autouse=True)
async def _create_schema():
    """Create the schema once for the whole session."""
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


@pytest.fixture
async def session():
    """A database session with a clean slate for every test."""
    async with SessionFactory() as db:
        for model in (
            __import__("app.models", fromlist=["Anomaly"]).Anomaly,
            __import__("app.models", fromlist=["AuditLog"]).AuditLog,
            __import__("app.models", fromlist=["Consent"]).Consent,
            __import__("app.models", fromlist=["Student"]).Student,
            __import__("app.models", fromlist=["ProgramIntake"]).ProgramIntake,
            __import__("app.models", fromlist=["Institution"]).Institution,
            __import__("app.models", fromlist=["User"]).User,
        ):
            await db.execute(model.__table__.delete())
        await db.commit()
        yield db
        await db.rollback()


@pytest.fixture
async def seeded(session):
    """A session with one institution, one programme and one student."""
    institution = Institution(
        institution_id="INST-T1",
        name="Test Institute of Technology",
        institution_type=InstitutionType.ENGINEERING,
        state="Karnataka",
        city="Bengaluru",
        affiliation_university="Test University",
        approval_year=2015,
        naac_grade="A+",
    )
    programme = ProgramIntake(
        program_id="BTECH_CSE",
        institution_id="INST-T1",
        program_name="B.Tech Computer Science",
        program_level="UG",
        approved_intake=10,
        max_supernumerary_nri=1,
        max_supernumerary_fn_oci=2,
        max_supernumerary_tfw=1,
        max_pmsss=1,
    )
    session.add_all([institution, programme])
    await session.commit()
    return session


@pytest.fixture
async def users(session):
    """One account per role."""
    rows = [
        User(
            user_id="USR-AICTE",
            email="aicte@edusync.test",
            full_name="Aicte Admin",
            role="aicte_admin",
            password_hash=hash_password("Test@1234"),
        ),
        User(
            user_id="USR-INST",
            email="principal@inst.test",
            full_name="Institution Admin",
            role="institution_admin",
            institution_id="INST-T1",
            password_hash=hash_password("Test@1234"),
        ),
        User(
            user_id="USR-VER",
            email="verifier@edusync.test",
            full_name="Verifier",
            role="verifier",
            password_hash=hash_password("Test@1234"),
        ),
        User(
            user_id="USR-STU",
            email="student@edusync.test",
            full_name="Student",
            role="student",
            password_hash=hash_password("Test@1234"),
        ),
    ]
    session.add_all(rows)
    await session.commit()
    return rows


@pytest.fixture
async def client(seeded, users):
    """An HTTP client bound to the ASGI app, overriding the database session."""
    from app.api import deps
    from app.main import app

    async def _get_session():
        async with SessionFactory() as db:
            yield db

    app.dependency_overrides[deps.get_db] = _get_session
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as http:
        yield http
    app.dependency_overrides.clear()


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
