"""Conversion job endpoints: create, poll, cancel, download, delete."""

from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response

from ..config import get_settings
from ..engines.registry import availability, get_spec, validate_options
from ..errors import ApiError, NotFound, ValidationError
from ..security import client_identity, content_disposition
from ..uploads import save_upload, validate_inputs

log = logging.getLogger(__name__)
router = APIRouter()


def _limit(request: Request, key: str, cost: int = 1) -> None:
    limiter = request.app.state.limiter
    identity = client_identity(
        request.headers,
        request.client.host if request.client else None,
        get_settings().trust_proxy_headers,
    )
    for _ in range(cost):
        allowed, retry = limiter.check(identity)
        if not allowed:
            from ..errors import RateLimited

            raise RateLimited(
                "Too many requests. Please wait a moment and try again.",
                code="rate_limited",
                details={"retryAfterSeconds": retry},
            )


@router.post("/jobs", status_code=202, summary="Start a conversion")
async def create_job(
    request: Request,
    tool: str = Form(...),
    options: str = Form("{}"),
    order: str = Form(""),
    files: Annotated[list[UploadFile], File()] = [],
) -> Response:
    settings = get_settings()
    _limit(request, "jobs")

    spec = get_spec(tool)
    if spec is None:
        raise ValidationError("That tool does not exist.", code="unknown_tool")
    available, reason = availability(spec)
    if not available:
        raise ValidationError(reason or "This tool is not available on this server.", code="tool_unavailable")

    if len(options) > 20_000:
        raise ValidationError("The options payload is too large.", code="invalid_request")
    try:
        raw_options = json.loads(options or "{}")
    except json.JSONDecodeError as exc:
        raise ValidationError("Options must be valid JSON.", code="invalid_options") from exc
    resolved = validate_options(spec, raw_options)

    uploads = [f for f in files if f and (f.filename or "").strip()]
    if not uploads:
        raise ValidationError("Select at least one file to convert.", code="no_files")
    if len(uploads) > spec.max_files:
        raise ValidationError(
            f"“{spec.title}” accepts at most {spec.max_files} files per job.",
            code="too_many_files",
        )
    if len(uploads) > settings.max_files_per_job:
        raise ValidationError(
            f"At most {settings.max_files_per_job} files can be uploaded per job.",
            code="too_many_files",
        )

    manager = request.app.state.manager
    job = manager.reserve(tool, resolved)
    saved: list[tuple[Path, str]] = []
    running_total = [0]
    try:
        for index, upload in enumerate(uploads):
            original = (upload.filename or f"file-{index}").strip()
            extension = original.rsplit(".", 1)[-1].lower() if "." in original else "bin"
            extension = "".join(ch for ch in extension if ch.isalnum())[:8] or "bin"
            destination = job.input_dir / f"{index:03d}-{uuid.uuid4().hex[:8]}.{extension}"
            await save_upload(
                upload,
                destination,
                settings.max_upload_bytes,
                running_total,
                settings.max_job_bytes,
            )
            saved.append((destination, original))
        sources = validate_inputs(spec, saved, settings)
        if order.strip():
            _reorder(sources, order, spec.max_files)
        manager.enqueue(job, sources)
    except ApiError:
        manager.delete(job.id)
        raise
    except Exception:
        log.exception("Upload pipeline error")
        manager.delete(job.id)
        raise ValidationError("The upload could not be processed.", code="upload_failed") from None
    finally:
        for upload in uploads:
            try:
                await upload.close()
            except Exception:  # pragma: no cover
                pass

    return JSONResponse(status_code=202, content=job.public())


def _reorder(sources, order: str, max_files: int) -> None:
    try:
        indexes = [int(part) - 1 for part in order.replace(";", ",").split(",") if part.strip()]
    except ValueError as exc:
        raise ValidationError("The file order must look like 3,1,2.", code="invalid_order") from exc
    if sorted(indexes) != list(range(len(sources))):
        raise ValidationError(
            f"The order must list each of the {len(sources)} files exactly once.",
            code="invalid_order",
        )
    original = list(sources)
    for position, index in enumerate(indexes):
        sources[position] = original[index]


@router.get("/jobs/{job_id}", summary="Conversion status and artifacts")
async def get_job(request: Request, job_id: str) -> dict:
    _limit(request, "status", cost=1)
    job = request.app.state.manager.get(job_id)
    return job.public()


@router.post("/jobs/{job_id}/cancel", summary="Cancel a running conversion")
async def cancel_job(request: Request, job_id: str) -> dict:
    job = request.app.state.manager.cancel(job_id)
    return job.public()


@router.delete("/jobs/{job_id}", status_code=204, summary="Delete a job and its files immediately")
async def delete_job(request: Request, job_id: str) -> Response:
    request.app.state.manager.delete(job_id)
    return Response(status_code=204)


@router.get("/jobs/{job_id}/download/{artifact_id}", summary="Download a converted file")
async def download(request: Request, job_id: str, artifact_id: str, token: str = "") -> FileResponse:
    _limit(request, "download")
    if not token:
        raise NotFound("This download link is incomplete.", code="invalid_token")
    manager = request.app.state.manager
    job, path, artifact = manager.artifact_for_download(job_id, artifact_id, token)
    if not path.exists():
        raise NotFound("This file has already been removed.", code="artifacts_gone")
    manager.register_download(job, artifact_id)
    headers = {
        "Content-Disposition": content_disposition(artifact["name"]),
        "Cache-Control": "no-store, private",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
    }
    return FileResponse(
        path,
        media_type=artifact["mediaType"],
        headers=headers,
        filename=None,
    )


@router.get("/jobs", summary="Recent jobs created by this server (no user data)")
async def list_jobs(request: Request) -> dict:
    """Aggregate counters only; document names are never listed publicly."""
    return request.app.state.manager.stats()
