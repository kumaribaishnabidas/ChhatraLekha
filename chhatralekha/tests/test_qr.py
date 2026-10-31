"""Tests for the APAAR QR payload and rendering.

The badge carries an opaque verification token on this deployment's own
origin. It never carries the raw APAAR ID, and it never points at an official
government service.
"""

from __future__ import annotations

import pytest

from app.core.config import get_settings
from app.services import qr


@pytest.fixture(autouse=True)
def _frontend_origin(monkeypatch):
    """Point the badge at a known origin."""
    monkeypatch.setattr(get_settings(), "frontend_origin", "https://chhatralekha.vercel.app")
    yield


# ------------------------------------------------------------- the payload


def test_the_payload_is_a_token_link_on_our_own_origin():
    payload = qr.build_token_payload("opaque-token-value")
    assert payload == "https://chhatralekha.vercel.app/verify/t/opaque-token-value"


def test_the_payload_never_carries_the_apaar_id():
    payload = qr.build_token_payload("opaque-token-value")
    assert "984210357890" not in payload
    assert "apaar" not in payload.lower()


def test_the_payload_never_points_at_an_official_domain():
    payload = qr.build_token_payload("opaque-token-value")
    assert "aicte-india.gov.in" not in payload
    assert "aicte.gov.in" not in payload
    assert "gov.in" not in payload


def test_the_payload_follows_the_configured_origin():
    settings = get_settings()
    original = settings.frontend_origin
    try:
        settings.frontend_origin = "https://another-app.vercel.app/"
        payload = qr.build_token_payload("token")
        assert payload == "https://another-app.vercel.app/verify/t/token"
    finally:
        settings.frontend_origin = original


def test_a_token_is_required():
    with pytest.raises(ValueError):
        qr.build_token_payload("")


def test_a_trailing_slash_on_the_origin_is_normalised():
    settings = get_settings()
    original = settings.frontend_origin
    try:
        settings.frontend_origin = "https://chhatralekha.vercel.app///"
        payload = qr.build_token_payload("token")
        assert payload == "https://chhatralekha.vercel.app/verify/t/token"
    finally:
        settings.frontend_origin = original


# ------------------------------------------------------------------ parsing


def test_a_token_link_is_parsed():
    payload = qr.build_token_payload("opaque-token-value")
    parsed = qr.parse_payload(payload)
    assert parsed is not None
    assert parsed.token == "opaque-token-value"
    assert parsed.is_token_payload is True
    assert parsed.apaar_id == ""


def test_a_token_in_the_query_string_is_parsed():
    parsed = qr.parse_payload("https://chhatralekha.vercel.app/verify?token=abc123")
    assert parsed is not None
    assert parsed.token == "abc123"


def test_a_bare_identifier_is_parsed():
    parsed = qr.parse_payload("984210357890")
    assert parsed is not None
    assert parsed.apaar_id == "984210357890"
    assert parsed.token is None


def test_the_legacy_link_format_is_still_readable():
    # A badge printed before the token flow existed carries the APAAR ID. It
    # can still be parsed, but the server never builds one.
    parsed = qr.parse_payload(
        "https://chhatralekha.vercel.app/verify?apaar=984210357890&inst=INST-0421"
    )
    assert parsed is not None
    assert parsed.apaar_id == "984210357890"
    assert parsed.institution_id == "INST-0421"


def test_a_link_without_a_token_or_an_apaar_id_is_rejected():
    assert qr.parse_payload("https://example.com/verify?foo=bar") is None
    assert qr.parse_payload("") is None
    assert qr.parse_payload(None) is None


def test_the_payload_round_trips():
    payload = qr.build_token_payload("opaque-token-value")
    assert qr.parse_payload(payload).token == "opaque-token-value"


# ---------------------------------------------------------------- rendering


def test_rendering_produces_a_png():
    png = qr.render_png("hello")
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(png) > 100


def test_rendering_produces_an_svg():
    svg = qr.render_svg("hello")
    assert "<svg" in svg


def test_the_module_matrix_has_a_square_shape():
    matrix = qr.render_matrix("hello")
    assert len(matrix) == len(matrix[0])
    assert len(matrix) > 20
