"""Tests for complete profile page, platform profile pictures, and student email system."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def async_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client


@pytest.fixture
async def student_auth_headers(async_client: AsyncClient):
    resp = await async_client.post("/api/auth/demo-login", json={"role": "student"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def teacher_auth_headers(async_client: AsyncClient):
    resp = await async_client.post("/api/auth/demo-login", json={"role": "teacher"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def admin_auth_headers(async_client: AsyncClient):
    resp = await async_client.post("/api/auth/demo-login", json={"role": "school_admin"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_get_my_profile_student(async_client: AsyncClient, student_auth_headers: dict):
    resp = await async_client.get("/api/profile/me", headers=student_auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "student"
    assert "user_id" in data
    assert "profile_completion_percentage" in data
    assert data["profile_completion_percentage"] >= 20
    assert "profile_pictures" in data
    assert data["profile_pictures"]["use_common"] is True
    assert data["student_details"] is not None
    assert "attendance_percentage" in data["student_details"]
    assert "guardian_name" in data["student_details"]


@pytest.mark.asyncio
async def test_get_my_profile_teacher(async_client: AsyncClient, teacher_auth_headers: dict):
    resp = await async_client.get("/api/profile/me", headers=teacher_auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "teacher"
    assert data["teacher_details"] is not None
    assert "employee_id" in data["teacher_details"]
    assert "subjects_taught" in data["teacher_details"]
    assert len(data["teacher_details"]["subjects_taught"]) > 0


@pytest.mark.asyncio
async def test_get_my_profile_admin(async_client: AsyncClient, admin_auth_headers: dict):
    resp = await async_client.get("/api/profile/me", headers=admin_auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "admin_details" in data
    assert data["admin_details"] is not None
    assert "admin_designation" in data["admin_details"]


@pytest.mark.asyncio
async def test_update_profile_permitted_fields(async_client: AsyncClient, student_auth_headers: dict):
    update_payload = {
        "full_name": "Aarav K. Sharma",
        "mobile": "+91 91234 56789",
        "preferred_language": "hi",
    }
    resp = await async_client.put("/api/profile/me", headers=student_auth_headers, json=update_payload)
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"

    # Verify updated values
    resp_get = await async_client.get("/api/profile/me", headers=student_auth_headers)
    assert resp_get.status_code == 200
    data = resp_get.json()
    assert data["full_name"] == "Aarav K. Sharma"
    assert data["mobile"] == "+91 91234 56789"
    assert data["preferred_language"] == "hi"


@pytest.mark.asyncio
async def test_student_email_verification_lifecycle(async_client: AsyncClient, student_auth_headers: dict):
    # 1. Request verification for personal email
    req_resp = await async_client.post(
        "/api/profile/email",
        headers=student_auth_headers,
        json={"email_type": "personal", "email": "aarav.student@mymail.in"},
    )
    assert req_resp.status_code == 200
    req_data = req_resp.json()
    assert req_data["status"] == "pending_verification"
    code = req_data.get("demo_verification_code") or "123456"

    # 2. Complete verification
    verify_resp = await async_client.post(
        "/api/profile/verify-email",
        headers=student_auth_headers,
        json={"email_type": "personal", "code": code},
    )
    assert verify_resp.status_code == 200
    assert verify_resp.json()["status"] == "verified"

    # 3. Verify institution email separately
    inst_resp = await async_client.post(
        "/api/profile/email",
        headers=student_auth_headers,
        json={"email_type": "institution", "email": "aarav.sharma@inst0421.edu.in"},
    )
    assert inst_resp.status_code == 200
    inst_code = inst_resp.json().get("demo_verification_code") or "123456"

    verify_inst_resp = await async_client.post(
        "/api/profile/verify-email",
        headers=student_auth_headers,
        json={"email_type": "institution", "code": inst_code},
    )
    assert verify_inst_resp.status_code == 200

    # 4. Confirm in profile
    prof_resp = await async_client.get("/api/profile/me", headers=student_auth_headers)
    prof_data = prof_resp.json()
    assert prof_data["personal_email"] == "aarav.student@mymail.in"
    assert prof_data["personal_email_verified"] is True
    assert prof_data["institution_email"] == "aarav.sharma@inst0421.edu.in"
    assert prof_data["institution_email_verified"] is True


@pytest.mark.asyncio
async def test_platform_profile_pictures_management(async_client: AsyncClient, student_auth_headers: dict):
    # 1. Upload common profile picture
    pic_resp = await async_client.post(
        "/api/profile/picture",
        headers=student_auth_headers,
        json={"platform": "common", "image_url": "https://example.com/avatars/common.png"},
    )
    assert pic_resp.status_code == 200
    pics = pic_resp.json()
    assert pics["common_url"] == "https://example.com/avatars/common.png"

    # 2. Upload custom web profile picture
    web_resp = await async_client.post(
        "/api/profile/picture",
        headers=student_auth_headers,
        json={"platform": "web", "image_url": "https://example.com/avatars/web.png"},
    )
    assert web_resp.status_code == 200
    assert web_resp.json()["web_url"] == "https://example.com/avatars/web.png"

    # 3. Toggle picture settings
    settings_resp = await async_client.put(
        "/api/profile/picture/settings",
        headers=student_auth_headers,
        json={"use_common": False},
    )
    assert settings_resp.status_code == 200
    assert settings_resp.json()["use_common"] is False

    # 4. Check active avatar in profile
    prof_resp = await async_client.get("/api/profile/me", headers=student_auth_headers)
    assert prof_resp.json()["active_avatar_url"] == "https://example.com/avatars/web.png"

    # 5. Delete web avatar
    del_resp = await async_client.delete(
        "/api/profile/picture?platform=web",
        headers=student_auth_headers,
    )
    assert del_resp.status_code == 200
    assert del_resp.json()["web_url"] is None


@pytest.mark.asyncio
async def test_get_active_sessions(async_client: AsyncClient, student_auth_headers: dict):
    resp = await async_client.get("/api/profile/sessions", headers=student_auth_headers)
    assert resp.status_code == 200
    sessions = resp.json()
    assert len(sessions) >= 1
    assert any(s["is_current"] for s in sessions)
