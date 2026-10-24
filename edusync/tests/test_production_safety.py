"""Production-safety behaviour of the configuration and the start-up.

These are the checks that decide whether a deployment is allowed to come up:
the in-memory demo database is refused, placeholder secrets are refused, a
missing database is a clear error, and the allowed CORS origins are exactly
what the deployment says they are.

Every case is built with ``_env_file=None`` so that a developer's local
``.env`` cannot change the outcome.
"""

from __future__ import annotations

import pytest

from app.core.config import Settings

FRESH_SECRET = "a-fresh-random-secret-key-of-at-least-32-characters"
FRESH_SEAL = "a-fresh-random-seal-key-32-characters"


def _production(**overrides) -> Settings:
    values = {
        "mongodb_url": "mongodb://cluster.example.net:27017",
        "secret_key": FRESH_SECRET,
        "seal_hmac_key": FRESH_SEAL,
        "environment": "production",
        # The suite itself runs on the in-memory database, so the flag has to
        # be turned off explicitly here.
        "allow_in_memory_db": False,
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


# ------------------------------------------------------- the allowed origins


def test_an_empty_cors_list_leaves_only_the_frontend_origin():
    settings = _production(cors_origins="", frontend_origin="https://edusync.vercel.app")
    assert settings.cors_origins == ["https://edusync.vercel.app"]


def test_a_missing_cors_list_leaves_only_the_frontend_origin():
    settings = _production(frontend_origin="https://edusync.vercel.app")
    assert settings.cors_origins == ["https://edusync.vercel.app"]


def test_the_trailing_slash_is_normalised_away():
    settings = _production(
        cors_origins="https://extra.example/",
        frontend_origin="https://edusync.vercel.app/",
    )
    assert settings.cors_origins == ["https://extra.example", "https://edusync.vercel.app"]
    assert all(not origin.endswith("/") for origin in settings.cors_origins)


def test_a_wildcard_is_never_allowed():
    settings = _production(cors_origins="*", frontend_origin="https://edusync.vercel.app")
    assert "*" not in settings.cors_origins
    assert settings.cors_origins == ["https://edusync.vercel.app"]


def test_the_frontend_origin_is_always_included():
    settings = _production(
        cors_origins="https://extra.example", frontend_origin="https://edusync.vercel.app"
    )
    assert "https://edusync.vercel.app" in settings.cors_origins


# ------------------------------------------------- the production refusals


def test_production_refuses_the_in_memory_database():
    settings = _production(mongodb_url="", allow_in_memory_db=False)
    with pytest.raises(RuntimeError) as error:
        settings.assert_production_safe()
    assert "MONGODB_URL is not set" in str(error.value)


def test_production_refuses_the_in_memory_database_even_when_it_is_allowed():
    settings = _production(mongodb_url="", allow_in_memory_db=True)
    with pytest.raises(RuntimeError) as error:
        settings.assert_production_safe()
    assert "in-memory database is never used in production" in str(error.value)


def test_production_refuses_a_short_secret_key():
    settings = _production(secret_key="too-short")
    with pytest.raises(RuntimeError) as error:
        settings.assert_production_safe()
    assert "SECRET_KEY" in str(error.value)


def test_production_refuses_the_documented_placeholder_secret_key():
    settings = _production(
        secret_key="change-me-to-a-long-random-string-at-least-32-characters"
    )
    with pytest.raises(RuntimeError) as error:
        settings.assert_production_safe()
    assert "SECRET_KEY" in str(error.value)


def test_production_refuses_a_short_seal_key():
    settings = _production(seal_hmac_key="short")
    with pytest.raises(RuntimeError) as error:
        settings.assert_production_safe()
    assert "SEAL_HMAC_KEY" in str(error.value)


def test_production_refuses_the_documented_placeholder_seal_key():
    settings = _production(seal_hmac_key="change-me-to-a-random-hmac-key")
    with pytest.raises(RuntimeError) as error:
        settings.assert_production_safe()
    assert "SEAL_HMAC_KEY" in str(error.value)


def test_a_correctly_configured_production_passes():
    settings = _production()
    settings.assert_production_safe()


# --------------------------------------------------------- the ENV alias


def test_env_is_accepted_as_an_alias_of_environment(monkeypatch):
    # The alias only fills in when ENVIRONMENT is not set anywhere - which is
    # the case on Render, where the platform sets ENV.
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    settings = Settings(
        _env_file=None,
        mongodb_url="mongodb://cluster.example.net:27017",
        env="production",
        secret_key=FRESH_SECRET,
        seal_hmac_key=FRESH_SEAL,
    )
    assert settings.environment == "production"
    assert settings.is_production is True


def test_environment_wins_over_the_env_alias():
    settings = Settings(
        _env_file=None,
        mongodb_url="mongodb://cluster.example.net:27017",
        env="production",
        environment="dev",
        secret_key=FRESH_SECRET,
        seal_hmac_key=FRESH_SEAL,
    )
    assert settings.environment == "dev"
    assert settings.is_production is False


def test_the_development_mode_does_not_refuse_anything():
    settings = Settings(
        _env_file=None,
        mongodb_url="",
        allow_in_memory_db=True,
        environment="dev",
        secret_key="short",
    )
    settings.assert_production_safe()


# ------------------------------------------------------------ the redaction


def test_the_connection_string_is_redacted():
    from app.core.database import redact_url

    redacted = redact_url(
        "mongodb+srv://apaaruser:SuperSecret123@cluster0.abcd.mongodb.net/edusync"
    )
    assert "SuperSecret123" not in redacted
    assert "apaaruser" in redacted
    assert "cluster0.abcd.mongodb.net" in redacted


# ------------------------------------------------------------- the seeding


def test_production_seeding_is_blocked_by_default():
    settings = _production()
    assert settings.allow_production_seed is False


def test_production_seeding_can_be_switched_on_deliberately():
    settings = _production(allow_production_seed=True)
    assert settings.allow_production_seed is True


def test_production_refuses_debug_true():
    settings = _production(debug=True)
    with pytest.raises(RuntimeError) as error:
        settings.assert_production_safe()
    assert "DEBUG=true is refused in production" in str(error.value)

