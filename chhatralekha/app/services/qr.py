"""APAAR QR badge payload and QR image rendering.

The payload is a plain HTTPS link so that any standards-compliant QR scanner
can resolve the credential.

Two rules govern what goes into that link:

* It points at **this deployment's own verification page**, derived from
  ``FRONTEND_ORIGIN``. It never points at an official government service:
  ChhatraLekha is a prototype, a badge that resolved to somebody else's registry
  would claim an authenticity the platform does not have, and would send a
  stranger's browser to a domain the operator does not control.
* It carries an **opaque, expiring, revocable token** - never the raw APAAR
  ID. The token discloses nothing, and only its hash is stored, so a dump of
  the collection cannot be replayed.

The public verification route is therefore ``{origin}/verify/t/{token}``, and
the token resolves to an allowlist of fields through
``GET /api/verify/token/{token}``.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import parse_qs, urlparse

import qrcode
from qrcode.constants import ERROR_CORRECT_H, ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q

#: The path of the verification page on this deployment.
VERIFY_PATH = "/verify"

#: The path segment that carries the opaque token.
TOKEN_PATH = "t"

_EC_LEVELS = {
    "L": ERROR_CORRECT_L,
    "M": ERROR_CORRECT_M,
    "Q": ERROR_CORRECT_Q,
    "H": ERROR_CORRECT_H,
}

_BARE_ID = re.compile(r"^\d{12}$")


def verification_base_url() -> str:
    """The public URL a scanned badge resolves to.

    It is derived from ``FRONTEND_ORIGIN``, so a badge always points at the
    deployment that issued it.
    """
    from app.core.config import get_settings

    return f"{get_settings().frontend_origin.rstrip('/')}{VERIFY_PATH}"


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


def build_token_payload(token: str, base_url: Optional[str] = None) -> str:
    """Build the deep-link payload of a badge that carries a token.

    The result is ``{origin}/verify/t/{token}``. The token is opaque, so the
    link discloses nothing about the student.
    """
    if not token:
        raise ValueError("A verification token is required to build a badge.")
    base = (base_url or verification_base_url()).rstrip("/")
    return f"{base}/{TOKEN_PATH}/{token}"


def parse_payload(raw: str | None) -> ParsedApaarPayload | None:
    """Extract the token or the APAAR identifier from a scanned QR payload.

    The current format carries a token. The original format, which put the
    APAAR ID in the URL, is still readable so that a badge printed before the
    token flow existed can be parsed - but the server never *builds* one.
    """
    value = (raw or "").strip()
    if not value:
        return None
    if _BARE_ID.match(value):
        return ParsedApaarPayload(apaar_id=value)
    try:
        query = parse_qs(urlparse(value).query)
    except ValueError:
        query = {}

    token = (query.get("token") or [None])[0]
    if token:
        return ParsedApaarPayload(apaar_id="", token=token)

    # A token can also sit in the path: {origin}/verify/t/{token}.
    path = urlparse(value).path.rstrip("/")
    if f"/{TOKEN_PATH}/" in path:
        candidate = path.rsplit(f"/{TOKEN_PATH}/", 1)[-1]
        if candidate and "/" not in candidate:
            return ParsedApaarPayload(apaar_id="", token=candidate)

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
