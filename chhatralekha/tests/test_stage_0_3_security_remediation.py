"""Regression and security test suite for Stage 0.3 remediation.

Covers all 15 required security scenarios:
1. Production demo-login rejection.
2. Demo role escalation rejection.
3. Valid development demo login.
4. Missing student-profile relationship.
5. Student A attempting to access Student B's attendance.
6. Student A attempting to access Student B's results.
7. Parent accessing an unrelated student.
8. Authorized parent accessing a linked child.
9. Teacher accessing a student outside assigned permissions.
10. Cross-institution record access rejection.
11. Notification ownership enforcement.
12. Expired email verification code rejection.
13. Incorrect verification attempt limit.
14. Universal verification bypass rejection.
15. Successful email verification and code reuse rejection.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from app.core.config import Settings
from app.core.database import mongo
from app.core.security import create_access_token


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def create_test_user(
    db,
    user_id: str,
    role: str,
    institution_id: str | None = None,
    apaar_id: str | None = None,
    email: str | None = None,
) -> str:
    """Helper to seed active user in MongoDB and generate signed token."""
    await db["users"].insert_one({
        "user_id": user_id,
        "email": email or f"{user_id.lower()}@chhatralekha.test",
        "full_name": f"User {user_id}",
        "role": role,
        "institution_id": institution_id,
        "apaar_id": apaar_id,
        "is_active": True,
    })
    extra = {}
    if apaar_id:
        extra["apaar_id"] = apaar_id
    return create_access_token(
        subject=user_id,
        role=role,
        institution_id=institution_id,
        extra_claims=extra if extra else None,
    )


# ------------------------------------------------------------- 1, 2, 3: Demo Login Security (SEC-AUTH-01)


@pytest.mark.asyncio
async def test_production_demo_login_rejected(client: AsyncClient, monkeypatch):
    """1. Demo login must be rejected in production environments."""
    prod_settings = Settings(environment="production")
    monkeypatch.setattr("app.api.auth.get_settings", lambda: prod_settings)

    resp = await client.post("/api/auth/demo-login", json={"role": "student"})
    assert resp.status_code == 403
    assert "disabled in production" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_demo_role_escalation_rejected(client: AsyncClient):
    """2. Disallow arbitrary role escalation and administrative roles in demo login."""
    # Attempting to escalate to national_admin
    resp = await client.post("/api/auth/demo-login", json={"role": "national_admin"})
    assert resp.status_code == 403
    assert "role escalation" in resp.json()["detail"].lower()

    # Attempting to escalate to platform_operator
    resp = await client.post("/api/auth/demo-login", json={"role": "platform_operator"})
    assert resp.status_code == 403
    assert "role escalation" in resp.json()["detail"].lower()

    # Attempting an unknown persona
    resp = await client.post("/api/auth/demo-login", json={"role": "super_root_admin"})
    assert resp.status_code == 400
    assert "invalid demo role" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_valid_development_demo_login(client: AsyncClient):
    """3. Valid development demo login succeeds for permitted personas."""
    resp = await client.post("/api/auth/demo-login", json={"role": "student"})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["role"] == "student"


# ------------------------------------------------------------- 4: Student Fallback Isolation (SEC-ISO-01 & SEC-ISO-02)


@pytest.mark.asyncio
async def test_missing_student_profile_relationship_returns_none_or_404(client: AsyncClient):
    """4. An account with no linked student record must never receive arbitrary student data."""
    db = mongo.db()
    # Insert an existing third-party student record in the DB
    await db["students"].insert_one({
        "apaar_id": "998877665544",
        "student_name": "Victim Student",
        "institution_id": "INST-T1",
        "guardian_phone_masked": "+91 99**** **00",
    })

    # Create a fresh student user with NO apaar_id linked
    token = await create_test_user(
        db,
        user_id="USR-UNLINKED-STU",
        role="student",
        institution_id="INST-T1",
        apaar_id=None,
    )

    # Calling /api/profile/me should return student_details = None, NOT the third-party student!
    resp = await client.get("/api/profile/me", headers=auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["student_details"] is None

    # Calling /api/me/profile should return 404 Not Found, NOT the third-party student!
    resp = await client.get("/api/me/profile", headers=auth(token))
    assert resp.status_code == 404
    assert "no student record linked" in resp.json()["detail"].lower()


# ------------------------------------------------------------- 5, 6: Student IDOR Protection (SEC-ATT-01 & SEC-ASM-01)


@pytest.mark.asyncio
async def test_student_a_cannot_access_student_b_attendance(client: AsyncClient):
    """5. Student A cannot supply Student B's identifier to view attendance."""
    db = mongo.db()
    token_a = await create_test_user(
        db,
        user_id="USR-STU-A",
        role="student",
        institution_id="INST-T1",
        apaar_id="111100000001",
    )
    resp = await client.get("/api/attendance/my-summary?student_id=222200000002", headers=auth(token_a))
    assert resp.status_code == 403
    assert "own attendance record" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_student_a_cannot_access_student_b_results(client: AsyncClient):
    """6. Student A cannot supply Student B's identifier to view examination results."""
    db = mongo.db()
    token_a = await create_test_user(
        db,
        user_id="USR-STU-A-RES",
        role="student",
        institution_id="INST-T1",
        apaar_id="111100000001",
    )
    resp = await client.get("/api/assessments/my-results?student_id=222200000002", headers=auth(token_a))
    assert resp.status_code == 403
    assert "own examination results" in resp.json()["detail"].lower()


# ------------------------------------------------------------- 7, 8: Parent Access Control


@pytest.mark.asyncio
async def test_parent_cannot_access_unrelated_student(client: AsyncClient):
    """7. Parent cannot access an unrelated student's attendance or results."""
    db = mongo.db()
    token_parent = await create_test_user(
        db,
        user_id="USR-PARENT-UNRELATED",
        role="parent",
    )
    # Attempting unrelated student attendance
    resp = await client.get("/api/attendance/my-summary?student_id=999900000009", headers=auth(token_parent))
    assert resp.status_code == 403
    assert "verified linked children" in resp.json()["detail"].lower()

    # Attempting unrelated student results
    resp = await client.get("/api/assessments/my-results?student_id=999900000009", headers=auth(token_parent))
    assert resp.status_code == 403
    assert "verified linked children" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_authorized_parent_can_access_linked_child(client: AsyncClient):
    """8. Authorized parent can access records for verified linked children."""
    db = mongo.db()
    parent_id = "USR-PARENT-AUTH"
    child_apaar = "888800000008"

    await db["guardian_relationships"].insert_one({
        "parent_user_id": parent_id,
        "student_id": child_apaar,
        "status": "VERIFIED",
    })
    token_parent = await create_test_user(
        db,
        user_id=parent_id,
        role="parent",
    )

    # Authorized child attendance
    resp = await client.get(f"/api/attendance/my-summary?student_id={child_apaar}", headers=auth(token_parent))
    assert resp.status_code == 200
    assert resp.json()["student_id"] == child_apaar

    # Authorized child results
    resp = await client.get(f"/api/assessments/my-results?student_id={child_apaar}", headers=auth(token_parent))
    assert resp.status_code == 200


# ------------------------------------------------------------- 9, 10: Teacher & Cross-Institution Scoping


@pytest.mark.asyncio
async def test_teacher_cannot_access_student_without_institution(client: AsyncClient):
    """9. Staff without an institution association cannot query student attendance."""
    db = mongo.db()
    token_unassociated_teacher = await create_test_user(
        db,
        user_id="USR-TEACHER-NO-INST",
        role="teacher",
        institution_id=None,
    )
    resp = await client.get("/api/attendance/my-summary?student_id=123456789012", headers=auth(token_unassociated_teacher))
    assert resp.status_code == 403
    assert "not associated" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_cross_institution_record_access_rejected(client: AsyncClient):
    """10. Teacher from Institution A cannot access student belonging to Institution B."""
    db = mongo.db()
    student_apaar = "777700000007"
    await db["students"].insert_one({
        "apaar_id": student_apaar,
        "institution_id": "INST-B",
        "student_name": "Student from Inst B",
    })

    token_teacher_a = await create_test_user(
        db,
        user_id="USR-TEACHER-INST-A",
        role="teacher",
        institution_id="INST-A",
    )

    resp = await client.get(f"/api/attendance/my-summary?student_id={student_apaar}", headers=auth(token_teacher_a))
    assert resp.status_code == 403
    assert "another institution" in resp.json()["detail"].lower()


# ------------------------------------------------------------- 11: Notification Ownership Enforcement (SEC-NOTIF-01)


@pytest.mark.asyncio
async def test_notification_ownership_enforced(client: AsyncClient):
    """11. One user cannot mark as read or delete another user's notifications."""
    db = mongo.db()
    user_a = "USR-NOTIF-OWNER"
    user_b = "USR-NOTIF-ATTACKER"
    ntf_id = "ntf-sec-test-01"

    token_a = await create_test_user(db, user_id=user_a, role="student")
    token_b = await create_test_user(db, user_id=user_b, role="student")

    await db["notifications"].insert_one({
        "notification_id": ntf_id,
        "user_id": user_a,
        "title": "Confidential Warning",
        "message": "Only for User A",
        "is_read": False,
        "created_at": datetime.now(timezone.utc),
    })

    # User B attempts to mark User A's notification as read
    resp = await client.post(f"/api/notifications/{ntf_id}/read", headers=auth(token_b))
    assert resp.status_code == 404
    assert "not found or access denied" in resp.json()["detail"].lower()

    # User B attempts to delete User A's notification
    resp = await client.delete(f"/api/notifications/{ntf_id}", headers=auth(token_b))
    assert resp.status_code == 404
    assert "not found or access denied" in resp.json()["detail"].lower()

    # User A can mark their own notification as read
    resp = await client.post(f"/api/notifications/{ntf_id}/read", headers=auth(token_a))
    assert resp.status_code == 200

    # User A can delete their own notification
    resp = await client.delete(f"/api/notifications/{ntf_id}", headers=auth(token_a))
    assert resp.status_code == 200


# ------------------------------------------------------------- 12, 13, 14, 15: Email Verification (SEC-EMAIL-01)


@pytest.mark.asyncio
async def test_expired_email_verification_code_rejected(client: AsyncClient):
    """12. Expired email verification code (>15 minutes) is rejected."""
    db = mongo.db()
    user_id = "USR-EMAIL-TEST-01"
    email = "expired.verify@example.com"
    token = await create_test_user(db, user_id=user_id, role="student")

    # Seed pending verification backdated 20 minutes ago
    past = datetime.now(timezone.utc) - timedelta(minutes=20)
    await db["users"].update_one(
        {"user_id": user_id},
        {
            "$set": {
                "pending_verifications": {
                    email: {
                        "code": "654321",
                        "email_type": "PERSONAL",
                        "created_at": past,
                        "expires_at": past + timedelta(minutes=15),
                        "attempts": 0,
                        "max_attempts": 5,
                        "consumed": False,
                    }
                }
            }
        },
    )

    resp = await client.post(
        "/api/profiles/me/verify-email",
        json={"email": email, "code": "654321"},
        headers=auth(token),
    )
    assert resp.status_code == 400
    assert "expired" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_email_verification_attempt_limit_exceeded(client: AsyncClient):
    """13. Attempt limit (5) blocks brute-force verification attacks."""
    db = mongo.db()
    user_id = "USR-EMAIL-TEST-02"
    email = "brute.force@example.com"
    token = await create_test_user(db, user_id=user_id, role="student")

    now = datetime.now(timezone.utc)
    await db["users"].update_one(
        {"user_id": user_id},
        {
            "$set": {
                "pending_verifications": {
                    email: {
                        "code": "888999",
                        "email_type": "PERSONAL",
                        "created_at": now,
                        "expires_at": now + timedelta(minutes=15),
                        "attempts": 5,  # Already at limit
                        "max_attempts": 5,
                        "consumed": False,
                    }
                }
            }
        },
    )

    resp = await client.post(
        "/api/profiles/me/verify-email",
        json={"email": email, "code": "000000"},
        headers=auth(token),
    )
    assert resp.status_code == 400
    assert "maximum verification attempts exceeded" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_universal_verification_bypass_code_rejected(client: AsyncClient):
    """14. Universal bypass code '123456' is rejected when real code is different."""
    db = mongo.db()
    user_id = "USR-EMAIL-TEST-03"
    email = "nobypass@example.com"
    token = await create_test_user(db, user_id=user_id, role="student")

    now = datetime.now(timezone.utc)
    await db["users"].update_one(
        {"user_id": user_id},
        {
            "$set": {
                "pending_verifications": {
                    email: {
                        "code": "741852",
                        "email_type": "PERSONAL",
                        "created_at": now,
                        "expires_at": now + timedelta(minutes=15),
                        "attempts": 0,
                        "max_attempts": 5,
                        "consumed": False,
                    }
                }
            }
        },
    )

    resp = await client.post(
        "/api/profiles/me/verify-email",
        json={"email": email, "code": "123456"},
        headers=auth(token),
    )
    assert resp.status_code == 400
    assert "invalid verification code" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_successful_email_verification_and_reuse_rejection(client: AsyncClient):
    """15. Successful email verification succeeds once and rejects code reuse."""
    db = mongo.db()
    user_id = "USR-EMAIL-TEST-04"
    email = "success.verify@example.com"
    token = await create_test_user(db, user_id=user_id, role="student")

    now = datetime.now(timezone.utc)
    await db["users"].update_one(
        {"user_id": user_id},
        {
            "$set": {
                "pending_verifications": {
                    email: {
                        "code": "333444",
                        "email_type": "PERSONAL",
                        "created_at": now,
                        "expires_at": now + timedelta(minutes=15),
                        "attempts": 0,
                        "max_attempts": 5,
                        "consumed": False,
                    }
                }
            }
        },
    )

    # First attempt with correct code succeeds
    resp1 = await client.post(
        "/api/profiles/me/verify-email",
        json={"email": email, "code": "333444"},
        headers=auth(token),
    )
    assert resp1.status_code == 200
    assert resp1.json()["status"] == "VERIFIED"

    # Second attempt with the same code is rejected (cannot reuse consumed code)
    resp2 = await client.post(
        "/api/profiles/me/verify-email",
        json={"email": email, "code": "333444"},
        headers=auth(token),
    )
    assert resp2.status_code == 400
    assert "invalid or expired" in resp2.json()["detail"].lower()
