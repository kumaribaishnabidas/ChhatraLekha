"""Application configuration.

Every secret is read from the environment (or a ``.env`` file) — nothing
sensitive is ever committed to the repository. The defaults are development
values and are rejected when ``ENVIRONMENT`` is ``prod``.
"""

from __future__ import annotations

import secrets
from functools import lru_cache
from typing import Annotated, List

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the ChhatraLekha platform."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ------------------------------------------------------------- identity
    app_name: str = "ChhatraLekha"
    environment: str = "dev"
    #: ``ENV`` is accepted as an alias of ``ENVIRONMENT`` because the hosting
    #: platforms set ``ENV`` by convention. ``ENVIRONMENT`` still wins when
    #: both are present.
    env: str = ""
    debug: bool = False
    api_prefix: str = "/api"
    #: The public origin of the web frontend, used for CORS and for the
    #: links printed on a QR badge.
    frontend_origin: str = "http://localhost:5173"

    # ------------------------------------------------------------- database
    mongodb_url: str = ""
    mongodb_database: str = "chhatralekha"
    mongodb_timeout_ms: int = 5000
    #: Key used to derive the privacy-preserving match token of an APAAR ID.
    #: An empty value falls back to the seal key.
    match_key: str = ""
    #: The in-memory MongoDB is a **demo and test facility only**. It has to be
    #: switched on explicitly; a missing or unreachable ``MONGODB_URL`` is an
    #: error, never a silent downgrade.
    allow_in_memory_db: bool = False

    @property
    def is_in_memory_mongo(self) -> bool:
        """True when the in-memory MongoDB is used."""
        return not self.mongodb_url.strip()

    @property
    def match_secret(self) -> bytes:
        """The secret used for the keyed match token."""
        return (self.match_key or self.seal_hmac_key).encode("utf-8")

    @property
    def google_enabled(self) -> bool:
        """Whether "Sign in with Google" is offered."""
        return bool(self.google_client_id.strip() and self.google_client_secret.strip())

    # ---------------------------------------------------------------- auth
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(48))
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # ----------------------------------------------------------- signatures
    seal_hmac_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    seal_ecdsa_private_key_pem: str = ""
    seal_ecdsa_public_key_pem: str = ""
    seal_key_id: str = "apaar-verify-2024-01"

    # ------------------------------------------------------------- security
    #: ``NoDecode`` stops pydantic-settings from trying to JSON-parse the
    #: environment variable, so a plain comma-separated list works.
    #:
    #: The list is empty by default, which means the allowed origins are
    #: exactly ``FRONTEND_ORIGIN`` - the only origin a deployment needs. The
    #: local development origins are added in development only.
    cors_origins: Annotated[List[str], NoDecode] = []
    rate_limit_per_minute: int = 60
    upload_max_size_mb: int = 10
    bcrypt_rounds: int = 12

    # ------------------------------------------------------- Google sign-in
    #: The OAuth 2.0 client of the Google Cloud project. When both the id and
    #: the secret are present, "Sign in with Google" is offered.
    google_client_id: str = ""
    google_client_secret: str = ""
    #: The redirect URI registered with Google. When it is empty it is
    #: derived from the incoming request, which is what a local development
    #: run needs.
    google_redirect_uri: str = ""
    #: The role given to somebody who signs in with Google for the first
    #: time and has no account yet.
    google_default_role: str = "pending"
    #: The scopes requested from Google.
    google_scopes: List[str] = ["openid", "email", "profile"]

    # -------------------------------------------------------------- session
    session_cookie_name: str = "chhatralekha_session"
    session_max_age: int = 60 * 60 * 8
    #: Whether the application should trust the reverse-proxy ``X-Forwarded-For``
    #: header. This must remain off unless the deployment runs behind a trusted
    #: proxy that strips spoofed values before they reach the app.
    trust_forwarded_headers: bool = False

    # ----------------------------------------------------------- demo data
    #: The password given to the seeded demo accounts. When it is empty the
    #: seed script generates one and prints it once.
    demo_password: str = ""
    #: Seeding a production database is refused unless this is switched on.
    allow_production_seed: bool = False
    #: The lifetime of a verification token, in minutes.
    verification_token_minutes: int = 60

    @model_validator(mode="before")
    @classmethod
    def _env_alias(cls, values):
        """Accept ``ENV`` as an alias of ``ENVIRONMENT``."""
        if isinstance(values, dict):
            alias = values.get("env")
            if alias and not values.get("environment"):
                values = {**values, "environment": alias}
        return values

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def _cors_is_derived_from_the_frontend_origin(self) -> "Settings":
        """Keep the CORS list in step with ``FRONTEND_ORIGIN``.

        A wildcard is never allowed: the API sends credentials, and a
        wildcard origin is not compatible with credentialed requests. The
        trailing slash is stripped from every origin, so that
        ``https://app.vercel.app/`` and ``https://app.vercel.app`` are the
        same origin.

        In production the list is exactly ``FRONTEND_ORIGIN``. In
        development the local origins are added so that the Vite dev server
        and the backend can talk to each other.
        """
        origins = [
            origin.strip().rstrip("/")
            for origin in self.cors_origins
            if origin.strip() and origin.strip() != "*"
        ]
        frontend = self.frontend_origin.strip().rstrip("/")
        if frontend and frontend not in origins:
            origins.append(frontend)
        if not origins and not self.is_production:
            origins = [
                "http://localhost:8000",
                "http://127.0.0.1:8000",
                "http://localhost:5173",
            ]
        object.__setattr__(self, "cors_origins", origins)
        return self

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"prod", "production"}

    def assert_production_safe(self) -> None:
        """Refuse to start in production with development settings.

        Outside production this is a no-op: the in-memory demo database is
        explicitly opt-in there, and the secret-length rules are a
        production concern.
        """
        if not self.is_production:
            return
        if self.allow_in_memory_db:
            raise RuntimeError(
                "ALLOW_IN_MEMORY_DB is set, but the in-memory database is never "
                "used in production. Remove it, or point MONGODB_URL at a real "
                "MongoDB server."
            )
        if self.is_in_memory_mongo:
            raise RuntimeError(
                "MONGODB_URL is not set, so the application would fall back to the "
                "in-memory demo database, which is never used in production. Set "
                "MONGODB_URL to a real MongoDB server (a mongodb+srv:// Atlas "
                "connection string, for example)."
            )
        if self.debug:
            raise RuntimeError(
                "DEBUG=true is refused in production. Set DEBUG=false."
            )
        if len(self.secret_key) < 32 or _is_placeholder(self.secret_key):
            raise RuntimeError(
                "SECRET_KEY must be a fresh random value of at least 32 characters "
                "in production. Generate one with: "
                'python -c "import secrets; print(secrets.token_urlsafe(48))"'
            )
        if len(self.seal_hmac_key) < 16 or _is_placeholder(self.seal_hmac_key):
            raise RuntimeError(
                "SEAL_HMAC_KEY must be a fresh random value of at least 16 characters "
                "in production. Generate one with: "
                'python -c "import secrets; print(secrets.token_urlsafe(32))"'
            )


def _is_placeholder(value: str) -> bool:
    """Whether a secret is one of the documented placeholders."""
    lowered = (value or "").strip().lower()
    if not lowered:
        return True
    markers = ("change-me", "change_me", "your-", "your_", "example", "placeholder", "local-development")
    return any(marker in lowered for marker in markers)


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor (use as a FastAPI dependency)."""
    return Settings()
