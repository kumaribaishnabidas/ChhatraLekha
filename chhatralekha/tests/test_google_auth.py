"""Tests for the Google sign-in."""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from app.core.config import get_settings
from app.services import google


@pytest.fixture(autouse=True)
def _google_configured(monkeypatch):
    """Configure a fake Google client for the tests."""
    settings = get_settings()
    monkeypatch.setattr(settings, "google_client_id", "client-id.apps.googleusercontent.com")
    monkeypatch.setattr(settings, "google_client_secret", "client-secret")
    monkeypatch.setattr(settings, "google_default_role", "verifier")
    yield


# ------------------------------------------------------------ the URL


def test_the_authorisation_url_points_at_google():
    url = google.authorisation_url(
        redirect_uri="https://chhatralekha.vercel.app/api/auth/google/callback",
        state="state-123",
    )
    assert url.startswith(google.GOOGLE_AUTHORIZE_URL)
    params = parse_qs(urlparse(url).query)
    assert params["client_id"] == ["client-id.apps.googleusercontent.com"]
    assert params["redirect_uri"] == [
        "https://chhatralekha.vercel.app/api/auth/google/callback"
    ]
    assert params["response_type"] == ["code"]
    assert params["state"] == ["state-123"]
    assert "email" in params["scope"][0]
    assert "openid" in params["scope"][0]


def test_the_authorisation_url_never_carries_a_secret():
    url = google.authorisation_url(
        redirect_uri="https://chhatralekha.vercel.app/api/auth/google/callback",
        state="state-123",
    )
    assert "client-secret" not in url
    assert "client_secret" not in url


def test_the_state_is_random():
    assert google.new_state() != google.new_state()
    assert len(google.new_state()) >= 16


# -------------------------------------------------------- the exchange


async def test_the_code_is_exchanged_for_tokens():
    seen = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = request.content.decode()
        return httpx.Response(200, json={"access_token": "ya29.token", "id_token": "id"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        tokens = await google.exchange_code(
            "the-code",
            redirect_uri="https://chhatralekha.vercel.app/api/auth/google/callback",
            client=client,
        )

    assert tokens["access_token"] == "ya29.token"
    assert "code=the-code" in seen["body"]
    assert "grant_type=authorization_code" in seen["body"]


async def test_a_refused_code_raises():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": "invalid_grant"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(google.GoogleAuthError):
            await google.exchange_code(
                "bad",
                redirect_uri="https://chhatralekha.vercel.app/api/auth/google/callback",
                client=client,
            )


async def test_the_profile_is_read():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer ya29.token"
        return httpx.Response(
            200,
            json={
                "sub": "1234567890",
                "email": "Person@Example.com",
                "name": "Person Example",
                "email_verified": True,
                "picture": "https://example.com/p.png",
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        profile = await google.fetch_profile("ya29.token", client=client)

    assert profile.subject == "1234567890"
    assert profile.email == "person@example.com"
    assert profile.name == "Person Example"


async def test_a_profile_without_an_identifier_is_refused():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"email": "person@example.com"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(google.GoogleAuthError):
            await google.fetch_profile("token", client=client)


# ------------------------------------------------------------ the account


async def test_a_new_person_gets_an_account_with_the_default_role():
    from app.core.database import mongo

    db = mongo.db()
    profile = google.GoogleProfile(
        subject="google-subject-1", email="newcomer@example.com", name="New Comer"
    )
    account, created = await google.resolve_account(db, profile)
    assert created is True
    assert account["role"] == "verifier"
    assert account["email"] == "newcomer@example.com"
    assert account["google_sub"] == "google-subject-1"
    # An account that has never used a password must not accept one.
    assert account["password_hash"] == google.GOOGLE_ONLY_PASSWORD_HASH


async def test_a_known_google_identity_signs_in_without_a_new_account():
    from app.core.database import mongo

    db = mongo.db()
    profile = google.GoogleProfile(
        subject="google-subject-2", email="known@example.com", name="Known Person"
    )
    first, created = await google.resolve_account(db, profile)
    assert created is True

    second, created_again = await google.resolve_account(db, profile)
    assert created_again is False
    assert second["user_id"] == first["user_id"]


async def test_an_existing_email_is_linked_rather_than_duplicated():
    from app.core.database import mongo

    db = mongo.db()
    await db["users"].insert_one(
        {
            "user_id": "USR-EXISTING",
            "email": "institution@example.com",
            "full_name": "Existing Person",
            "role": "institution_admin",
            "institution_id": "INST-0421",
            "password_hash": "x",
            "is_active": True,
        }
    )
    profile = google.GoogleProfile(
        subject="google-subject-3",
        email="institution@example.com",
        name="Existing Person",
    )
    account, created = await google.resolve_account(db, profile)
    assert created is False
    assert account["user_id"] == "USR-EXISTING"
    # The role and the institution of the existing account are kept.
    assert account["role"] == "institution_admin"
    assert account["institution_id"] == "INST-0421"
    stored = await db["users"].find_one({"user_id": "USR-EXISTING"})
    assert stored["google_sub"] == "google-subject-3"
