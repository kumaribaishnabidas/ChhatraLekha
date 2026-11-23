"""Tests for FastAPI API documentation security (/docs, /redoc, /openapi.json).

Verifies that:
- In development/test mode, documentation endpoints (/docs, /redoc, /openapi.json) are available.
- In production mode, documentation endpoints are strictly disabled by default (returning 404).
- Documentation endpoints can be explicitly enabled in production (e.g. for private staging) via ENABLE_DOCS=true.
- Documentation endpoints can be explicitly disabled in dev mode via ENABLE_DOCS=false.
- Both ENABLE_DOCS and DOCS_ENABLED settings are supported.
- Standard API routes (such as /api/health) continue functioning normally regardless of documentation state.
- The SPA catch-all route does not fall through to serve frontend HTML for disabled doc endpoints.
- The 503 frontend_missing response does not advertise /docs when documentation is disabled.
"""

from __future__ import annotations

import httpx
import pytest

from app.core.config import Settings
from app.main import create_app


def _make_settings(**overrides) -> Settings:
    """Build a Settings instance with local .env ignored."""
    defaults = {
        "mongodb_url": "",
        "allow_in_memory_db": True,
        "secret_key": "test-secret-key-that-is-long-enough-for-tests",
        "seal_hmac_key": "test-seal-hmac-key",
        "rate_limit_per_minute": 0,
        "bcrypt_rounds": 4,
    }
    defaults.update(overrides)
    return Settings(_env_file=None, **defaults)


@pytest.mark.asyncio
async def test_docs_enabled_by_default_in_dev():
    """In development, /docs, /redoc, and /openapi.json should return 200."""
    dev_settings = _make_settings(environment="dev")
    assert dev_settings.is_production is False
    assert dev_settings.is_docs_enabled is True

    test_app = create_app(dev_settings)
    transport = httpx.ASGITransport(app=test_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        docs_resp = await client.get("/docs")
        assert docs_resp.status_code == 200
        assert "swagger" in docs_resp.text.lower() or "html" in docs_resp.headers.get("content-type", "")

        redoc_resp = await client.get("/redoc")
        assert redoc_resp.status_code == 200
        assert "redoc" in redoc_resp.text.lower() or "html" in redoc_resp.headers.get("content-type", "")

        openapi_resp = await client.get("/openapi.json")
        assert openapi_resp.status_code == 200
        data = openapi_resp.json()
        assert "paths" in data
        assert "/api/health" in data["paths"]


@pytest.mark.asyncio
async def test_docs_disabled_by_default_in_production():
    """In production, /docs, /redoc, and /openapi.json must be disabled and return 404."""
    prod_settings = _make_settings(
        environment="production",
        mongodb_url="mongodb://cluster.example.net:27017",
        secret_key="a-fresh-random-secret-key-of-at-least-32-characters",
        seal_hmac_key="a-fresh-random-seal-key-32-characters",
        allow_in_memory_db=False,
    )
    assert prod_settings.is_production is True
    assert prod_settings.is_docs_enabled is False

    test_app = create_app(prod_settings)
    transport = httpx.ASGITransport(app=test_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        docs_resp = await client.get("/docs")
        assert docs_resp.status_code == 404

        redoc_resp = await client.get("/redoc")
        assert redoc_resp.status_code == 404

        openapi_resp = await client.get("/openapi.json")
        assert openapi_resp.status_code == 404


@pytest.mark.asyncio
async def test_docs_explicitly_enabled_in_production():
    """Setting enable_docs=True allows docs in production/staging when needed."""
    prod_settings = _make_settings(
        environment="production",
        enable_docs=True,
        mongodb_url="mongodb://cluster.example.net:27017",
        secret_key="a-fresh-random-secret-key-of-at-least-32-characters",
        seal_hmac_key="a-fresh-random-seal-key-32-characters",
        allow_in_memory_db=False,
    )
    assert prod_settings.is_production is True
    assert prod_settings.is_docs_enabled is True

    test_app = create_app(prod_settings)
    transport = httpx.ASGITransport(app=test_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        docs_resp = await client.get("/docs")
        assert docs_resp.status_code == 200

        redoc_resp = await client.get("/redoc")
        assert redoc_resp.status_code == 200

        openapi_resp = await client.get("/openapi.json")
        assert openapi_resp.status_code == 200


@pytest.mark.asyncio
async def test_docs_explicitly_disabled_in_dev():
    """Setting enable_docs=False suppresses docs even in development."""
    dev_settings = _make_settings(environment="dev", enable_docs=False)
    assert dev_settings.is_production is False
    assert dev_settings.is_docs_enabled is False

    test_app = create_app(dev_settings)
    transport = httpx.ASGITransport(app=test_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        docs_resp = await client.get("/docs")
        assert docs_resp.status_code == 404

        redoc_resp = await client.get("/redoc")
        assert redoc_resp.status_code == 404

        openapi_resp = await client.get("/openapi.json")
        assert openapi_resp.status_code == 404


@pytest.mark.asyncio
async def test_docs_enabled_alias():
    """DOCS_ENABLED should act as an alias for ENABLE_DOCS."""
    # Test docs_enabled=True in production
    s1 = _make_settings(
        environment="production",
        docs_enabled=True,
        mongodb_url="mongodb://cluster.example.net:27017",
        secret_key="a-fresh-random-secret-key-of-at-least-32-characters",
        seal_hmac_key="a-fresh-random-seal-key-32-characters",
        allow_in_memory_db=False,
    )
    assert s1.is_docs_enabled is True

    # Test docs_enabled=False in dev
    s2 = _make_settings(environment="dev", docs_enabled=False)
    assert s2.is_docs_enabled is False


@pytest.mark.asyncio
async def test_api_routes_preserved_when_docs_disabled():
    """Standard API endpoints continue functioning normally when docs are disabled."""
    prod_settings = _make_settings(
        environment="production",
        enable_docs=False,
        mongodb_url="mongodb://cluster.example.net:27017",
        secret_key="a-fresh-random-secret-key-of-at-least-32-characters",
        seal_hmac_key="a-fresh-random-seal-key-32-characters",
        allow_in_memory_db=False,
    )
    test_app = create_app(prod_settings)
    transport = httpx.ASGITransport(app=test_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Docs endpoints return 404
        assert (await client.get("/docs")).status_code == 404
        assert (await client.get("/openapi.json")).status_code == 404

        # Health endpoint remains operational
        health_resp = await client.get("/api/health")
        assert health_resp.status_code == 200
        health_data = health_resp.json()
        assert health_data["app"] == "ChhatraLekha"
        assert health_data["environment"] == "production"

        # Demo academic context public endpoint remains operational
        demo_ctx_resp = await client.get("/api/auth/demo-academic-context")
        assert demo_ctx_resp.status_code == 200


@pytest.mark.asyncio
async def test_frontend_missing_does_not_leak_docs_in_production(monkeypatch):
    """When frontend is missing and docs are disabled, 503 response omits 'api': '/docs'."""
    from pathlib import Path
    import app.main

    # Simulate missing frontend dist
    non_existent = Path("/non/existent/path/for/test")
    monkeypatch.setattr(app.main, "FRONTEND_DIST", non_existent)

    # 1. When docs disabled:
    prod_settings = _make_settings(
        environment="production",
        enable_docs=False,
        mongodb_url="mongodb://cluster.example.net:27017",
        secret_key="a-fresh-random-secret-key-of-at-least-32-characters",
        seal_hmac_key="a-fresh-random-seal-key-32-characters",
        allow_in_memory_db=False,
    )
    app_no_docs = create_app(prod_settings)
    transport = httpx.ASGITransport(app=app_no_docs)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.get("/")
        assert resp.status_code == 503
        data = resp.json()
        assert "api" not in data

    # 2. When docs enabled:
    dev_settings = _make_settings(environment="dev", enable_docs=True)
    app_with_docs = create_app(dev_settings)
    transport2 = httpx.ASGITransport(app=app_with_docs)
    async with httpx.AsyncClient(transport=transport2, base_url="http://testserver") as client2:
        resp2 = await client2.get("/")
        assert resp2.status_code == 503
        data2 = resp2.json()
        assert data2.get("api") == "/docs"


@pytest.mark.asyncio
async def test_spa_catchall_rejects_docs_when_disabled(monkeypatch, tmp_path):
    """When frontend dist exists, disabled docs routes must return 404, not index.html."""
    import app.main

    # Create dummy index.html in tmp directory
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    index_file = dist_dir / "index.html"
    index_file.write_text("<!doctype html><html><body>SPA Root</body></html>")

    monkeypatch.setattr(app.main, "FRONTEND_DIST", dist_dir)

    prod_settings = _make_settings(
        environment="production",
        enable_docs=False,
        mongodb_url="mongodb://cluster.example.net:27017",
        secret_key="a-fresh-random-secret-key-of-at-least-32-characters",
        seal_hmac_key="a-fresh-random-seal-key-32-characters",
        allow_in_memory_db=False,
    )
    spa_app = create_app(prod_settings)
    transport = httpx.ASGITransport(app=spa_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # /docs must return 404, not 200 with index.html
        resp_docs = await client.get("/docs")
        assert resp_docs.status_code == 404
        assert resp_docs.headers.get("content-type", "").startswith("application/json")

        # /openapi.json must return 404
        resp_openapi = await client.get("/openapi.json")
        assert resp_openapi.status_code == 404

        # /redoc must return 404
        resp_redoc = await client.get("/redoc")
        assert resp_redoc.status_code == 404

        # Regular SPA route falls through to index.html
        resp_spa = await client.get("/dashboard")
        assert resp_spa.status_code == 200
        assert "SPA Root" in resp_spa.text

