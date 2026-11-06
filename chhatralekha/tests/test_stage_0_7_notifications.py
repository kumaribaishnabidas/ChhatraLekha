"""Stage 0.7: Notifications, Announcements & Communication System Tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

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
async def second_student_headers(async_client: AsyncClient):
    # Simulate a second user by logging in as parent/guardian
    resp = await async_client.post("/api/auth/demo-login", json={"role": "parent"})
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
async def test_all_ten_notification_categories_supported(async_client: AsyncClient, student_auth_headers):
    """Verify that all 10 notification categories are present and retrievable."""
    res = await async_client.get("/api/notifications", headers=student_auth_headers)
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 5

    # Check category filter for RESULTS
    results_res = await async_client.get("/api/notifications?category=RESULTS", headers=student_auth_headers)
    assert results_res.status_code == 200
    results_items = results_res.json()
    for item in results_items:
        assert item["category"] == "RESULTS"

    # Check category filter for TIMETABLE
    tt_res = await async_client.get("/api/notifications?category=TIMETABLE", headers=student_auth_headers)
    assert tt_res.status_code == 200
    for item in tt_res.json():
        assert item["category"] == "TIMETABLE"


@pytest.mark.asyncio
async def test_paginated_notifications_endpoint(async_client: AsyncClient, student_auth_headers):
    """Verify pagination model and response metadata."""
    res = await async_client.get("/api/notifications/paged?page=1&page_size=3", headers=student_auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "total_pages" in data
    assert "unread_count" in data
    assert data["page"] == 1
    assert data["page_size"] == 3
    assert len(data["items"]) <= 3
    assert data["total"] >= len(data["items"])


@pytest.mark.asyncio
async def test_security_category_cannot_be_disabled(async_client: AsyncClient, student_auth_headers):
    """Critical Security Requirement: SECURITY notifications cannot be suppressed by user."""
    # Attempt to update preferences with subscribed_categories excluding SECURITY
    update_payload = {
        "subscribed_categories": ["ACADEMIC", "ATTENDANCE"],
        "language_preference": "hi",
    }
    res = await async_client.put(
        "/api/notifications/preferences",
        json=update_payload,
        headers=student_auth_headers,
    )
    assert res.status_code == 200
    prefs = res.json()
    # SECURITY must be automatically retained
    assert "SECURITY" in prefs["subscribed_categories"]
    assert "ACADEMIC" in prefs["subscribed_categories"]
    assert "ATTENDANCE" in prefs["subscribed_categories"]
    assert prefs["language_preference"] == "hi"


@pytest.mark.asyncio
async def test_device_token_registration_and_revocation(async_client: AsyncClient, student_auth_headers):
    """Verify push notification device registration and revocation lifecycle."""
    device_token = "fcm_mock_token_abc123xyz789_android"
    payload = {
        "token": device_token,
        "platform": "ANDROID",
        "device_name": "Pixel 8 Pro",
        "device_model": "Google Pixel",
        "app_version": "2.0.0",
    }

    # Register device
    reg_res = await async_client.post(
        "/api/notifications/devices",
        json=payload,
        headers=student_auth_headers,
    )
    assert reg_res.status_code == 200
    device_data = reg_res.json()
    assert device_data["token"] == device_token
    assert device_data["platform"] == "ANDROID"
    assert device_data["device_name"] == "Pixel 8 Pro"

    # List registered devices
    list_res = await async_client.get("/api/notifications/devices", headers=student_auth_headers)
    assert list_res.status_code == 200
    devices = list_res.json()
    assert any(d["token"] == device_token for d in devices)

    # Revoke device
    del_res = await async_client.delete(
        f"/api/notifications/devices/{device_token}",
        headers=student_auth_headers,
    )
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "REVOKED"

    # Revoke again should 404
    del_again = await async_client.delete(
        f"/api/notifications/devices/{device_token}",
        headers=student_auth_headers,
    )
    assert del_again.status_code == 404


@pytest.mark.asyncio
async def test_notification_ownership_isolation(
    async_client: AsyncClient, student_auth_headers, second_student_headers
):
    """Verify that a user cannot mark or delete another user's personal notification."""
    # List student notifications
    list_res = await async_client.get("/api/notifications", headers=student_auth_headers)
    assert list_res.status_code == 200
    student_notifs = list_res.json()
    target_nid = student_notifs[0]["notification_id"]

    # Second user tries to delete student's notification (must fail with 404 access denied)
    del_res = await async_client.delete(
        f"/api/notifications/{target_nid}",
        headers=second_student_headers,
    )
    assert del_res.status_code == 404


@pytest.mark.asyncio
async def test_announcement_workflow_with_scheduling_and_summary(
    async_client: AsyncClient, admin_auth_headers, student_auth_headers
):
    """Test publication, audience targeting, scheduling, delivery summary, and edit."""
    now = datetime.now(timezone.utc)
    future_time = (now + timedelta(days=2)).isoformat()
    expiry_time = (now + timedelta(days=10)).isoformat()

    ann_payload = {
        "title": "Annual Inter-School Science Conclave 2026",
        "content": "All students from grades 9 through 12 are invited to present research posters.",
        "priority": "HIGH",
        "target_scope": "CLASS",
        "target_classes": ["Class 9-A", "Class 10-A", "Class 11-A"],
        "target_departments": ["Sciences"],
        "scheduled_for": future_time,
        "expires_at": expiry_time,
        "delivery_channels": ["IN_APP", "EMAIL", "PUSH"],
        "attachment_title": "Conclave_Guidelines.pdf",
        "attachment_url": "https://cdn.chhatralekha.edu.in/docs/conclave-2026.pdf",
    }

    # Admin publishes scheduled announcement
    create_res = await async_client.post(
        "/api/announcements",
        json=ann_payload,
        headers=admin_auth_headers,
    )
    assert create_res.status_code == 200
    created = create_res.json()
    ann_id = created["announcement_id"]
    assert created["status"] == "SCHEDULED"
    assert created["delivery_summary"] is not None
    assert "in_app" in created["delivery_summary"]
    assert "email" in created["delivery_summary"]
    assert "push" in created["delivery_summary"]

    # Delivery summary endpoint
    summary_res = await async_client.get(
        f"/api/announcements/{ann_id}/delivery-summary",
        headers=admin_auth_headers,
    )
    assert summary_res.status_code == 200
    summary_data = summary_res.json()
    assert summary_data["announcement_id"] == ann_id
    assert summary_data["status"] == "SCHEDULED"
    assert summary_data["acknowledgements_count"] == 0

    # Edit announcement (e.g. change title and set scheduled_for to past to publish)
    past_time = (now - timedelta(hours=1)).isoformat()
    update_res = await async_client.put(
        f"/api/announcements/{ann_id}",
        json={"title": "Updated: Annual Inter-School Science Conclave 2026", "scheduled_for": past_time},
        headers=admin_auth_headers,
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["title"] == "Updated: Annual Inter-School Science Conclave 2026"
    assert updated["status"] == "PUBLISHED"

    # Student acknowledges notice
    ack_res = await async_client.post(
        f"/api/announcements/{ann_id}/acknowledge",
        headers=student_auth_headers,
    )
    assert ack_res.status_code == 200
    assert ack_res.json()["message"] == "Acknowledged successfully."

    # Summary should now reflect acknowledgement
    summary_res2 = await async_client.get(
        f"/api/announcements/{ann_id}/delivery-summary",
        headers=admin_auth_headers,
    )
    assert summary_res2.status_code == 200
    assert summary_res2.json()["acknowledgements_count"] == 1
