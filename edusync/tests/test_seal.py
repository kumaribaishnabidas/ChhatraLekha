"""Tests for the tamper-evident credential seals."""

from __future__ import annotations

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.services import seal


def payload(**overrides) -> seal.CredentialPayload:
    values = {
        "apaar_id": "984210357890",
        "institution_id": "INST-0421",
        "program_id": "BTECH_CSE",
        "academic_year": "2024-25",
        "enrollment_date": "2024-08-01",
        "student_name": "Aakash Verma",
        "date_of_birth": "2004-03-12",
        "gender": "M",
        "admission_quota": "REGULAR_MERIT",
        "nationality": "Indian",
        "student_institute_roll_no": "CSE-0001",
        "issued_at": 1726000000000,
    }
    values.update(overrides)
    return seal.CredentialPayload(**values)


def test_the_canonical_string_contains_every_committed_field():
    canonical = payload().canonical()
    assert canonical.startswith("APAAR|984210357890|INST-0421|BTECH_CSE|2024-25|2024-08-01|")
    assert "Aakash Verma" in canonical
    assert "CSE-0001" in canonical


def test_the_legacy_canonical_keeps_the_original_five_fields():
    assert payload().legacy_canonical() == "APAAR|984210357890|INST-0421|BTECH_CSE|2024-25|2024-08-01"


def test_an_hmac_seal_verifies():
    signed = seal.sign_hmac(payload(), b"a-very-secret-key")
    result = seal.verify_hmac(signed, payload(), b"a-very-secret-key")
    assert result.is_valid
    assert result.algorithm == seal.SealAlgorithm.HMAC


def test_an_hmac_seal_fails_for_a_different_record():
    signed = seal.sign_hmac(payload(), b"a-very-secret-key")
    result = seal.verify_hmac(signed, payload(student_name="Someone Else"), b"a-very-secret-key")
    assert not result.is_valid
    assert result.verdict == seal.SealVerdict.INVALID


def test_an_hmac_seal_fails_with_the_wrong_secret():
    signed = seal.sign_hmac(payload(), b"secret-one")
    result = seal.verify_hmac(signed, payload(), b"secret-two")
    assert not result.is_valid


def test_the_wire_format_is_algorithm_keyid_signature():
    signed = seal.sign_hmac(payload(), b"secret", key_id="k1")
    algorithm, key_id, signature = signed.split(".")
    assert algorithm == "HMAC-SHA256"
    assert key_id == "k1"
    assert signature


def test_a_legacy_seal_is_reported_as_unverified():
    legacy = seal.legacy_seal(payload())
    result = seal.verify(legacy, payload())
    assert result.verdict == seal.SealVerdict.LEGACY_UNVERIFIED
    assert not result.is_valid


def test_a_tampered_legacy_seal_is_invalid():
    result = seal.verify("A" * 32, payload())
    assert result.verdict == seal.SealVerdict.INVALID


def test_an_ed25519_seal_verifies_with_the_published_key():
    private_key = Ed25519PrivateKey.generate()
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    signed = seal.sign_ed25519(payload(), private_key, key_id="ed1")
    result = seal.verify_ed25519(signed, payload(), public_pem)
    assert result.is_valid
    assert result.algorithm == seal.SealAlgorithm.ED25519


def test_an_ed25519_seal_fails_for_a_tampered_record():
    private_key = Ed25519PrivateKey.generate()
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    signed = seal.sign_ed25519(payload(), private_key)
    result = seal.verify_ed25519(signed, payload(program_id="BTECH_ECE"), public_pem)
    assert not result.is_valid


def test_an_empty_seal_is_malformed():
    result = seal.verify("", payload())
    assert result.verdict == seal.SealVerdict.MALFORMED


def test_a_garbled_seal_is_malformed():
    result = seal.verify("not-a-seal", payload())
    assert result.verdict == seal.SealVerdict.MALFORMED


def test_an_unknown_algorithm_is_reported():
    result = seal.verify("XYZ.key.signature", payload())
    assert result.verdict == seal.SealVerdict.UNKNOWN_ALGORITHM


def test_parsing_a_wire_format_seal():
    parsed = seal.parse("HMAC-SHA256.k1.abc")
    assert parsed is not None
    assert parsed.algorithm == "HMAC-SHA256"
    assert parsed.key_id == "k1"
    assert parsed.signature == "abc"


def test_parsing_a_malformed_seal_returns_none():
    assert seal.parse("only-one-part") is None
    assert seal.parse("") is None


def test_base64url_round_trips():
    raw = b"\x00\x01\xfe\xff hello world"
    encoded = seal.b64url_encode(raw)
    assert "=" not in encoded
    assert seal.b64url_decode(encoded) == raw


def test_the_default_signing_uses_the_configured_key():
    signed = seal.sign(payload())
    assert seal.verify(signed, payload()).is_valid
