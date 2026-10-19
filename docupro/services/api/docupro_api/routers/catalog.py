"""Catalog, capabilities, health and privacy endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request

from ..config import get_settings
from ..engines import ocr
from ..engines.office_render import libreoffice_available
from ..engines.registry import public_catalog

router = APIRouter()


@router.get("/tools", summary="List every conversion the server can run")
async def tools() -> dict:
    return public_catalog()


@router.get("/capabilities", summary="Engine and format capabilities of this server")
async def capabilities(request: Request) -> dict:
    settings = get_settings()
    manager = request.app.state.manager
    return {
        "version": settings.version,
        "engines": {
            "pdf": "MuPDF",
            "wordLayout": "pdf2docx",
            "docxRender": "libreoffice" if libreoffice_available() else "html-fallback",
            "libreoffice": libreoffice_available(),
            "ocr": ocr.ocr_backend(),
            "ocrLanguages": ocr.available_languages(),
            "images": "Pillow + pillow-heif",
            "spreadsheets": "openpyxl",
        },
        "limits": {
            "maxUploadBytes": settings.max_upload_bytes,
            "maxJobBytes": settings.max_job_bytes,
            "maxFilesPerJob": settings.max_files_per_job,
            "maxPages": settings.max_pages,
            "maxPixels": settings.max_pixels,
            "retentionMinutes": settings.retention_minutes,
            "conversionTimeoutSeconds": settings.conversion_timeout,
            "maxConcurrentJobs": settings.max_concurrent_jobs,
        },
        "queue": manager.stats(),
        "privacy": {
            "retentionMinutes": settings.retention_minutes,
            "deleteAfterDownloadSeconds": 120,
            "storage": "Encrypted-in-transit uploads, private per-job directories on the conversion host.",
            "training": "Documents are never used for model training.",
        },
    }


@router.get("/health", summary="Liveness probe")
async def health() -> dict:
    return {"status": "ok", "version": get_settings().version}


@router.get("/ready", summary="Readiness probe")
async def ready(request: Request) -> dict:
    settings = get_settings()
    checks = {
        "storage": settings.jobs_dir.exists() and settings.jobs_dir.is_dir(),
        "queue": request.app.state.manager.stats()["jobs"]["queued"] < settings.max_queue,
    }
    return {"status": "ready" if all(checks.values()) else "degraded", "checks": checks}
