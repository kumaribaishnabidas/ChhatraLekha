"""Google Sign-In (OpenID Connect).

The flow is the standard OAuth 2.0 **authorization code** flow:

1. the browser is sent to ``/api/auth/google``, which redirects to Google's
   consent screen with a ``state`` that is remembered in a short-lived,
   HttpOnly cookie;
2. Google redirects back to ``/api/auth/google/callback``, which exchanges
   the code for an ID token, reads the profile, and issues the same JWT pair
   the password sign-in issues;
3. the browser is returned to the portal, which stores the tokens and
   continues as that user.

An account is **linked**, not duplicated: if the e-mail already belongs to a
local account, the Google identity is attached to it; if the Google identity
is already known, that account is used. Only a completely new person gets a
new account, and it is given the restricted default role.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import urlencode

import httpx

from app.core.config import get_settings

GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"

#: The name of the short-lived cookie that carries the CSRF ``state``.
STATE_COOKIE = "chhatralekha_google_state"

#: How long the state cookie lives, in seconds.
STATE_TTL_SECONDS = 600


class GoogleAuthError(RuntimeError):
    """Raised when Google cannot be reached or answers with an error."""


@dataclass
class GoogleProfile:
    """The identity Google returned."""

    subject: str
    email: str
    name: str
    picture: Optional[str] = None
    email_verified: bool = True


def new_state() -> str:
    """A random CSRF token for the authorisation request."""
    return secrets.token_urlsafe(24)


def authorisation_url(
    *,
    redirect_uri: str,
    state: str,
    client_id: str | None = None,
    scopes: list[str] | None = None,
) -> str:
    """The URL that sends the browser to Google's consent screen."""
    settings = get_settings()
    params = {
        "client_id": (client_id or settings.google_client_id).strip(),
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes or settings.google_scopes),
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    }
    return f"{GOOGLE_AUTHORIZE_URL}?{urlencode(params)}"


async def exchange_code(
    code: str,
    *,
    redirect_uri: str,
    client_id: str | None = None,
    client_secret: str | None = None,
    client: Optional[httpx.AsyncClient] = None,
) -> dict[str, Any]:
    """Exchange an authorisation code for Google's tokens."""
    settings = get_settings()
    payload = {
        "code": code,
        "client_id": (client_id or settings.google_client_id).strip(),
        "client_secret": (client_secret or settings.google_client_secret).strip(),
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    if client is not None:
        response = await client.post(GOOGLE_TOKEN_URL, data=payload, headers=headers)
    else:
        async with httpx.AsyncClient(timeout=20) as owned:
            response = await owned.post(GOOGLE_TOKEN_URL, data=payload, headers=headers)

    if response.status_code != 200:
        raise GoogleAuthError(
            f"Google refused the authorisation code ({response.status_code})."
        )
    return response.json()


async def fetch_profile(
    access_token: str,
    *,
    client: Optional[httpx.AsyncClient] = None,
) -> GoogleProfile:
    """Read the profile of the signed-in Google account."""
    headers = {"Authorization": f"Bearer {access_token}"}
    if client is not None:
        response = await client.get(GOOGLE_USERINFO_URL, headers=headers)
    else:
        async with httpx.AsyncClient(timeout=20) as owned:
            response = await owned.get(GOOGLE_USERINFO_URL, headers=headers)

    if response.status_code != 200:
        raise GoogleAuthError(
            f"Google did not return the profile ({response.status_code})."
        )
    data = response.json()
    subject = str(data.get("sub", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    if not subject or not email:
        raise GoogleAuthError("Google did not return an identifier and an e-mail address.")
    return GoogleProfile(
        subject=subject,
        email=email,
        name=str(data.get("name") or email.split("@")[0]).strip(),
        picture=data.get("picture"),
        email_verified=bool(data.get("email_verified", True)),
    )


#: The value stored in ``password_hash`` for an account that has never used a
#: password. It is not a valid bcrypt hash, so no password can ever match it.
GOOGLE_ONLY_PASSWORD_HASH = "!google-sign-in-only"


async def resolve_account(db, profile: GoogleProfile) -> tuple[dict[str, Any], bool]:
    """Find the account behind a Google identity, creating or linking it.

    Returns the account document and whether it was just created.
    """
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)

    existing = await db["users"].find_one({"google_sub": profile.subject})
    if existing:
        return existing, False

    by_email = await db["users"].find_one({"email": profile.email})
    if by_email:
        # The person already has an account; attach the Google identity to it
        # rather than creating a second account for the same person.
        await db["users"].update_one(
            {"user_id": by_email["user_id"]},
            {
                "$set": {
                    "google_sub": profile.subject,
                    "google_picture": profile.picture,
                    "updated_at": now,
                }
            },
        )
        linked = dict(by_email)
        linked["google_sub"] = profile.subject
        linked["google_picture"] = profile.picture
        return linked, False

    settings = get_settings()
    document = {
        "user_id": f"USR-G-{profile.subject[:12].upper()}",
        "email": profile.email,
        "full_name": profile.name,
        "role": settings.google_default_role or "verifier",
        "institution_id": None,
        "password_hash": GOOGLE_ONLY_PASSWORD_HASH,
        "google_sub": profile.subject,
        "google_picture": profile.picture,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    await db["users"].insert_one(document)
    return document, True
