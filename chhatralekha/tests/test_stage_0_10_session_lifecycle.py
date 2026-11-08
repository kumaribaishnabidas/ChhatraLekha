"""Security regression tests for Stage 0.10: Secure Authentication Session Lifecycle.

Validates stateful refresh-token rotation, jti tracking, cryptographic at-rest
token hashing, session revocation, reuse detection with token family invalidation,
server-side logout, concurrent race prevention, and audit sanitization.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import get_settings
from app.core.database import mongo
from app.core.security import (
    create_refresh_token,
    decode_token,
    hash_refresh_token,
)


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# -----------------------------------------------------------------------------
# 1. Valid refresh token succeeds
# -----------------------------------------------------------------------------
async def test_valid_refresh_token_succeeds(client):
    """A valid refresh token exchanged via /api/auth/refresh returns a fresh access token."""
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": "aicte@chhatralekha.test", "password": "Test@1234"},
    )
    assert login_resp.status_code == 200
    refresh_token = login_resp.json()["refresh_token"]

    refresh_resp = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 200
    body = refresh_resp.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["user_id"] == "USR-AICTE"
    assert body["role"] == "aicte_admin"

    claims = decode_token(body["access_token"], expected_type="access")
    assert claims["sub"] == "USR-AICTE"
    assert claims["role"] == "aicte_admin"


# -----------------------------------------------------------------------------
# 2. Successful refresh rotates the token
# -----------------------------------------------------------------------------
async def test_successful_refresh_rotates_the_token(client):
    """Refreshing an access token issues a new refresh token and records rotation lineage in MongoDB."""
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": "principal@inst.test", "password": "Test@1234"},
    )
    assert login_resp.status_code == 200
    r1 = login_resp.json()["refresh_token"]

    refresh_resp = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": r1},
    )
    assert refresh_resp.status_code == 200
    r2 = refresh_resp.json()["refresh_token"]

    assert r1 != r2, "Refresh token must rotate upon successful refresh."

    # Inspect MongoDB session persistence
    db = mongo.db()
    r1_hash = hash_refresh_token(r1)
    r2_hash = hash_refresh_token(r2)

    doc1 = await db["refresh_sessions"].find_one({"token_hash": r1_hash})
    doc2 = await db["refresh_sessions"].find_one({"token_hash": r2_hash})

    assert doc1 is not None
    assert doc2 is not None

    # Predecessor should be marked as rotated
    assert doc1["rotated_at"] is not None
    assert doc1["last_used_at"] is not None
    assert doc1["child_jti"] == doc2["jti"]

    # Child should be active with reference to parent
    assert doc2["parent_jti"] == doc1["jti"]
    assert doc2["family_id"] == doc1["family_id"]
    assert doc2["rotated_at"] is None
    assert doc2["is_revoked"] is False


# -----------------------------------------------------------------------------
# 3. Old refresh token is rejected after rotation
# -----------------------------------------------------------------------------
async def test_old_refresh_token_is_rejected_after_rotation(client):
    """An old refresh token that has already been rotated is immediately rejected."""
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": "principal@inst.test", "password": "Test@1234"},
    )
    r1 = login_resp.json()["refresh_token"]

    # Rotate r1 -> r2
    first_refresh = await client.post("/api/auth/refresh", json={"refresh_token": r1})
    assert first_refresh.status_code == 200

    # Attempt to use r1 again
    second_refresh = await client.post("/api/auth/refresh", json={"refresh_token": r1})
    assert second_refresh.status_code == 401
    assert "reuse detected" in second_refresh.json()["detail"].lower()


# -----------------------------------------------------------------------------
# 4. Expired refresh token is rejected
# -----------------------------------------------------------------------------
async def test_expired_refresh_token_is_rejected(client):
    """A refresh token whose expiration timestamp is in the past is rejected."""
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": "student@chhatralekha.test", "password": "Test@1234"},
    )
    r1 = login_resp.json()["refresh_token"]

    # Manually backdate the session expiry in MongoDB
    r1_hash = hash_refresh_token(r1)
    past_time = datetime.now(timezone.utc) - timedelta(days=1)
    await mongo.db()["refresh_sessions"].update_one(
        {"token_hash": r1_hash},
        {"$set": {"expires_at": past_time}},
    )

    refresh_resp = await client.post("/api/auth/refresh", json={"refresh_token": r1})
    assert refresh_resp.status_code == 401
    assert "expired" in refresh_resp.json()["detail"].lower()


# -----------------------------------------------------------------------------
# 5. Revoked refresh token is rejected
# -----------------------------------------------------------------------------
async def test_revoked_refresh_token_is_rejected(client):
    """A refresh token that was flagged as revoked is rejected."""
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": "student@chhatralekha.test", "password": "Test@1234"},
    )
    r1 = login_resp.json()["refresh_token"]

    r1_hash = hash_refresh_token(r1)
    await mongo.db()["refresh_sessions"].update_one(
        {"token_hash": r1_hash},
        {"$set": {"is_revoked": True, "revoked_reason": "MANUAL_TEST"}},
    )

    refresh_resp = await client.post("/api/auth/refresh", json={"refresh_token": r1})
    assert refresh_resp.status_code == 401
    assert "revoked" in refresh_resp.json()["detail"].lower()


# -----------------------------------------------------------------------------
# 6. Unknown token identifier is rejected
# -----------------------------------------------------------------------------
async def test_unknown_token_identifier_is_rejected(client):
    """A forged or unknown refresh token with an unregistered jti is rejected."""
    # Generate a signed JWT with a novel jti never recorded in the DB
    rogue_token = create_refresh_token(
        subject="USR-STU",
        jti="unregistered-jti-xyz-9999",
        family_id="fam_fake_12345",
    )

    refresh_resp = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": rogue_token},
    )
    assert refresh_resp.status_code == 401
    assert "unknown" in refresh_resp.json()["detail"].lower() or "invalid" in refresh_resp.json()["detail"].lower()


async def test_untracked_legacy_refresh_token_without_jti_is_rejected(client):
    """Legacy tokens bypassed session revocation and therefore must not be exchanged."""
    settings = get_settings()
    now = int(datetime.now(timezone.utc).timestamp())
    legacy_token = jwt.encode(
        {"sub": "USR-STU", "type": "refresh", "iat": now, "exp": now + 3600},
        settings.secret_key,
        algorithm=settings.algorithm,
    )

    response = await client.post("/api/auth/refresh", json={"refresh_token": legacy_token})
    assert response.status_code == 401
    assert "unknown refresh token" in response.json()["detail"].lower()
    assert await mongo.db()["refresh_sessions"].count_documents({"user_id": "USR-STU"}) == 0


# -----------------------------------------------------------------------------
# 7. Refresh-token reuse is detected and revokes token family
# -----------------------------------------------------------------------------
async def test_refresh_token_reuse_detected_and_family_revoked(client):
    """When a consumed refresh token is presented again, the system revokes the entire token family."""
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": "principal@inst.test", "password": "Test@1234"},
    )
    r1 = login_resp.json()["refresh_token"]

    # Rotate r1 -> r2
    first_refresh = await client.post("/api/auth/refresh", json={"refresh_token": r1})
    r2 = first_refresh.json()["refresh_token"]

    # Rotate r2 -> r3
    second_refresh = await client.post("/api/auth/refresh", json={"refresh_token": r2})
    r3 = second_refresh.json()["refresh_token"]

    # Attacker re-plays r1 (which was already rotated)
    reuse_attempt = await client.post("/api/auth/refresh", json={"refresh_token": r1})
    assert reuse_attempt.status_code == 401
    assert "reuse detected" in reuse_attempt.json()["detail"].lower()

    # Now the legitimate active token r3 MUST be revoked as well!
    legitimate_attempt = await client.post("/api/auth/refresh", json={"refresh_token": r3})
    assert legitimate_attempt.status_code == 401
    assert "revoked" in legitimate_attempt.json()["detail"].lower()

    # Verify audit event was logged
    audit_event = await mongo.db()["audit_events"].find_one({"action": "REFRESH_TOKEN_REUSE_DETECTED"})
    assert audit_event is not None
    assert audit_event["category"] == "SECURITY"
    assert audit_event["actor"] == "USR-INST"


# -----------------------------------------------------------------------------
# 8. Logout revokes the active session
# -----------------------------------------------------------------------------
async def test_logout_revokes_the_active_session(client):
    """POST /api/auth/logout invalidates the caller's refresh token session."""
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": "aicte@chhatralekha.test", "password": "Test@1234"},
    )
    access_token = login_resp.json()["access_token"]
    refresh_token = login_resp.json()["refresh_token"]

    logout_resp = await client.post(
        "/api/auth/logout",
        json={"refresh_token": refresh_token},
        headers=auth(access_token),
    )
    assert logout_resp.status_code == 200
    assert logout_resp.json()["status"] == "success"

    # Refreshing with the logged-out token must fail
    refresh_resp = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_resp.status_code == 401
    assert "revoked" in refresh_resp.json()["detail"].lower()


# -----------------------------------------------------------------------------
# 9. Repeated logout is safe and idempotent
# -----------------------------------------------------------------------------
async def test_repeated_logout_is_safe_and_idempotent(client):
    """Invoking logout repeatedly with the same token is safe and returns a consistent response."""
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": "verifier@chhatralekha.test", "password": "Test@1234"},
    )
    access_token = login_resp.json()["access_token"]
    refresh_token = login_resp.json()["refresh_token"]

    logout1 = await client.post(
        "/api/auth/logout",
        json={"refresh_token": refresh_token},
        headers=auth(access_token),
    )
    assert logout1.status_code == 200

    logout2 = await client.post(
        "/api/auth/logout",
        json={"refresh_token": refresh_token},
        headers=auth(access_token),
    )
    assert logout2.status_code == 200
    assert logout2.json()["status"] == "success"


# -----------------------------------------------------------------------------
# 10. Another user cannot revoke someone else's session
# -----------------------------------------------------------------------------
async def test_another_user_cannot_revoke_someone_elses_session(client):
    """A user cannot revoke a session that belongs to a different principal."""
    # User 1 (Admin) logs in
    admin_login = await client.post(
        "/api/auth/login",
        json={"email": "aicte@chhatralekha.test", "password": "Test@1234"},
    )
    admin_refresh = admin_login.json()["refresh_token"]

    # User 2 (Student) logs in
    student_login = await client.post(
        "/api/auth/login",
        json={"email": "student@chhatralekha.test", "password": "Test@1234"},
    )
    student_access = student_login.json()["access_token"]

    # Student attempts to revoke Admin's refresh session
    evil_logout = await client.post(
        "/api/auth/logout",
        json={"refresh_token": admin_refresh},
        headers=auth(student_access),
    )
    assert evil_logout.status_code == 403
    assert "another user" in evil_logout.json()["detail"].lower()

    # Admin's refresh token should still be active and usable
    admin_refresh_resp = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": admin_refresh},
    )
    assert admin_refresh_resp.status_code == 200


# -----------------------------------------------------------------------------
# 11. Inactive users cannot refresh
# -----------------------------------------------------------------------------
async def test_inactive_users_cannot_refresh(client):
    """Deactivated user accounts are barred from issuing new tokens via refresh."""
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": "student@chhatralekha.test", "password": "Test@1234"},
    )
    refresh_token = login_resp.json()["refresh_token"]

    # Deactivate the student account
    await mongo.db()["users"].update_one(
        {"user_id": "USR-STU"},
        {"$set": {"is_active": False}},
    )

    refresh_resp = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_resp.status_code == 401
    assert "not active" in refresh_resp.json()["detail"].lower()


# -----------------------------------------------------------------------------
# 12. Concurrent refresh attempts cannot create two valid descendants
# -----------------------------------------------------------------------------
async def test_concurrent_refresh_attempts_cannot_create_two_descendants(client):
    """Simultaneous concurrent refresh calls with the same token result in at most one success."""
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": "principal@inst.test", "password": "Test@1234"},
    )
    r1 = login_resp.json()["refresh_token"]

    # Execute two parallel refresh requests
    res1, res2 = await asyncio.gather(
        client.post("/api/auth/refresh", json={"refresh_token": r1}),
        client.post("/api/auth/refresh", json={"refresh_token": r1}),
        return_exceptions=False,
    )

    statuses = [res1.status_code, res2.status_code]
    # Exactly one succeeded (200), or due to reuse detection one succeeded and the race was rejected
    assert 200 in statuses
    # At most one 200 OK response is permitted
    assert statuses.count(200) == 1, f"Concurrent refresh allowed split-brain descendants: {statuses}"


# -----------------------------------------------------------------------------
# 13. Token values never appear in logs or audit trail
# -----------------------------------------------------------------------------
async def test_token_values_never_appear_in_logs_or_audit_trail(client):
    """Neither access tokens nor plaintext refresh tokens are logged in MongoDB or audit records."""
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": "aicte@chhatralekha.test", "password": "Test@1234"},
    )
    access_token = login_resp.json()["access_token"]
    refresh_token = login_resp.json()["refresh_token"]

    # Refresh
    refresh_resp = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    new_refresh = refresh_resp.json()["refresh_token"]

    # Logout
    await client.post(
        "/api/auth/logout",
        json={"refresh_token": new_refresh},
        headers=auth(access_token),
    )

    # Check all audit events in MongoDB
    audit_events = await mongo.db()["audit_events"].find({}).to_list(length=None)
    assert len(audit_events) > 0

    tokens_to_check = [access_token, refresh_token, new_refresh]
    for event in audit_events:
        event_str = str(event)
        for tok in tokens_to_check:
            assert tok not in event_str, f"Token leaked into audit event: {event}"

    # Check refresh_sessions collection
    sessions = await mongo.db()["refresh_sessions"].find({}).to_list(length=None)
    for s in sessions:
        session_str = str(s)
        for tok in tokens_to_check:
            assert tok not in session_str, f"Plaintext token leaked into refresh_sessions: {s}"
        assert "token_hash" in s
        assert s["token_hash"] != ""


# -----------------------------------------------------------------------------
# 14. Existing login and demo restrictions remain intact
# -----------------------------------------------------------------------------
async def test_existing_login_and_demo_restrictions_remain_intact(client):
    """Verifies wrong password rejection, demo role whitelisting, and escalation blocking."""
    # Invalid password
    bad_login = await client.post(
        "/api/auth/login",
        json={"email": "aicte@chhatralekha.test", "password": "WrongPassword!"},
    )
    assert bad_login.status_code == 401

    # Allowed demo persona succeeds and generates stateful refresh session
    demo_resp = await client.post("/api/auth/demo-login", json={"role": "student"})
    assert demo_resp.status_code == 200
    demo_data = demo_resp.json()
    assert demo_data["role"] == "student"
    assert demo_data["refresh_token"]

    # Disallowed demo role blocked
    blocked_demo = await client.post("/api/auth/demo-login", json={"role": "national_admin"})
    assert blocked_demo.status_code == 403

    # Unknown demo role blocked
    invalid_demo = await client.post("/api/auth/demo-login", json={"role": "superman"})
    assert invalid_demo.status_code == 400
