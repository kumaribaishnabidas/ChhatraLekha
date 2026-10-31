"""End-to-end tests of the Google sign-in endpoints."""

from __future__ import annotations

from app.core.config import get_settings


async def test_the_config_endpoint_reports_that_google_is_off(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "google_client_id", "")
    monkeypatch.setattr(get_settings(), "google_client_secret", "")
    response = await client.get("/api/auth/google/config")
    assert response.status_code == 200
    assert response.json()["enabled"] is False


async def test_the_start_endpoint_refuses_when_google_is_off(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "google_client_id", "")
    monkeypatch.setattr(get_settings(), "google_client_secret", "")
    response = await client.get("/api/auth/google", follow_redirects=False)
    assert response.status_code == 503
    assert "GOOGLE_CLIENT_ID" in response.json()["detail"]


async def test_the_start_endpoint_redirects_to_google(client, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "google_client_id", "client-id.apps.googleusercontent.com")
    monkeypatch.setattr(settings, "google_client_secret", "client-secret")

    response = await client.get("/api/auth/google", follow_redirects=False)
    assert response.status_code == 307
    location = response.headers["location"]
    assert location.startswith("https://accounts.google.com/o/oauth2/v2/auth")
    assert "client_id=client-id.apps.googleusercontent.com" in location
    assert "response_type=code" in location
    assert "state=" in location

    # The CSRF state is remembered in a short-lived, HttpOnly cookie.
    cookies = response.headers.get_list("set-cookie")
    assert any("chhatralekha_google_state=" in cookie for cookie in cookies)
    assert any("HttpOnly" in cookie for cookie in cookies)
    assert any("Max-Age=600" in cookie for cookie in cookies)


async def test_a_callback_without_a_state_is_refused(client, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "google_client_id", "client-id")
    monkeypatch.setattr(settings, "google_client_secret", "secret")

    response = await client.get(
        "/api/auth/google/callback", params={"code": "the-code"}, follow_redirects=False
    )
    assert response.status_code == 307
    assert response.headers["location"].startswith(
        f"{settings.frontend_origin.rstrip('/')}/login#"
    )
    assert "error=" in response.headers["location"]
    assert any(
        "chhatralekha_google_state=" in cookie
        and ("Max-Age=0" in cookie or "expires=" in cookie.lower())
        for cookie in response.headers.get_list("set-cookie")
    )


async def test_a_callback_with_a_wrong_state_is_refused(client, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "google_client_id", "client-id")
    monkeypatch.setattr(settings, "google_client_secret", "secret")

    # Start the flow to get the real state cookie.
    start = await client.get("/api/auth/google", follow_redirects=False)
    state = start.cookies.get("chhatralekha_google_state")
    assert state

    response = await client.get(
        "/api/auth/google/callback",
        params={"code": "the-code", "state": "a-different-state"},
        follow_redirects=False,
    )
    assert response.status_code == 307
    assert "error=" in response.headers["location"]


async def test_a_callback_with_a_google_error_is_refused(client, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "google_client_id", "client-id")
    monkeypatch.setattr(settings, "google_client_secret", "secret")

    response = await client.get(
        "/api/auth/google/callback",
        params={"error": "access_denied"},
        follow_redirects=False,
    )
    assert response.status_code == 307
    assert "error=" in response.headers["location"]
    assert "access_denied" in response.headers["location"]
    assert any(
        "chhatralekha_google_state=" in cookie
        and ("Max-Age=0" in cookie or "expires=" in cookie.lower())
        for cookie in response.headers.get_list("set-cookie")
    )


def test_client_ip_ignores_forwarded_headers_by_default(monkeypatch):
    from app.api.deps import client_ip
    from app.core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "trust_forwarded_headers", False)

    request = type("Request", (), {"headers": {"X-Forwarded-For": "203.0.113.42"}, "client": type("Client", (), {"host": "10.0.0.5"})()})()
    assert client_ip(request) == "10.0.0.5"


def test_client_ip_uses_forwarded_header_when_explicitly_trusted(monkeypatch):
    from app.api.deps import client_ip
    from app.core.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "trust_forwarded_headers", True)

    request = type("Request", (), {"headers": {"X-Forwarded-For": "203.0.113.42, 10.0.0.5"}, "client": type("Client", (), {"host": "10.0.0.5"})()})()
    assert client_ip(request) == "203.0.113.42"
