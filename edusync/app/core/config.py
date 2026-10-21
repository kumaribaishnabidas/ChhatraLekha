"""Application configuration.

Every secret is read from the environment (or a ``.env`` file) — nothing
sensitive is ever committed to the repository. The defaults are development
values and are rejected when ``ENVIRONMENT`` is ``prod``.
"""

from __future__ import annotations

import secrets
from functools import lru_cache
from typing import Annotated, List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the EduSynC platform."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ------------------------------------------------------------- identity
    app_name: str = "EduSynC"
    environment: str = "dev"
    debug: bool = False
    api_prefix: str = "/api"

    # ------------------------------------------------------------- database
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "edusync"
    mongodb_timeout_ms: int = 5000
    #: Key used to derive the privacy-preserving match token of an APAAR ID.
    #: An empty value falls back to the seal key.
    match_key: str = ""

    @property
    def is_in_memory_mongo(self) -> bool:
        """True when the in-memory MongoDB is used (no server configured)."""
        return not self.mongodb_url.strip()

    @property
    def match_secret(self) -> bytes:
        """The secret used for the keyed match token."""
        return (self.match_key or self.seal_hmac_key).encode("utf-8")

    # ---------------------------------------------------------------- auth
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(48))
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # ----------------------------------------------------------- signatures
    seal_hmac_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    seal_ecdsa_private_key_pem: str = ""
    seal_ecdsa_public_key_pem: str = ""
    seal_key_id: str = "edusync-2024-01"

    # ------------------------------------------------------------- security
    #: ``NoDecode`` stops pydantic-settings from trying to JSON-parse the
    #: environment variable, so a plain comma-separated list works.
    cors_origins: Annotated[List[str], NoDecode] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5173",
    ]
    rate_limit_per_minute: int = 60
    upload_max_size_mb: int = 10
    bcrypt_rounds: int = 12

    # -------------------------------------------------------------- session
    session_cookie_name: str = "edusync_session"
    session_max_age: int = 60 * 60 * 8

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"prod", "production"}

    def assert_production_safe(self) -> None:
        """Refuse to start in production with development secrets."""
        if not self.is_production:
            return
        if len(self.secret_key) < 32:
            raise RuntimeError("SECRET_KEY must be at least 32 characters in production.")
        if len(self.seal_hmac_key) < 16:
            raise RuntimeError("SEAL_HMAC_KEY must be at least 16 characters in production.")
        if self.is_in_memory_mongo:
            raise RuntimeError(
                "MONGODB_URL must point at a real MongoDB server in production."
            )


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor (use as a FastAPI dependency)."""
    return Settings()
