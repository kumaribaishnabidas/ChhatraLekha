"""Unit tests for the Notification Module."""

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
async def admin_auth_headers(async_client: AsyncClient):
    resp = await async_client.post("/api/auth/demo-login", json={"role": "school_admin"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_list_notifications_seeds_and_returns_items(async_client: AsyncClient, student_auth_headers):
    res = await async_client.get("/api/notifications", headers=student_auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "notification_id" in data[0]
    assert "category" in data[0]
    assert "priority" in data[0]


@pytest.mark.asyncio
async def test_unread_count_endpoint(async_client: AsyncClient, student_auth_headers):
    res = await async_client.get("/api/notifications/unread-count", headers=student_auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "unread_count" in data
    assert "urgent_count" in data
    assert data["unread_count"] >= 0


@pytest.mark.asyncio
async def test_mark_as_read_and_mark_all_read(async_client: AsyncClient, student_auth_headers):
    # First ensure notifications exist
    list_res = await async_client.get("/api/notifications", headers=student_auth_headers)
    notifs = list_res.json()
    assert len(notifs) > 0
    nid = notifs[0]["notification_id"]

    # Mark single
    res = await async_client.post(f"/api/notifications/{nid}/read", headers=student_auth_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "SUCCESS"
    assert res.json()["read_at"] is not None

    # Mark all
    all_res = await async_client.post("/api/notifications/read-all", headers=student_auth_headers)
    assert all_res.status_code == 200
    assert all_res.json()["status"] == "SUCCESS"

    # Check unread count is 0
    count_res = await async_client.get("/api/notifications/unread-count", headers=student_auth_headers)
    assert count_res.json()["unread_count"] == 0


@pytest.mark.asyncio
async def test_notification_preferences(async_client: AsyncClient, student_auth_headers):
    get_res = await async_client.get("/api/notifications/preferences", headers=student_auth_headers)
    assert get_res.status_code == 200
    prefs = get_res.json()
    assert prefs["in_app_enabled"] is True

    update_payload = {
        "quiet_hours_enabled": True,
        "quiet_hours_start": "23:00",
        "quiet_hours_end": "06:00",
        "email_enabled": False,
    }
    put_res = await async_client.put(
        "/api/notifications/preferences",
        json=update_payload,
        headers=student_auth_headers,
    )
    assert put_res.status_code == 200
    updated = put_res.json()
    assert updated["quiet_hours_enabled"] is True
    assert updated["quiet_hours_start"] == "23:00"
    assert updated["email_enabled"] is False


@pytest.mark.asyncio
async def test_broadcast_notification_authorization(async_client: AsyncClient, student_auth_headers, admin_auth_headers):
    broadcast_data = {
        "title": "Semester Registration Open",
        "message": "All students must register for elective courses by 10 December.",
        "category": "ACADEMIC",
        "priority": "HIGH",
        "target_role": "student",
    }

    # Student cannot broadcast (403 Forbidden)
    forbidden_res = await async_client.post(
        "/api/notifications/broadcast",
        json=broadcast_data,
        headers=student_auth_headers,
    )
    assert forbidden_res.status_code == 403

    # Admin can broadcast (200 OK)
    allowed_res = await async_client.post(
        "/api/notifications/broadcast",
        json=broadcast_data,
        headers=admin_auth_headers,
    )
    assert allowed_res.status_code == 200
    created = allowed_res.json()
    assert created["title"] == broadcast_data["title"]
    assert created["category"] == "ACADEMIC"
    assert created["priority"] == "HIGH"


@pytest.mark.asyncio
async def test_delete_notification(async_client: AsyncClient, student_auth_headers):
    list_res = await async_client.get("/api/notifications", headers=student_auth_headers)
    notifs = list_res.json()
    target_id = notifs[0]["notification_id"]

    del_res = await async_client.delete(f"/api/notifications/{target_id}", headers=student_auth_headers)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "DELETED"
