"""DOCUPRO conversion service (FastAPI application).

Serves the JSON API and, when a built web bundle is present, the single page
application from the same origin so the browser only ever talks to one host.
"""

from __future__ import annotations

import logging
import os
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .engines.registry import get_spec
from .errors import ApiError, PayloadTooLarge
from .jobs import JobManager
from .routers import catalog, jobs
from .security import RateLimiter

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("docupro")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.ensure_dirs()
    app.state.manager = JobManager(settings, get_spec)
    app.state.limiter = RateLimiter(settings.rate_limit_per_minute, settings.rate_limit_burst)
    log.info(
        "DOCUPRO %s ready (retention %s min, concurrency %s)",
        settings.version,
        settings.retention_minutes,
        settings.max_concurrent_jobs,
    )
    try:
        yield
    finally:
        app.state.manager.shutdown()


app = FastAPI(
    title="DOCUPRO API",
    version=settings.version,
    description="Private document conversion API. Files are processed in isolated workers and deleted automatically.",
    lifespan=lifespan,
    docs_url="/api/docs" if os.environ.get("DOCUPRO_ENABLE_DOCS") == "1" else None,
    redoc_url=None,
    openapi_url="/api/openapi.json" if os.environ.get("DOCUPRO_ENABLE_DOCS") == "1" else None,
)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type"],
        max_age=600,
    )


@app.middleware("http")
async def hardening(request: Request, call_next):
    started = time.perf_counter()
    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:16]

    if request.method in {"POST", "PUT", "PATCH"}:
        declared = request.headers.get("content-length")
        if declared is not None:
            try:
                if int(declared) > settings.max_job_bytes + 2 * 1024 * 1024:
                    raise PayloadTooLarge(
                        f"The upload exceeds the {settings.max_job_bytes // (1024 * 1024)} MB total limit.",
                        code="job_too_large",
                    )
            except ValueError:
                raise PayloadTooLarge("Invalid content length.", code="invalid_request") from None

    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    if request.url.path.startswith("/api/"):
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; frame-ancestors *; base-uri 'none'; form-action 'none'"
        )
        response.headers["Cache-Control"] = "no-store"
    else:
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self'; "
            "object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors *"
        )
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    slow = time.perf_counter() - started
    if slow > 5:
        log.warning("Slow request %s %s took %.2fs", request.method, request.url.path, slow)
    return response


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    headers = {}
    if exc.status_code == 429:
        retry = exc.details.get("retryAfterSeconds") if isinstance(exc.details, dict) else None
        headers["Retry-After"] = str(retry or 30)
    return JSONResponse(status_code=exc.status_code, content=exc.to_dict(), headers=headers)


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    fields = []
    for error in exc.errors()[:8]:
        location = ".".join(str(part) for part in error.get("loc", []) if part != "body")
        fields.append({"field": location or "request", "message": error.get("msg", "Invalid value")})
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "invalid_request",
                "message": "Some of the submitted values were not valid.",
                "details": {"fields": fields},
            }
        },
    )


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception) -> JSONResponse:
    log.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_error",
                "message": "Something went wrong on the server. Please try again.",
            }
        },
    )


app.include_router(catalog.router, prefix="/api", tags=["catalog"])
app.include_router(jobs.router, prefix="/api", tags=["jobs"])


# --- static single page application ----------------------------------------
_web_dir = settings.web_dir
if _web_dir and (_web_dir / "index.html").is_file():
    assets = _web_dir / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa(full_path: str) -> Response:
        if full_path.startswith("api/"):
            return JSONResponse(status_code=404, content={"error": {"code": "not_found", "message": "Not found."}})
        candidate = (_web_dir / full_path).resolve()
        if full_path and _web_dir.resolve() in candidate.parents and candidate.is_file():
            headers = (
                {"Cache-Control": "public, max-age=31536000, immutable"} if full_path.startswith("assets/") else {}
            )
            return FileResponse(candidate, headers=headers)
        return FileResponse(_web_dir / "index.html", headers={"Cache-Control": "no-cache"})
else:

    @app.get("/", include_in_schema=False)
    async def api_index() -> dict:
        return {
            "name": "DOCUPRO conversion API",
            "version": settings.version,
            "docs": "/api/tools",
            "note": "Build the web app (npm run build in apps/web) to serve the interface from this origin.",
        }
