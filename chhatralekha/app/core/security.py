"""Password hashing, JWT issuing/verification and API-key helpers.

The implementation deliberately avoids ``passlib`` because the
``passlib 1.7`` / ``bcrypt 4.x`` combination emits a noisy
``AttributeError: module 'bcrypt' has no attribute '__about__'`` warning on
import. ``bcrypt`` is used directly instead, which is a single, stable API.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
import jwt

from app.core.config import get_settings

settings = get_settings()

# --------------------------------------------------------------------- types

ROLE_AICTE = "aicte_admin"
ROLE_INSTITUTION = "institution_admin"
ROLE_VERIFIER = "verifier"
ROLE_STUDENT = "student"

ALL_ROLES = (ROLE_AICTE, ROLE_INSTITUTION, ROLE_VERIFIER, ROLE_STUDENT)


# ------------------------------------------------------------------ passwords

def hash_password(password: str) -> str:
    """Hash a password with bcrypt."""
    salt = bcrypt.gensalt(rounds=settings.bcrypt_rounds)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a bcrypt hash, never raising."""
    if not password or not hashed:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def password_policy_violations(password: str) -> list[str]:
    """Return the list of policy violations for a candidate password."""
    violations: list[str] = []
    if len(password) < 8:
        violations.append("The password must be at least 8 characters long.")
    if not any(char.isdigit() for char in password):
        violations.append("The password must contain at least one digit.")
    if not any(char.isalpha() for char in password):
        violations.append("The password must contain at least one letter.")
    if password.lower() in {"password", "admin", "chhatralekha", "aicte", "12345678"}:
        violations.append("The password is too common.")
    return violations


# --------------------------------------------------------------- pin hashing

PBKDF2_ITERATIONS = 120_000
PBKDF2_KEY_LENGTH = 32
PBKDF2_SALT_LENGTH = 16


def new_salt() -> str:
    """A fresh random salt, hex encoded."""
    return secrets.token_hex(PBKDF2_SALT_LENGTH)


def hash_pin(pin: str, salt: str) -> str:
    """PBKDF2-HMAC-SHA256 digest of a PIN."""
    derived = hashlib.pbkdf2_hmac(
        "sha256", pin.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS, dklen=PBKDF2_KEY_LENGTH
    )
    return derived.hex()


def verify_pin(pin: str, salt: str, expected_hash: str) -> bool:
    """Constant-time verification of a PIN against a stored digest."""
    if not pin or not salt or not expected_hash:
        return False
    return hmac.compare_digest(hash_pin(pin, salt), expected_hash.strip().lower())


# ---------------------------------------------------------------------- JWT

def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(
    subject: str,
    role: str,
    institution_id: Optional[str] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Issue a signed access token."""
    expires_at = _now() + timedelta(minutes=settings.access_token_expire_minutes)
    payload: Dict[str, Any] = {
        "sub": subject,
        "role": role,
        "institution_id": institution_id,
        "type": "access",
        "iat": int(_now().timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(subject: str) -> str:
    """Issue a signed refresh token."""
    expires_at = _now() + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": subject,
        "type": "refresh",
        "iat": int(_now().timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str, expected_type: str = "access") -> Dict[str, Any]:
    """Decode and validate a token, raising ``jwt.PyJWTError`` on failure."""
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError(f"Expected a '{expected_type}' token.")
    return payload


# ------------------------------------------------------------------ api keys

def generate_api_key(prefix: str = "chhatralekha") -> tuple[str, str]:
    """Return ``(plaintext_key, hashed_key)`` for a machine-to-machine client."""
    raw = f"{prefix}_{secrets.token_urlsafe(32)}"
    return raw, hash_api_key(raw)


def hash_api_key(raw: str) -> str:
    """Hash an API key with SHA-256 for at-rest storage."""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def verify_api_key(raw: str, hashed: str) -> bool:
    """Verify an API key against its stored hash."""
    if not raw or not hashed:
        return False
    return hmac.compare_digest(hash_api_key(raw), hashed.strip().lower())
