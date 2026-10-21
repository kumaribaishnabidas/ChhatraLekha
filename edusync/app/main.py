"""EduSynC - APAAR ID Student Data Management & Verification Platform.

The FastAPI application exposes:

* the REST API under ``/api`` (OpenAPI documented at ``/docs``);
* the HTML portal under ``/`` (AICTE, institution, verifier and student
  views, installable as a PWA);
* the public verification deep-link target of the APAAR QR badge.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text

from app.api import ALL_ROUTERS
from app.core.config import get_settings
from app.core.database import Base, engine

settings = get_settings()

logger = logging.getLogger("edusync")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

BASE_DIR = __import__("pathlib").Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "web" / "templates"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Prepare the database on start-up."""
    settings.assert_production_safe()
    from app import models  # noqa: F401  (registers every table)

    if settings.is_sqlite:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        logger.info("SQLite schema ready at %s", settings.database_url)
    else:
        logger.info("Using the migrated database at %s", settings.database_url)
    yield
    await engine.dispose()


app = FastAPI(
    title="EduSynC - APAAR ID Platform",
    description=(
        "Student data management, automated validation, anomaly detection, "
        "signed credential verification, consent management and regulatory "
        "reporting for AICTE-approved institutions."
    ),
    version="1.0.0",
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

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "web" / "static")),
    name="static",
)

for router in ALL_ROUTERS:
    app.include_router(router, prefix=settings.api_prefix)


# ------------------------------------------------------------------ health


@app.get("/api/health", tags=["system"], summary="Liveness and readiness")
async def health() -> dict:
    """Report the health of the service and its database connection."""
    database = "down"
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        database = "up"
    except Exception as exc:  # noqa: BLE001
        logger.warning("Database health check failed: %s", exc)
    return {
        "status": "ok" if database == "up" else "degraded",
        "app": settings.app_name,
        "environment": settings.environment,
        "database": database,
        "version": app.version,
    }


# ------------------------------------------------------------------ portal


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def portal_home(request: Request):
    """The portal landing page."""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "app_name": settings.app_name,
            "environment": settings.environment,
        },
    )


@app.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def portal_login(request: Request):
    """The portal sign-in page."""
    return templates.TemplateResponse(
        "login.html", {"request": request, "app_name": settings.app_name}
    )


@app.get("/verify", response_class=HTMLResponse, include_in_schema=False)
async def portal_verify(request: Request):
    """The public credential-verification page reached by a scanned badge."""
    return templates.TemplateResponse(
        "verify.html",
        {
            "request": request,
            "app_name": settings.app_name,
            "apaar_id": request.query_params.get("apaar", ""),
        },
    )


@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def portal_dashboard(request: Request):
    """The AICTE Directorate dashboard."""
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "app_name": settings.app_name}
    )


@app.get("/manifest.webmanifest", include_in_schema=False)
async def manifest():
    """The PWA manifest that makes the portal installable."""
    return JSONResponse(
        {
            "name": "EduSynC - APAAR ID Platform",
            "short_name": "EduSynC",
            "description": (
                "APAAR ID student data management, verification and reporting for "
                "AICTE-approved institutions."
            ),
            "start_url": "/",
            "scope": "/",
            "display": "standalone",
            "background_color": "#14246B",
            "theme_color": "#14246B",
            "icons": [
                {
                    "src": "/static/images/icon-192.png",
                    "sizes": "192x192",
                    "type": "image/png",
                },
                {
                    "src": "/static/images/icon-512.png",
                    "sizes": "512x512",
                    "type": "image/png",
                },
            ],
        }
    )


@app.get("/service-worker.js", include_in_schema=False)
async def service_worker():
    """A minimal offline shell for the PWA."""
    script = """
const CACHE = 'edusync-v1';
const ASSETS = ['/', '/static/css/app.css', '/manifest.webmanifest'];
self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(ASSETS)));
  self.skipWaiting();
});
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key)))
    )
  );
  self.clients.claim();
});
self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        const copy = response.clone();
        caches.open(CACHE).then((cache) => cache.put(event.request, copy));
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});
"""
    return HTMLResponse(content=script, media_type="application/javascript")


@app.exception_handler(404)
async def not_found(request: Request, exc):
    """Render the portal's 404 page for browser navigation."""
    if request.url.path.startswith("/api"):
        return JSONResponse({"detail": "Not found"}, status_code=status.HTTP_404_NOT_FOUND)
    return templates.TemplateResponse(
        "404.html", {"request": request}, status_code=status.HTTP_404_NOT_FOUND
    )
