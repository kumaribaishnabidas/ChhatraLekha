"""EduSynC - APAAR ID Student Data Management & Verification Platform.

The FastAPI application exposes:

* the REST API under ``/api`` (OpenAPI documented at ``/docs``);
* the React web frontend, which is built by Vite into ``frontend/dist`` and
  served as a single-page application from the same origin.
"""

from __future__ import annotations

import logging
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

    # A developer running without a MongoDB server gets the in-memory
    # database, which starts empty. Seeding it here means the portal is
    # demonstrable with a single command and no external service.
    if mongo.is_in_memory:
        empty = await mongo.db()["students"].count_documents({}) == 0
        if empty:
            from app.scripts.seed import seed

            logger.info("Seeding the in-memory MongoDB with the demo dataset...")
            summary = await seed()
            logger.info(
                "Seeded %s institutions, %s programmes, %s students and %s anomalies.",
                summary["institutions"],
                summary["programmes"],
                summary["students"],
                summary["anomalies"],
            )

    yield
    await mongo.disconnect()


app = FastAPI(
    title="EduSynC - APAAR ID Platform",
    description=(
        "Student data management, automated validation, anomaly detection, "
        "signed credential verification, consent management and regulatory "
        "reporting for AICTE-approved institutions."
    ),
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in ALL_ROUTERS:
    app.include_router(router, prefix=settings.api_prefix)


# ------------------------------------------------------------------ health


@app.get("/api/health", tags=["system"], summary="Liveness and readiness")
async def health() -> dict:
    """Report the health of the service and its database connection."""
    database = "down"
    try:
        if not mongo.is_connected:
            await mongo.connect()
        await mongo.db().command("ping")
        database = "up"
    except Exception as exc:  # noqa: BLE001
        logger.warning("Database health check failed: %s", exc)
    return {
        "status": "ok" if database == "up" else "degraded",
        "app": settings.app_name,
        "environment": settings.environment,
        "database": database,
        "database_engine": "mongodb",
        "version": app.version,
    }


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
