"""Tests for the APAAR QR payload and rendering."""

from __future__ import annotations

from app.services import qr


def test_the_payload_is_a_verification_link():
    payload = qr.build_payload("984210357890", "INST-0421", "BTECH_CSE", "SEAL", 1726000000000)
    assert payload.startswith("https://apaar.aicte-india.gov.in/verify?")
    assert "apaar=984210357890" in payload
    assert "inst=INST-0421" in payload
    assert "prog=BTECH_CSE" in payload
    assert "seal=SEAL" in payload
    assert "t=1726000000000" in payload


def test_a_bare_identifier_is_parsed():
    parsed = qr.parse_payload("984210357890")
    assert parsed is not None
    assert parsed.apaar_id == "984210357890"
    assert parsed.institution_id is None


def test_a_verification_link_is_parsed():
    payload = qr.build_payload("984210357890", "INST-0421", "BTECH_CSE", "SEAL", 1726000000000)
    parsed = qr.parse_payload(payload)
    assert parsed is not None
    assert parsed.apaar_id == "984210357890"
    assert parsed.institution_id == "INST-0421"
    assert parsed.program_id == "BTECH_CSE"
    assert parsed.seal == "SEAL"
    assert parsed.timestamp == 1726000000000


def test_a_link_without_an_apaar_id_is_rejected():
    assert qr.parse_payload("https://example.com/verify?foo=bar") is None
    assert qr.parse_payload("") is None
    assert qr.parse_payload(None) is None


def test_the_payload_round_trips():
    payload = qr.build_payload("984210357890", "INST-0421", "BTECH_CSE", "SEAL", 1726000000000)
    assert qr.parse_payload(payload).apaar_id == "984210357890"


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
