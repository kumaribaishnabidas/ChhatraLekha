"""Tests for the opaque verification tokens and the in-memory safety rules."""

from __future__ import annotations

import pytest

from app.core.database import Mongo, MongoConnectionError, mongo
from app.models.documents import redact_apaar
from app.repositories.tokens import hash_token, tokens_match


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def create_student(client, token, **overrides):
    payload = {
        "apaar_id": "984210357890",
        "student_name": "Rahul Kumar",
        "date_of_birth": "2004-03-12",
        "gender": "M",
        "institution_id": "INST-T1",
        "program_id": "BTECH_CSE",
        "academic_year": "2024-25",
        "admission_quota": "REGULAR_MERIT",
        "enrollment_date": "2024-07-01",
        "student_institute_roll_no": "CSE-0001",
        "nationality": "Indian",
    }
    payload.update(overrides)
    return await client.post("/api/students", json=payload, headers=auth(token))


# ------------------------------------------------------------------ issuing


async def test_a_token_is_issued_and_only_its_hash_is_stored(
    client, institution_token
):
    created = await create_student(client, institution_token)
    record_id = created.json()["record_id"]

    response = await client.post(
        "/api/verification-tokens",
        json={"student_record_id": record_id},
        headers=auth(institution_token),
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["token"]
    assert body["token_id"]
    assert "not official APAAR" in body["notice"]

    stored = await mongo.db()["verification_tokens"].find_one(
        {"token_id": body["token_id"]}
    )
    assert stored["token_hash"] == hash_token(body["token"])
    assert body["token"] not in stored.values()


async def test_the_token_is_not_written_to_the_audit_trail(client, institution_token):
    created = await create_student(client, institution_token)
    record_id = created.json()["record_id"]
    issued = await client.post(
        "/api/verification-tokens",
        json={"student_record_id": record_id},
        headers=auth(institution_token),
    )
    token = issued.json()["token"]

    entries = await mongo.db()["audit_events"].find({}).to_list(length=None)
    for entry in entries:
        assert token not in str(entry.get("details", ""))
        assert token not in str(entry.get("subject", ""))


# ------------------------------------------------------------- verification


async def test_the_public_verification_returns_only_allowlisted_fields(
    client, institution_token
):
    created = await create_student(client, institution_token)
    record_id = created.json()["record_id"]
    issued = await client.post(
        "/api/verification-tokens",
        json={"student_record_id": record_id},
        headers=auth(institution_token),
    )
    token = issued.json()["token"]

    response = await client.get(f"/api/verify/token/{token}")
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert body["verdict"] == "VALID"
    assert body["institution"] == "INST-T1"
    assert body["programme"] == "BTECH_CSE"
    assert body["academic_year"] == "2024-25"
    assert "not official APAAR" in body["notice"]

    # The allowlist: no APAAR ID, no date of birth, no contact details, and
    # none of the underlying document.
    serialised = response.text
    assert "984210357890" not in serialised
    assert "2004-03-12" not in serialised
    assert "Rahul Kumar" not in serialised
    assert "apaar" not in body
    assert "date_of_birth" not in body
    assert "student" not in body
    assert set(body) <= {
        "valid",
        "verdict",
        "reason",
        "record_status",
        "institution",
        "programme",
        "academic_year",
        "issued_at",
        "expires_at",
        "needs_refresh",
        "notice",
    }


async def test_an_unknown_token_is_not_found(client):
    response = await client.get("/api/verify/token/not-a-real-token")
    assert response.status_code == 200
    assert response.json()["verdict"] == "NOT_FOUND"
    assert response.json()["valid"] is False


async def test_a_revoked_token_no_longer_verifies(client, institution_token):
    created = await create_student(client, institution_token)
    record_id = created.json()["record_id"]
    issued = await client.post(
        "/api/verification-tokens",
        json={"student_record_id": record_id},
        headers=auth(institution_token),
    )
    token_id = issued.json()["token_id"]
    token = issued.json()["token"]

    revoked = await client.post(
        f"/api/verification-tokens/{token_id}/revoke", headers=auth(institution_token)
    )
    assert revoked.status_code == 200
    assert revoked.json()["revoked"] is True

    response = await client.get(f"/api/verify/token/{token}")
    assert response.json()["verdict"] == "REVOKED"
    assert response.json()["valid"] is False


async def test_an_expired_token_no_longer_verifies(client, institution_token):
    from datetime import datetime, timedelta, timezone

    created = await create_student(client, institution_token)
    record_id = created.json()["record_id"]
    issued = await client.post(
        "/api/verification-tokens",
        json={"student_record_id": record_id},
        headers=auth(institution_token),
    )
    token = issued.json()["token"]

    await mongo.db()["verification_tokens"].update_one(
        {"token_id": issued.json()["token_id"]},
        {
            "$set": {
                "expires_at": datetime.now(timezone.utc) - timedelta(minutes=1)
            }
        },
    )
    response = await client.get(f"/api/verify/token/{token}")
    assert response.json()["verdict"] == "EXPIRED"
    assert response.json()["valid"] is False


async def test_a_correction_marks_the_tokens_as_needing_a_refresh(
    client, institution_token
):
    created = await create_student(client, institution_token)
    record_id = created.json()["record_id"]
    issued = await client.post(
        "/api/verification-tokens",
        json={"student_record_id": record_id},
        headers=auth(institution_token),
    )
    token = issued.json()["token"]

    applied = await client.post(
        f"/api/students/{record_id}/corrections",
        json={
            "changes": {"student_name": "Rahul K. Sharma"},
            "reason": "the admission document spells the name differently",
            "expected_version": 1,
        },
        headers=auth(institution_token),
    )
    assert applied.status_code == 200
    assert applied.json()["tokens_needing_reissue"] >= 1

    response = await client.get(f"/api/verify/token/{token}")
    body = response.json()
    assert body["verdict"] == "NEEDS_REFRESH"
    assert body["needs_refresh"] is True
    assert body["valid"] is False


async def test_the_badge_carries_a_token_rather_than_the_apaar_id(
    client, institution_token
):
    created = await create_student(client, institution_token)
    assert created.status_code == 201
    response = await client.get(
        "/api/students/984210357890/qr", headers=auth(institution_token)
    )
    assert response.status_code == 200
    assert response.content[:8] == b"\x89PNG\r\n\x1a\n"

    tokens = await mongo.db()["verification_tokens"].find({}).to_list(length=None)
    assert tokens
    # A badge is issued a token, and the raw APAAR ID is never the payload.
    assert all(token["token_hash"] for token in tokens)


# --------------------------------------------------------------- the helpers


def test_the_token_hash_is_stable():
    assert hash_token("abc") == hash_token("abc")
    assert hash_token("abc") != hash_token("abd")


def test_the_token_comparison_is_exact():
    assert tokens_match("abc", hash_token("abc"))
    assert not tokens_match("abd", hash_token("abc"))
    assert not tokens_match("", hash_token("abc"))


def test_the_apaar_id_is_redacted_for_the_audit_trail():
    assert redact_apaar("984210357890") == "9842 **** ****"
    assert redact_apaar("") == ""


# -------------------------------------------------- the in-memory safety rule


async def test_the_in_memory_database_is_refused_without_the_explicit_flag(monkeypatch):
    from app.core import config as config_module

    settings = config_module.Settings(
        mongodb_url="",
        allow_in_memory_db=False,
        environment="dev",
    )
    connection = Mongo()
    # The Mongo class reads the module-level settings, so patch them for the
    # duration of the check.
    monkeypatch.setattr("app.core.database.settings", settings)
    with pytest.raises(MongoConnectionError) as error:
        await connection.connect()
    assert "ALLOW_IN_MEMORY_DB" in str(error.value)


async def test_the_in_memory_database_is_refused_in_production(monkeypatch):
    from app.core import config as config_module

    settings = config_module.Settings(
        mongodb_url="",
        allow_in_memory_db=True,
        environment="production",
    )
    connection = Mongo()
    monkeypatch.setattr("app.core.database.settings", settings)
    with pytest.raises(MongoConnectionError) as error:
        await connection.connect()
    assert "never used in production" in str(error.value)


def test_the_production_start_up_refuses_the_in_memory_database():
    from app.core.config import Settings

    settings = Settings(
        mongodb_url="", allow_in_memory_db=True, environment="production"
    )
    with pytest.raises(RuntimeError) as error:
        settings.assert_production_safe()
    assert "never used in production" in str(error.value)


def test_the_production_start_up_refuses_a_short_secret():
    from app.core.config import Settings

    settings = Settings(
        mongodb_url="mongodb://localhost:27017",
        secret_key="short",
        environment="production",
    )
    with pytest.raises(RuntimeError):
        settings.assert_production_safe()
