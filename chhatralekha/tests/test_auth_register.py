"""Tests for self-service user registration endpoint POST /api/auth/register."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.core.database import mongo
from app.main import app

settings = get_settings()


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_register_student_success():
    """A student can successfully self-register and then sign in."""
    db = mongo.db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"{settings.api_prefix}/auth/register",
            json={
                "email": "aarav.student@example.org",
                "password": "Password123!",
                "full_name": "Aarav Sharma",
                "role": "student",
                "identifier": "123456789012",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "success"
        assert data["email"] == "aarav.student@example.org"
        assert data["role"] == "student"
        assert data["requires_approval"] is False
        assert data["user_id"].startswith("usr_")

        # Verify user persisted in database
        saved = await db["users"].find_one({"email": "aarav.student@example.org"})
        assert saved is not None
        assert saved["full_name"] == "Aarav Sharma"
        assert saved["role"] == "student"
        assert saved["apaar_id"] == "123456789012"
        assert saved["is_active"] is True

        # Verify audit log was recorded
        audit = await db["audit_events"].find_one({
            "action": "REGISTER",
            "subject": saved["user_id"],
        })
        assert audit is not None

        # Verify the newly registered user can login with their password
        login_resp = await client.post(
            f"{settings.api_prefix}/auth/login",
            json={
                "email": "aarav.student@example.org",
                "password": "Password123!",
            },
        )
        assert login_resp.status_code == 200
        token_data = login_resp.json()
        assert token_data["role"] == "student"
        assert token_data["user_id"] == saved["user_id"]
        assert token_data["apaar_id"] == "123456789012"


@pytest.mark.anyio
async def test_register_parent_and_teacher_success():
    """Parent and teacher roles can self-register directly."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register Parent
        resp_parent = await client.post(
            f"{settings.api_prefix}/auth/register",
            json={
                "email": "priya.parent@example.org",
                "password": "Password123!",
                "full_name": "Priya Sharma",
                "role": "parent",
            },
        )
        assert resp_parent.status_code == 201
        assert resp_parent.json()["role"] == "parent"
        assert resp_parent.json()["requires_approval"] is False

        # Register Teacher
        resp_teacher = await client.post(
            f"{settings.api_prefix}/auth/register",
            json={
                "email": "rajesh.teacher@example.org",
                "password": "Password123!",
                "full_name": "Rajesh Kumar",
                "role": "teacher",
            },
        )
        assert resp_teacher.status_code == 201
        assert resp_teacher.json()["role"] == "teacher"
        assert resp_teacher.json()["requires_approval"] is False


@pytest.mark.anyio
async def test_register_institution_admin_pending():
    """Institution admin self-registration assigns pending role and records join request."""
    db = mongo.db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"{settings.api_prefix}/auth/register",
            json={
                "email": "principal@delhi-school.edu.in",
                "password": "Password123!",
                "full_name": "Dr. Ramesh Verma",
                "role": "institution_admin",
                "identifier": "Delhi Model Public School",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "success"
        assert data["role"] == "pending"
        assert data["requires_approval"] is True
        assert "requires review" in data["message"].lower()

        # Check user record in database has role "pending"
        saved_user = await db["users"].find_one({"email": "principal@delhi-school.edu.in"})
        assert saved_user is not None
        assert saved_user["role"] == "pending"

        # Check membership request was generated
        join_req = await db["membership_requests"].find_one({"user_id": saved_user["user_id"]})
        assert join_req is not None
        assert join_req["status"] == "PENDING"
        assert join_req["requested_role"] == "institution_admin"
        assert join_req["institution_name"] == "Delhi Model Public School"

        # Verify audit log recorded
        audit = await db["audit_events"].find_one({
            "action": "REGISTER_INSTITUTION_ADMIN_PENDING",
            "subject": saved_user["user_id"],
        })
        assert audit is not None


@pytest.mark.anyio
async def test_register_restricted_roles_rejected():
    """Platform, regulator, and authority roles cannot be self-registered."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        restricted_roles = [
            "national_admin",
            "aicte_admin",
            "platform_operator",
            "state_admin",
            "district_admin",
            "regulator_admin",
            "university_admin",
            "academic_admin",
            "verifier",
        ]
        for restricted_role in restricted_roles:
            resp = await client.post(
                f"{settings.api_prefix}/auth/register",
                json={
                    "email": f"hacker_{restricted_role}@example.org",
                    "password": "Password123!",
                    "full_name": "Malicious Actor",
                    "role": restricted_role,
                },
            )
            assert resp.status_code == 403, f"Expected 403 for {restricted_role}"
            assert "restricted" in resp.json()["detail"].lower()


@pytest.mark.anyio
async def test_register_invalid_role_rejected():
    """Arbitrary roles are rejected with 400 Bad Request."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"{settings.api_prefix}/auth/register",
            json={
                "email": "invalid@example.org",
                "password": "Password123!",
                "full_name": "Invalid Role Tester",
                "role": "super_vip_user",
            },
        )
        assert resp.status_code == 400
        assert "Invalid registration role" in resp.json()["detail"]


@pytest.mark.anyio
async def test_register_duplicate_email_anti_enumeration():
    """Duplicate email registration returns generic 400 without revealing account state."""
    db = mongo.db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First registration
        resp1 = await client.post(
            f"{settings.api_prefix}/auth/register",
            json={
                "email": "duplicate.test@example.org",
                "password": "Password123!",
                "full_name": "First User",
                "role": "student",
            },
        )
        assert resp1.status_code == 201

        # Second registration with same email (different case)
        resp2 = await client.post(
            f"{settings.api_prefix}/auth/register",
            json={
                "email": "Duplicate.Test@Example.ORG",
                "password": "DifferentPassword123!",
                "full_name": "Second User",
                "role": "student",
            },
        )
        assert resp2.status_code == 400
        assert "Unable to complete registration" in resp2.json()["detail"]
        assert "duplicate" not in resp2.json()["detail"].lower()
        assert "already exists with this email" in resp2.json()["detail"]

        # Verify duplicate audit event
        audit = await db["audit_events"].find_one({
            "action": "REGISTER_DUPLICATE_ATTEMPT",
            "subject": "duplicate.test@example.org",
        })
        assert audit is not None


@pytest.mark.anyio
async def test_register_weak_password_rejected():
    """Password policy violations are rejected with 400 Bad Request."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Too short (< 8 chars)
        resp = await client.post(
            f"{settings.api_prefix}/auth/register",
            json={
                "email": "short.pass@example.org",
                "password": "Pass1",
                "full_name": "Short Password",
                "role": "student",
            },
        )
        assert resp.status_code == 400
        assert "at least 8 characters" in resp.json()["detail"]

        # Missing digit
        resp_no_digit = await client.post(
            f"{settings.api_prefix}/auth/register",
            json={
                "email": "no.digit@example.org",
                "password": "PasswordOnlyLetters",
                "full_name": "No Digit",
                "role": "student",
            },
        )
        assert resp_no_digit.status_code == 400
        assert "at least one digit" in resp_no_digit.json()["detail"]
