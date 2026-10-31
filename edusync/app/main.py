"""EduSynC - APAAR ID Student Data Management & Verification Platform.

The FastAPI application exposes:

* the REST API under ``/api`` (OpenAPI documented at ``/docs``);
* the React web frontend, which is built by Vite into ``frontend/dist`` and
  served as a single-page application from the same origin.
"""

from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import ALL_ROUTERS
from app.core.config import get_settings
from app.core.database import mongo

settings = get_settings()

logger = logging.getLogger("edusync")
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)

#: Where the built React application lives.
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Open the MongoDB connection on start-up and close it on shutdown."""
    settings.assert_production_safe()
    await mongo.connect()
    logger.info(
        "EduSynC is ready (MongoDB database '%s')", settings.mongodb_database
    )
    logger.info(
        "Correction mode: %s",
        "multi-document transactions"
        if mongo.supports_transactions
        else "explicit operation_status recovery (the server is not a replica set)",
    )

    # The in-memory database is a demo facility. It starts empty, so it is
    # seeded here - but only when it was explicitly asked for, and never in
    # production. Seeding a real database is always a manual step.
    if mongo.is_in_memory and not settings.is_production:
        empty = await mongo.db()["students"].count_documents({}) == 0
        if empty:
            from app.scripts.seed import seed

            logger.info("Seeding the in-memory demo database...")
            summary = await seed()
            logger.info(
                "Seeded %s institutions, %s programmes, %s students and %s anomalies.",
                summary["institutions"],
                summary["programmes"],
                summary["students"],
                summary["anomalies"],
            )
            # The demo accounts are useless without their password, and the
            # operator has no other way to learn it. It is printed once, in the
            # server log, and never in an HTTP response.
            logger.warning(
                "DEMO ACCOUNTS (in-memory demo data only, never a real "
                "deployment):"
            )
            for email, role in summary.get("accounts", []):
                logger.warning("    %-34s %s", email, role)
            logger.warning(
                "    password: %s   (from DEMO_PASSWORD; change it in "
                "edusync/.env)",
                summary["demo_password"],
            )

    yield
    await mongo.disconnect()


if settings.is_production:
    _docs_url = None
    _redoc_url = None
    _openapi_url = None
else:
    _docs_url = "/docs"
    _redoc_url = "/redoc"
    _openapi_url = "/openapi.json"

app = FastAPI(
    title="EduSynC - APAAR ID Platform",
    description=(
        "Student data management, automated validation, anomaly detection, "
        "signed credential verification, consent management and regulatory "
        "reporting for AICTE-approved institutions."
    ),
    version="2.0.0",
    lifespan=lifespan,
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=_openapi_url,
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(self), microphone=(self)"
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "camera=(self), microphone=(self), geolocation=()")
    if settings.is_production:
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )
    return response


for router in ALL_ROUTERS:
    app.include_router(router, prefix=settings.api_prefix)


# ------------------------------------------------------------------ health


@app.get("/api/health", tags=["system"], summary="Liveness and readiness")
async def health() -> dict:
    """Report the health of the service and its database connection."""
    database = "down"
    error = ""
    try:
        if not mongo.is_connected:
            await mongo.connect()
        await mongo.db().command("ping")
        database = "up"
    except Exception as exc:  # noqa: BLE001
        logger.warning("Database health check failed: %s", exc)
        error = str(exc)

    in_memory = mongo.is_in_memory
    return {
        "status": "ok" if database == "up" else "degraded",
        "app": settings.app_name,
        "environment": settings.environment,
        "database": database,
        "database_engine": "mongodb",
        "in_memory_demo_data": in_memory,
        "notice": (
            "In-memory demo data - not persisted. This is a demo and test facility "
            "only."
            if in_memory
            else ""
        ),
        "error": error,
        "version": app.version,
    }


@app.get("/health", include_in_schema=False)
async def health_alias() -> dict:
    """The health check used by the Render deployment."""
    return await health()


# ------------------------------------------------------- the React frontend

if FRONTEND_DIST.is_dir():
    assets = FRONTEND_DIST / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa(full_path: str, request: Request):
        """Serve the built React application (single-page fallback)."""
        if full_path.startswith("api/"):
            return JSONResponse({"detail": "Not found"}, status_code=404)
        candidate = FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")

else:

    @app.get("/", include_in_schema=False)
    async def frontend_missing():
        """Explain how to build the React frontend when it is not present."""
        return JSONResponse(
            {
                "detail": (
                    "The React frontend has not been built. Run 'npm install && "
                    "npm run build' in the 'frontend' directory, or use the Vite "
                    "dev server with 'npm run dev'."
                ),
                "api": "/docs",
            },
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
