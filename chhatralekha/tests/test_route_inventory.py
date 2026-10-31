"""Route inventory and tenant isolation security tests (Stage 4).

1. Route inventory: Enumerate every endpoint in the FastAPI application.
   Verify that any non-public route enforces authentication and permission checks.
2. Tenant isolation: Verify that an institution admin cannot access or modify
   another institution's records.
3. Security headers: Verify that secure HTTP response headers are set.
"""

from __future__ import annotations

import pytest
from fastapi.routing import APIRoute

from app.api.deps import Principal, get_principal
from app.main import app

PUBLIC_ROUTE_PATHS = {
    "/health",
    "/api/health",
    "/api/auth/login",
    "/api/auth/refresh",
    "/api/auth/google",
    "/api/auth/google/callback",
    "/api/auth/google/config",
    "/api/auth/password-policy",
    "/api/auth/check-password",
    "/api/verify/token/{token}",
    "/api/verify/redirect/{apaar_id}",
    "/api/verify/public-key",
    "/api/verify/jwks",
    "/api/institutions/register",
    "/api/schools/template",
    "/api/transparency",
}


def test_route_inventory_all_routes_are_protected_or_explicitly_public():
    """Every API endpoint must be either explicitly public or guarded by auth/permission."""
    unprotected = []

    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        path = route.path
        if not path.startswith("/api"):
            continue

        if path in PUBLIC_ROUTE_PATHS:
            continue

        # Inspect route dependencies and endpoint signature dependencies
        has_security = False
        all_dependencies = list(route.dependencies)
        if hasattr(route, "dependant"):
            all_dependencies.extend(route.dependant.dependencies)

        for dep in all_dependencies:
            call = getattr(dep, "call", None)
            if call is None:
                continue
            # Check for require_permission, require_any_permission, or get_principal
            name = getattr(call, "__name__", "")
            qualname = getattr(call, "__qualname__", "")
            if (
                "require_permission" in qualname
                or "require_permission" in name
                or "require_any_permission" in qualname
                or "require_any_permission" in name
            ):
                has_security = True
                break
            if call is get_principal or "get_principal" in name:
                has_security = True
                break

        if not has_security:
            unprotected.append(f"{route.methods} {path}")

    assert not unprotected, (
        f"Found API routes without auth/permission dependency: {unprotected}"
    )


async def test_security_headers_present_on_response(client):
    """Responses must carry secure headers and request correlation ID."""
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "camera" in response.headers.get("Permissions-Policy", "")


async def test_tenant_isolation_institution_scoping():
    """An institution admin cannot access another institution's data."""
    admin_inst_1 = Principal(
        subject="admin1",
        role="institution_admin",
        institution_id="INST-001",
    )

    # Allowed for own institution
    admin_inst_1.require_scope("INST-001")

    # Forbidden for another institution
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        admin_inst_1.require_scope("INST-002")
    assert exc_info.value.status_code == 403
    assert "another institution" in exc_info.value.detail
