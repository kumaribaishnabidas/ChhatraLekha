"""Tamper-evident credential seals.

Three generations coexist, exactly as in the Kotlin client:

* ``LEGACY``   - an unkeyed SHA-256 digest. It is reported as
  ``LEGACY_UNVERIFIED`` and never as a valid signature, because anybody can
  recompute it.
* ``HMAC``     - HMAC-SHA256 with a server-held secret. Strong, but only the
  holder of the secret can verify it.
* ``ED25519``  - a digital signature. The public key can be published, so any
  third party can verify a credential offline.

The wire format is ``<ALG>.<keyId>.<signature>`` with a base64url payload.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from app.core.config import get_settings

settings = get_settings()


class SealAlgorithm(str, Enum):
    LEGACY = "SHA256"
    HMAC = "HMAC-SHA256"
    ED25519 = "ED25519"

    @property
    def label(self) -> str:
        return {
            SealAlgorithm.LEGACY: "Legacy SHA-256 digest (unkeyed)",
            SealAlgorithm.HMAC: "HMAC-SHA256 (server-held secret)",
            SealAlgorithm.ED25519: "Ed25519 digital signature (publicly verifiable)",
        }[self]


class SealVerdict(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    LEGACY_UNVERIFIED = "LEGACY_UNVERIFIED"
    UNKNOWN_ALGORITHM = "UNKNOWN_ALGORITHM"
    MALFORMED = "MALFORMED"
    KEY_UNAVAILABLE = "KEY_UNAVAILABLE"
    REVOKED = "REVOKED"


@dataclass
class CredentialPayload:
    """The fields a seal commits to."""

    apaar_id: str
    institution_id: str
    program_id: str
    academic_year: str
    enrollment_date: str
    student_name: str = ""
    date_of_birth: str = ""
    gender: str = ""
    admission_quota: str = ""
    nationality: str = ""
    student_institute_roll_no: str = ""
    issued_at: int = 0
    version: int = 2

    def canonical(self) -> str:
        """The current canonical string (all committed fields).

        ``issued_at`` is deliberately **not** part of the commitment: it is
        the moment the badge was printed, and a verifier who receives the
        badge does not know it. Committing to it would make every badge
        unverifiable.
        """
        return "|".join(
            [
                "APAAR",
                self.apaar_id.strip(),
                self.institution_id.strip(),
                self.program_id.strip(),
                self.academic_year.strip(),
                self.enrollment_date.strip(),
                self.student_name.strip(),
                self.date_of_birth.strip(),
                self.gender.strip(),
                self.admission_quota.strip(),
                self.nationality.strip(),
                self.student_institute_roll_no.strip(),
                str(self.version),
            ]
        )

    def legacy_canonical(self) -> str:
        """The original five-field canonical string.

        Seals produced before the payload was extended must still verify, so
        the legacy format is preserved verbatim.
        """
        return "|".join(
            [
                "APAAR",
                self.apaar_id.strip(),
                self.institution_id.strip(),
                self.program_id.strip(),
                self.academic_year.strip(),
                self.enrollment_date.strip(),
            ]
        )


@dataclass
class SealVerification:
    """The outcome of verifying a presented seal."""

    verdict: SealVerdict
    algorithm: Optional[SealAlgorithm] = None
    key_id: str = ""
    reason: str = ""

    @property
    def is_valid(self) -> bool:
        return self.verdict == SealVerdict.VALID

    @property
    def label(self) -> str:
        return {
            SealVerdict.VALID: "Valid",
            SealVerdict.INVALID: "Invalid",
            SealVerdict.LEGACY_UNVERIFIED: "Legacy - unverifiable",
            SealVerdict.UNKNOWN_ALGORITHM: "Unknown algorithm",
            SealVerdict.MALFORMED: "Malformed seal",
            SealVerdict.KEY_UNAVAILABLE: "Verification key unavailable",
            SealVerdict.REVOKED: "Revoked",
        }[self.verdict]


# --------------------------------------------------------------- base64url


def b64url_encode(raw: bytes) -> str:
    """Base64url without padding."""
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def b64url_decode(value: str) -> bytes:
    """Decode base64url, tolerating missing padding."""
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


# ------------------------------------------------------------------ sealing


def legacy_seal(payload: CredentialPayload) -> str:
    """The original unkeyed SHA-256 seal (32 hex characters)."""
    digest = hashlib.sha256(payload.legacy_canonical().encode("utf-8")).hexdigest()
    return digest[:32].upper()


def sign_hmac(payload: CredentialPayload, secret: bytes, key_id: str | None = None) -> str:
    """Sign a payload with HMAC-SHA256."""
    key_id = key_id or settings.seal_key_id
    digest = hmac.new(secret, payload.canonical().encode("utf-8"), hashlib.sha256).digest()
    return f"{SealAlgorithm.HMAC.value}.{key_id}.{b64url_encode(digest)}"


def sign_ed25519(payload: CredentialPayload, private_key: Ed25519PrivateKey, key_id: str | None = None) -> str:
    """Sign a payload with an Ed25519 private key."""
    key_id = key_id or settings.seal_key_id
    signature = private_key.sign(payload.canonical().encode("utf-8"))
    return f"{SealAlgorithm.ED25519.value}.{key_id}.{b64url_encode(signature)}"


def sign(payload: CredentialPayload) -> str:
    """Sign with the configured default algorithm (HMAC)."""
    return sign_hmac(payload, settings.seal_hmac_key.encode("utf-8"))


# ---------------------------------------------------------------- verifying


@dataclass
class ParsedSeal:
    """A parsed wire-format seal."""

    algorithm: str
    key_id: str
    signature: str


def parse(presented: str) -> ParsedSeal | None:
    """Parse the ``<ALG>.<keyId>.<signature>`` wire format."""
    if not presented:
        return None
    parts = presented.strip().split(".")
    if len(parts) != 3:
        return None
    algorithm, key_id, signature = parts
    if not algorithm or not key_id or not signature:
        return None
    return ParsedSeal(algorithm=algorithm, key_id=key_id, signature=signature)


def verify(presented: str, payload: CredentialPayload) -> SealVerification:
    """Verify a presented seal against the payload it claims to describe."""
    if not presented or not presented.strip():
        return SealVerification(
            verdict=SealVerdict.MALFORMED, reason="No seal was presented."
        )

    parsed = parse(presented)
    if parsed is None:
        # A bare 32-character hex string is a legacy seal.
        compact = presented.strip()
        if len(compact) == 32 and all(char in "0123456789ABCDEFabcdef" for char in compact):
            expected = legacy_seal(payload)
            if hmac.compare_digest(expected, compact.upper()):
                return SealVerification(
                    verdict=SealVerdict.LEGACY_UNVERIFIED,
                    algorithm=SealAlgorithm.LEGACY,
                    key_id="legacy",
                    reason=(
                        "The seal is an unkeyed SHA-256 digest. It is consistent with the "
                        "record but cannot prove authorship."
                    ),
                )
            return SealVerification(
                verdict=SealVerdict.INVALID,
                algorithm=SealAlgorithm.LEGACY,
                key_id="legacy",
                reason="The legacy seal does not match the record.",
            )
        return SealVerification(
            verdict=SealVerdict.MALFORMED,
            reason="The seal does not follow the <ALG>.<keyId>.<signature> format.",
        )

    if parsed.algorithm == SealAlgorithm.LEGACY.value:
        expected = legacy_seal(payload)
        if hmac.compare_digest(expected, parsed.signature.upper()):
            return SealVerification(
                verdict=SealVerdict.LEGACY_UNVERIFIED,
                algorithm=SealAlgorithm.LEGACY,
                key_id=parsed.key_id,
                reason="Unkeyed SHA-256 digest - consistent but not cryptographically proven.",
            )
        return SealVerification(
            verdict=SealVerdict.INVALID,
            algorithm=SealAlgorithm.LEGACY,
            key_id=parsed.key_id,
            reason="The legacy seal does not match the record.",
        )

    if parsed.algorithm == SealAlgorithm.HMAC.value:
        return verify_hmac(presented, payload)

    if parsed.algorithm == SealAlgorithm.ED25519.value:
        return verify_ed25519(presented, payload)

    return SealVerification(
        verdict=SealVerdict.UNKNOWN_ALGORITHM,
        algorithm=None,
        key_id=parsed.key_id,
        reason=f"Unknown seal algorithm '{parsed.algorithm}'.",
    )


def verify_hmac(
    presented: str, payload: CredentialPayload, secret: bytes | None = None
) -> SealVerification:
    """Verify an HMAC-SHA256 seal.

    When *secret* is omitted the configured server-held key is used, which is
    the normal path. Passing the key explicitly lets a caller verify a seal
    produced with a different key.
    """
    parsed = parse(presented)
    if parsed is None:
        return SealVerification(
            verdict=SealVerdict.MALFORMED, reason="The seal is malformed."
        )
    key = secret if secret is not None else settings.seal_hmac_key.encode("utf-8")
    expected = hmac.new(key, payload.canonical().encode("utf-8"), hashlib.sha256).digest()
    try:
        actual = b64url_decode(parsed.signature)
    except Exception:  # noqa: BLE001 - any decoding problem means "invalid"
        return SealVerification(
            verdict=SealVerdict.MALFORMED,
            algorithm=SealAlgorithm.HMAC,
            key_id=parsed.key_id,
            reason="The signature is not valid base64url.",
        )
    if hmac.compare_digest(expected, actual):
        return SealVerification(
            verdict=SealVerdict.VALID,
            algorithm=SealAlgorithm.HMAC,
            key_id=parsed.key_id,
            reason="The HMAC signature matches the record.",
        )
    return SealVerification(
        verdict=SealVerdict.INVALID,
        algorithm=SealAlgorithm.HMAC,
        key_id=parsed.key_id,
        reason="The HMAC signature does not match the record.",
    )


def verify_ed25519(
    presented: str, payload: CredentialPayload, public_key_pem: str | None = None
) -> SealVerification:
    """Verify an Ed25519 signature against a published public key."""
    parsed = parse(presented)
    if parsed is None:
        return SealVerification(
            verdict=SealVerdict.MALFORMED, reason="The seal is malformed."
        )
    pem = public_key_pem if public_key_pem is not None else settings.seal_ecdsa_public_key_pem
    if not pem:
        return SealVerification(
            verdict=SealVerdict.KEY_UNAVAILABLE,
            algorithm=SealAlgorithm.ED25519,
            key_id=parsed.key_id,
            reason="No Ed25519 public key is published for this key id.",
        )
    try:
        public_key = serialization.load_pem_public_key(pem.encode("utf-8"))
    except Exception:  # noqa: BLE001
        return SealVerification(
            verdict=SealVerdict.KEY_UNAVAILABLE,
            algorithm=SealAlgorithm.ED25519,
            key_id=parsed.key_id,
            reason="The configured public key could not be loaded.",
        )
    if not isinstance(public_key, Ed25519PublicKey):
        return SealVerification(
            verdict=SealVerdict.KEY_UNAVAILABLE,
            algorithm=SealAlgorithm.ED25519,
            key_id=parsed.key_id,
            reason="The configured key is not an Ed25519 public key.",
        )
    try:
        signature = b64url_decode(parsed.signature)
    except Exception:  # noqa: BLE001
        return SealVerification(
            verdict=SealVerdict.MALFORMED,
            algorithm=SealAlgorithm.ED25519,
            key_id=parsed.key_id,
            reason="The signature is not valid base64url.",
        )
    try:
        public_key.verify(signature, payload.canonical().encode("utf-8"))
    except InvalidSignature:
        return SealVerification(
            verdict=SealVerdict.INVALID,
            algorithm=SealAlgorithm.ED25519,
            key_id=parsed.key_id,
            reason="The Ed25519 signature does not match the record.",
        )
    return SealVerification(
        verdict=SealVerdict.VALID,
        algorithm=SealAlgorithm.ED25519,
        key_id=parsed.key_id,
        reason="The Ed25519 signature matches the record.",
    )


# --------------------------------------------------------------- utilities


def sha256_hex(value: str) -> str:
    """Full SHA-256 hex digest of a string."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def format_timestamp(millis: int) -> str:
    """Human readable RFC-3339 style timestamp used on certificates."""
    from datetime import datetime, timezone

    moment = datetime.fromtimestamp(millis / 1000, tz=timezone.utc)
    return moment.strftime("%d %b %Y, %H:%M:%S UTC")


def format_iso(millis: int) -> str:
    """ISO-8601 timestamp for audit logs and machine-readable payloads."""
    from datetime import datetime, timezone

    moment = datetime.fromtimestamp(millis / 1000, tz=timezone.utc)
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")
