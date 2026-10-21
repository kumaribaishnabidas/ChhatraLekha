"""APAAR QR badge payload and QR image rendering.

The payload is a plain HTTPS verification link so that any standards-compliant
QR scanner (or a future deep-link handler) can resolve the credential. The
server can therefore be pointed at by the Android app, the web portal and a
third-party verifier alike.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import parse_qs, urlparse

import qrcode
from qrcode.constants import ERROR_CORRECT_H, ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q

BASE_URL = "https://apaar.aicte-india.gov.in/verify"

_EC_LEVELS = {
    "L": ERROR_CORRECT_L,
    "M": ERROR_CORRECT_M,
    "Q": ERROR_CORRECT_Q,
    "H": ERROR_CORRECT_H,
}

_BARE_ID = re.compile(r"^\d{12}$")


@dataclass
class ParsedApaarPayload:
    """The parts recovered from a scanned QR payload."""

    apaar_id: str
    institution_id: Optional[str] = None
    program_id: Optional[str] = None
    seal: Optional[str] = None
    timestamp: Optional[int] = None
    token: Optional[str] = None

    @property
    def is_token_payload(self) -> bool:
        """Whether the payload carries an opaque verification token."""
        return bool(self.token)


def build_payload(
    apaar_id: str,
    institution_id: str,
    program_id: str,
    seal: str,
    timestamp: int,
    base_url: str = BASE_URL,
) -> str:
    """Build the deep-link payload carried by the APAAR QR badge.

    This is the original format, which puts the APAAR ID in the URL. It is
    kept for badges that were already printed; new badges carry an opaque
    token instead - see [build_token_payload].
    """
    return (
        f"{base_url}?apaar={apaar_id}"
        f"&inst={institution_id}"
        f"&prog={program_id}"
        f"&seal={seal}"
        f"&t={timestamp}"
    )


def build_token_payload(token: str, base_url: str = BASE_URL) -> str:
    """Build the deep-link payload of a badge that carries a token.

    The token is opaque, expiring and revocable, so the URL discloses
    nothing about the student.
    """
    return f"{base_url}?token={token}"


def parse_payload(raw: str | None) -> ParsedApaarPayload | None:
    """Extract the APAAR identifier or the token from a scanned payload.

    Accepts the canonical verification URL as well as a bare 12-digit
    identifier. A payload that carries ``token=`` is the current format; one
    that carries ``apaar=`` is the original format, which is only readable by
    an authenticated verifier.
    """
    value = (raw or "").strip()
    if not value:
        return None
    if _BARE_ID.match(value):
        return ParsedApaarPayload(apaar_id=value)
    try:
        query = parse_qs(urlparse(value).query)
    except ValueError:
        return None

    token = (query.get("token") or [None])[0]
    if token:
        return ParsedApaarPayload(apaar_id="", token=token)

    apaar = (query.get("apaar") or [None])[0]
    if not apaar:
        return None
    timestamp_raw = (query.get("t") or [None])[0]
    try:
        timestamp = int(timestamp_raw) if timestamp_raw else None
    except (TypeError, ValueError):
        timestamp = None
    return ParsedApaarPayload(
        apaar_id=apaar,
        institution_id=(query.get("inst") or [None])[0],
        program_id=(query.get("prog") or [None])[0],
        seal=(query.get("seal") or [None])[0],
        timestamp=timestamp,
    )


def render_png(
    payload: str,
    box_size: int = 8,
    border: int = 4,
    ec_level: str = "M",
) -> bytes:
    """Render the payload as a PNG image."""
    code = qrcode.QRCode(
        version=None,
        error_correction=_EC_LEVELS.get(ec_level.upper(), ERROR_CORRECT_M),
        box_size=box_size,
        border=border,
    )
    code.add_data(payload)
    code.make(fit=True)
    image = code.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def render_svg(payload: str, border: int = 4, ec_level: str = "M") -> str:
    """Render the payload as an inline SVG (used by the web portal)."""
    import qrcode.image.svg

    code = qrcode.QRCode(
        version=None,
        error_correction=_EC_LEVELS.get(ec_level.upper(), ERROR_CORRECT_M),
        box_size=10,
        border=border,
    )
    code.add_data(payload)
    code.make(fit=True)
    image = code.make_image(image_factory=qrcode.image.svg.SvgImage)
    buffer = io.BytesIO()
    image.save(buffer)
    return buffer.getvalue().decode("utf-8")


def render_matrix(payload: str) -> list[list[bool]]:
    """Return the module matrix of the symbol (dark = ``True``)."""
    code = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=1,
        border=0,
    )
    code.add_data(payload)
    code.make(fit=True)
    return code.get_matrix()
